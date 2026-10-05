"""`make warmup`: wake everything the first round touches, so nothing on stage is cold.

  1. the audience app on Cloud Run (HTTP 200; run `make stage-on` first so it stays warm);
  2. the stage models in Ollama: David, last month's David and the embedding model;
  3. one David call (with his glossary) and one Goliath call: through the duel service when it is
     running (POST /warmup, nothing is recorded), otherwise directly with the same code.

Exit code 1 if anything failed.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time

import httpx

from _common import audience_service
from genlingo_duel.settings import get_settings

failed = 0


def line(label: str, result: str, ok: bool = True) -> None:
    global failed
    if not ok:
        failed = 1
    print(f"  {label:<38} {result if ok else 'FALLÓ (' + result + ')'}", flush=True)


def wake_audience_app(project: str, region: str) -> None:
    print("App del público (Cloud Run)", flush=True)
    try:
        url = audience_service(project, region)["url"]
    except Exception as exc:  # gcloud missing or not logged in
        line("URL del servicio", f"{type(exc).__name__}: {exc}", ok=False)
        return
    for path in ("/", "/api/config"):
        t0 = time.perf_counter()
        try:
            res = httpx.get(url + path, timeout=90, follow_redirects=True)
            line(path, f"{res.status_code} {time.perf_counter() - t0:.2f}s", ok=res.status_code == 200)
        except httpx.HTTPError as exc:
            line(path, type(exc).__name__, ok=False)


def preload_models(s, keep_alive: str) -> None:
    print("Modelos en Ollama", flush=True)
    with httpx.Client(base_url=s.ollama_url, timeout=180) as http:
        for tag in [t for t in (s.david_tag, s.david_previous_tag) if t]:
            t0 = time.perf_counter()
            try:
                res = http.post("/api/chat", json={"model": tag, "messages": [], "keep_alive": keep_alive})
                line(tag, f"cargado en {time.perf_counter() - t0:.1f}s" if res.status_code == 200 else res.text[:80],
                     ok=res.status_code == 200)
            except httpx.HTTPError as exc:
                line(tag, f"{type(exc).__name__}: ¿Ollama corriendo? (make up)", ok=False)
        if s.embedding_model:
            t0 = time.perf_counter()
            try:
                res = http.post("/api/embed", json={"model": s.embedding_model, "input": ["hola"], "keep_alive": keep_alive})
                line(s.embedding_model, f"cargado en {time.perf_counter() - t0:.1f}s" if res.status_code == 200 else res.text[:80],
                     ok=res.status_code == 200)
            except httpx.HTTPError as exc:
                line(s.embedding_model, type(exc).__name__, ok=False)


def report_duel(results: dict) -> None:
    for name in ("david", "goliath"):
        r = results[name]
        ok = r["status"] == "ok"
        detail = f"{r['latency_ms'] / 1000:.2f}s «{r['text'][:50]}»" if ok else f"{r['status']}: {r.get('error') or ''}"[:120]
        line(f"{name.capitalize()} ({r['model']})", detail, ok=ok)


async def direct_duel(s) -> dict:
    from genlingo_duel.arena import Arena
    from genlingo_duel.main import WARMUP_PHRASE

    results = await Arena.from_settings(s).duel(WARMUP_PHRASE, "genz_to_parent", "GT")
    return {n: {"status": r.status, "model": r.model, "latency_ms": r.latency_ms, "text": r.text, "error": r.error}
            for n, r in results.items()}


def main() -> int:
    s = get_settings()
    region = os.environ.get("REGION", "us-central1")
    wake_audience_app(s.project, region)
    if s.mock_ai:
        print("Modelos en Ollama\n  (MOCK_AI=1: modelos simulados, nada que cargar)")
    else:
        preload_models(s, os.environ.get("OLLAMA_KEEP_ALIVE", "2h"))
    duel_url = f"http://127.0.0.1:{os.environ.get('DUEL_PORT', '8787')}"
    try:
        httpx.get(duel_url + "/health", timeout=3).raise_for_status()
        print("Una ronda de calentamiento por el servicio del duelo (no se registra)", flush=True)
        res = httpx.post(duel_url + "/warmup", timeout=120)
        res.raise_for_status()
        report_duel(res.json())
    except httpx.HTTPStatusError as exc:
        line("POST /warmup", f"{exc.response.status_code} {exc.response.text[:80]}", ok=False)
    except httpx.HTTPError:
        print("Una ronda de calentamiento directa (el duelo no está corriendo: make up)", flush=True)
        report_duel(asyncio.run(direct_duel(s)))
    print("warmup ok" if not failed else "warmup: algo falló (mira las líneas FALLÓ)")
    return failed


if __name__ == "__main__":
    sys.exit(main())
