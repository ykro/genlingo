"""Talk-day gate: everything the live demo needs, checked in one go.

  make preflight        (after `make up` in another terminal and `make stage-on && make warmup`)

One Spanish line per check, `[ok]` or `[FALLA]` with the fix. Exit code = number of failures.
  Laptop: Ollama with David, last month's David and the embedding model; the duel service; the
          presenter view; the term bank, lexicon and test set; David's run file; free disk.
  Cloud:  the audience app answers, is kept warm (min-instances >= 1) and runs this event;
          Gemini answers (one tiny call); Firestore answers for this event.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
import time

import httpx

from _common import DATA, ROOT, audience_service
from genlingo_duel.runs import load_run
from genlingo_duel.settings import get_settings

MIN_FREE_GB = 10
PRESENTER_URL = "http://127.0.0.1:3000"


class Report:
    def __init__(self) -> None:
        self.failures = 0

    def ok(self, text: str) -> None:
        print(f"  [ok]    {text}", flush=True)

    def fail(self, text: str, fix: str) -> None:
        self.failures += 1
        print(f"  [FALLA] {text}\n          → {fix}", flush=True)


def check_ollama(r: Report, s) -> None:
    print("Ollama", flush=True)
    if s.mock_ai:
        r.fail("MOCK_AI=1: en escena los modelos serían simulados", "pon MOCK_AI=0 en .env y vuelve a correr make up")
        return
    try:
        models = httpx.get(s.ollama_url + "/api/tags", timeout=5).json().get("models", [])
    except httpx.HTTPError as exc:
        r.fail(f"Ollama no responde en {s.ollama_url} ({type(exc).__name__})", "make up (arranca Ollama)")
        return
    names = {(m.get("name") or "").removesuffix(":latest") for m in models}
    r.ok(f"Ollama responde ({len(names)} modelos)")
    wanted = [(s.david_tag, "David"), (s.david_previous_tag, "David del mes pasado"), (s.embedding_model, "embeddings")]
    for tag, role in wanted:
        if not tag:
            r.fail(f"{role}: sin tag en .env", "define LOCAL_MODEL_TAG, DAVID_PREVIOUS_TAG y EMBEDDING_MODEL en .env")
        elif tag.removesuffix(":latest") in names:
            r.ok(f"{role}: {tag}")
        else:
            fix = f"ollama pull {tag}" if role == "embeddings" else f"make pull-model TAG={tag}"
            r.fail(f"{role}: {tag} no está en Ollama", fix)


def check_local_services(r: Report, s) -> None:
    print("Duelo y vista del presentador", flush=True)
    port = os.environ.get("DUEL_PORT", "8787")
    try:
        h = httpx.get(f"http://127.0.0.1:{port}/health", timeout=5).json()
        problems = []
        if not h.get("ollama"):
            problems.append("no ve Ollama")
        if not h.get("online"):
            problems.append("sin internet (Goliath fuera)")
        if h.get("david_tag") != s.david_tag:
            problems.append(f"usa {h.get('david_tag')} y .env dice {s.david_tag}")
        feed = "encendido" if h.get("audience_feed") else "apagado"
        if problems:
            r.fail(f"El duelo responde pero {', '.join(problems)}", "revisa la conexión y reinicia make up")
        else:
            r.ok(f"Duelo responde en :{port} (David {h.get('david_tag')}, en línea, feed del público {feed})")
    except (httpx.HTTPError, ValueError) as exc:
        r.fail(f"El duelo no responde en :{port} ({type(exc).__name__})", "make up en otra terminal")
    try:
        res = httpx.get(PRESENTER_URL + "/api/config", timeout=5)
        if res.status_code == 200:
            r.ok(f"Vista del presentador responde ({PRESENTER_URL}/presenter)")
        else:
            r.fail(f"La vista del presentador responde {res.status_code}", "reinicia make up")
    except httpx.HTTPError as exc:
        r.fail(f"La vista del presentador no responde en :3000 ({type(exc).__name__})", "make up en otra terminal")


def check_data(r: Report, s) -> None:
    print("Datos", flush=True)
    files = [
        (DATA / "terms.jsonl", "banco de términos", "git checkout data/terms.jsonl"),
        (DATA / "counterparts.jsonl", "léxico (contrapartes validadas)", "make counterparts"),
        (DATA / "pairs" / "test_web.jsonl", "set de prueba (rondas E y G)", "make test-set"),
    ]
    for path, label, fix in files:
        if path.exists() and path.stat().st_size > 0:
            lines = sum(1 for _ in path.open(encoding="utf-8"))
            r.ok(f"{label}: {path.relative_to(ROOT)} ({lines:,} líneas)")
        else:
            r.fail(f"Falta {label}: {path.relative_to(ROOT)}", fix)
    run = load_run(s.runs_dir, s.david_tag) if s.david_tag else None
    if run:
        r.ok(f"Ficha de entrenamiento de David (prompt {run.get('prompt_style') or s.david_prompt_style})")
    else:
        r.fail(f"No hay train/runs/ para {s.david_tag}: David recibiría el prompt por defecto",
               "git pull (las fichas están en train/runs/) o revisa LOCAL_MODEL_TAG")
    free_gb = shutil.disk_usage(ROOT).free / 1e9
    if free_gb >= MIN_FREE_GB:
        r.ok(f"Disco libre: {free_gb:.0f} GB")
    else:
        r.fail(f"Disco libre: {free_gb:.1f} GB (mínimo {MIN_FREE_GB} GB)", "borra GGUF viejos (ollama rm <tag>) o data/.cache")


def check_audience_app(r: Report, s, region: str) -> None:
    print("App del público (Cloud Run)", flush=True)
    try:
        svc = audience_service(s.project, region)
    except Exception as exc:
        r.fail(f"No se pudo leer el servicio genlingo ({exc})", "gcloud auth login y revisa el proyecto")
        return
    try:
        t0 = time.perf_counter()
        res = httpx.get(svc["url"], timeout=30, follow_redirects=True)
        if res.status_code == 200:
            r.ok(f"Responde 200 en {time.perf_counter() - t0:.2f}s ({svc['url']})")
        else:
            r.fail(f"Responde {res.status_code}", "revisa el servicio genlingo en Cloud Run (make deploy)")
    except httpx.HTTPError as exc:
        r.fail(f"No responde ({type(exc).__name__})", "revisa la conexión y el servicio en Cloud Run")
    if svc["min_instances"] >= 1:
        r.ok(f"min-instances = {svc['min_instances']} (sin arranque en frío)")
    else:
        r.fail(f"min-instances = {svc['min_instances']}: el primer QR esperaría un arranque en frío", "make stage-on")
    event = svc["env"].get("EVENT_ID", "")
    if event == s.event_id:
        r.ok(f"Evento «{event}» igual que en la laptop")
    else:
        r.fail(f"La app usa el evento «{event}» y la laptop «{s.event_id}»: el feed no vería las frases",
               "iguala EVENT_ID en .env y en Cloud Run (EVENT_ID=… make deploy)")


async def gemini_call(s):
    from duel_core import GeminiClient

    client = GeminiClient(s.project, s.location, thinking_level=s.gemini_thinking_level or None)
    return await client.complete([{"role": "user", "content": "Responde solo: ok"}], model=s.gemini_model)


def check_gemini(r: Report, s) -> None:
    print("Goliath (Gemini en Vertex AI)", flush=True)
    if not s.gemini_model:
        r.fail("GEMINI_MODEL vacío", "define GEMINI_MODEL en .env")
        return
    try:
        res = asyncio.run(gemini_call(s))
        r.ok(f"{s.gemini_model} responde en {res.latency_ms / 1000:.2f}s ({res.input_tokens}+{res.output_tokens} tokens)")
    except Exception as exc:
        r.fail(f"{s.gemini_model} no responde ({type(exc).__name__}: {str(exc)[:100]})",
               "gcloud auth application-default login y revisa la conexión")


def check_firestore(r: Report, s) -> None:
    print("Firestore (votos y frases del público)", flush=True)
    try:
        from google.cloud import firestore
        from google.cloud.firestore_v1.base_query import FieldFilter
        from reset import _retry

        db = firestore.Client(project=s.project, database=s.firestore_database)
        t0 = time.perf_counter()
        query = db.collection("phrases").where(filter=FieldFilter("event", "==", s.event_id)).limit(1)
        list(query.stream(retry=_retry(), timeout=10))
        r.ok(f"Base {s.firestore_database} responde para el evento «{s.event_id}» ({time.perf_counter() - t0:.2f}s)")
    except Exception as exc:
        r.fail(f"Firestore no responde ({type(exc).__name__}: {str(exc)[:100]})",
               "gcloud auth application-default login y revisa la conexión")


def main() -> int:
    s = get_settings()
    region = os.environ.get("REGION", "us-central1")
    r = Report()
    check_ollama(r, s)
    check_local_services(r, s)
    check_data(r, s)
    check_audience_app(r, s, region)
    check_gemini(r, s)
    check_firestore(r, s)
    print()
    if r.failures:
        print(f"preflight FALLÓ: {r.failures} problema(s). Corrígelos antes de subir al escenario.")
    else:
        print("preflight ok: listo para la charla.")
    return r.failures


if __name__ == "__main__":
    sys.exit(main())
