"""`make check-candidates`: try candidate page examples live, each with its own country, before adding them.

The page's examples have to show what David wins. A candidate qualifies only if, N times out of N (3 by
default), David gets every slang term right and Goliath gets at least one wrong, by the page's own ✓/✗ check
(duel/genlingo_duel/term_check.py), and its human reference was reviewed as correct (`reference_ok` in the
candidates file). It also has to be text we may show (an open-licensed source or a sentence the curator
wrote) and a test sentence David never trained on.

The deployed page only translates typed text with Guatemalan slang, so this calls the services the way the
page does, with the page's own code (the arena: same prompts, glossary, David's private GPU service with an
identity token, Gemini on Vertex AI), passing each candidate's country. It wakes David if he is cold.

    make check-candidates [CANDIDATES=evals/experiments/<file>.json] [RUNS=3] [ONLY=MX,CO]

Reads the candidates file ({"candidates": [{"pair_id", "reference_ok", "note"}]}), writes the live answers
next to it (<file>.live.json) and the results table into <file>.md, between the "live" markers.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from _common import ROOT
from genlingo_duel.arena import Arena
from genlingo_duel.dataset import load_pairs, read_jsonl
from genlingo_duel.glossary import load_counterparts
from genlingo_duel.overlap import TextIndex
from genlingo_duel.settings import get_settings
from genlingo_duel.term_check import term_checks
from genlingo_duel.terms import TermBank

START, END = "<!-- live:start -->", "<!-- live:end -->"
DIRECTIONS = {"genz_to_parent": "Gen Z → papás", "parent_to_genz": "papás → Gen Z"}
COUNTRY_NAMES = {"GT": "Guatemala", "MX": "México", "CO": "Colombia", "LATAM": "español neutro"}


def shown_text_ok(public_row: dict) -> str | None:
    """None if the page may show this pair; else why not (a closed source's quoted text is never shown)."""
    if public_row.get("redacted"):
        return "texto de una fuente cerrada"
    return None


def training_index(data_dir: Path) -> TextIndex:
    """Everything a David could have trained on: every training pair, and the rendered chat set of the last training."""
    texts = [x for p in load_pairs(data_dir) if p.split == "train" for x in (p.source, p.target)]
    for f in sorted((data_dir / "train").glob("chat*.jsonl")):
        texts += [m["content"] for r in read_jsonl(f) for m in r["messages"] if m["role"] in ("user", "assistant")]
    return TextIndex(texts)


def verdict(runs: list[dict], reference_ok: bool | None) -> tuple[bool, str]:
    """(qualifies, why). Each run: {"david": {"ok": bool|None, "terms": [...]}, "goliath": {...}}."""
    d_all = sum(1 for r in runs if r["david"]["terms"] and all(t["ok"] for t in r["david"]["terms"]))
    g_miss = sum(1 for r in runs if r["goliath"]["text"] and r["goliath"]["terms"] and not all(t["ok"] for t in r["goliath"]["terms"]))
    n = len(runs)
    why = f"David {d_all}/{n} todo ✓ · Goliath falla {g_miss}/{n}"
    if reference_ok is not True:
        why += " · referencia " + ("sin revisar" if reference_ok is None else "incorrecta")
    return d_all == n and g_miss == n and reference_ok is True, why


async def one_side(arena: Arena, side: str, pair, bank, cps) -> dict:
    res = await arena.translate_one(side, pair.source, pair.direction, pair.country)
    text = res.text if res.status == "ok" else None
    terms = term_checks(bank, cps, pair.source, pair.direction, pair.country, text, pair.target) if text else []
    return {"text": text, "error": res.error, "latency_ms": res.latency_ms, "terms": terms}


async def wake(arena: Arena) -> float:
    """Start David's GPU instance if it is cold and load both models, as the page does when it opens."""
    s, client, t0 = arena.settings, arena.david_client, time.time()
    if s.mock_ai:
        return 0.0
    loaded = await client.loaded_models(timeout_s=600)  # type: ignore[attr-defined]
    if s.david_tag not in loaded:
        await client.warm_up(s.david_tag)  # type: ignore[attr-defined]
    if s.embedding_model and s.embedding_model not in loaded:
        await client.warm_up_embedding(s.embedding_model)  # type: ignore[attr-defined]
    await arena.get_glossary()
    return time.time() - t0


async def run(path: Path, runs: int, only: set[str]) -> int:
    spec = json.loads(path.read_text(encoding="utf-8"))
    s = get_settings()
    arena = Arena.from_settings(s)
    pairs = {p.id: p for p in load_pairs(s.data_dir) if p.split == "test" and p.status in ("auto_validated", "approved")}
    public = {r["id"]: r for r in (json.loads(l) for l in (s.data_dir / "pairs" / "test_web.jsonl").read_text().splitlines() if l.strip())}
    frozen = s.data_dir / "eval" / "terms_test.jsonl"
    bank = TermBank(read_jsonl(frozen if frozen.exists() else s.data_dir / "terms.jsonl"), ignore_ambiguous=True)
    cps = load_counterparts(s.data_dir / "counterparts.jsonl")
    trained = training_index(s.data_dir)
    print(f"David {s.david_tag} · Goliath {s.gemini_model} · {runs} vueltas", flush=True)
    print(f"David listo en {await wake(arena):.0f} s", flush=True)
    sem = asyncio.Semaphore(4)

    async def check(c: dict) -> dict:
        pid = c["pair_id"]
        p = pairs.get(pid)
        why_not = ("no está en el set de prueba" if p is None else shown_text_ok(public.get(pid, {}))
                   or ("David pudo entrenar con ella" if trained.overlaps(p.source) or trained.overlaps(p.target) else None))
        out = {**c, "country": p.country if p else None, "direction": p.direction if p else None,
               "text": p.source if p else None, "reference": p.target if p else None,
               "source_id": p.provenance.get("source_id") if p else None, "runs": []}
        if why_not:
            out.update(qualifies=False, why=why_not)
            return out
        async with sem:
            for _ in range(runs):
                d, g = await asyncio.gather(one_side(arena, "david", p, bank, cps), one_side(arena, "goliath", p, bank, cps))
                out["runs"].append({"david": d, "goliath": g})
        out["qualifies"], out["why"] = verdict(out["runs"], c.get("reference_ok"))
        print(f"{'OK' if out['qualifies'] else '--'} {p.country} {pid}: {out['why']}", flush=True)
        return out

    todo = [c for c in spec["candidates"] if not only or (pairs.get(c["pair_id"]) and pairs[c["pair_id"]].country in only)]
    results = await asyncio.gather(*(check(c) for c in todo))
    live = {"checked_at": time.strftime("%Y-%m-%d %H:%M"), "david_model": s.david_tag, "goliath_model": s.gemini_model,
            "runs": runs, "mock": s.mock_ai, "results": results}
    path.with_suffix(".live.json").write_text(json.dumps(live, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_table(path.with_suffix(".md"), live)
    print(f"{sum(r['qualifies'] for r in results)} de {len(results)} pasan -> {path.with_suffix('.md')}")
    return 0


def _answers(r: dict, side: str) -> str:
    seen: dict[str, int] = {}
    for run in r["runs"]:
        a = run[side]
        mark = "✓" if a["terms"] and all(t["ok"] for t in a["terms"]) else "✗"
        key = f"{a['text'] or '(sin respuesta)'} {mark}"
        seen[key] = seen.get(key, 0) + 1
    return "<br>".join(f"{k}" + (f" ×{n}" if n > 1 else "") for k, n in seen.items())


def write_table(md: Path, live: dict) -> None:
    lines = [START, "",
             f"En vivo el {live['checked_at']}: David `{live['david_model']}`, Goliath `{live['goliath_model']}`, "
             f"{live['runs']} vueltas cada uno" + (" (**MOCK_AI=1**, ensayo)" if live["mock"] else "") + ".", ""]
    for country in ("MX", "CO", "LATAM", "GT"):
        rows = [r for r in live["results"] if r["country"] == country]
        if not rows:
            continue
        ok = sum(r["qualifies"] for r in rows)
        lines += [f"### {COUNTRY_NAMES[country]}: {ok} de {len(rows)} pasan", "",
                  "| | frase | referencia | David | Goliath | por qué |", "| --- | --- | --- | --- | --- | --- |"]
        for r in rows:
            lines.append(f"| {'✅' if r['qualifies'] else '—'} | {r['text']} <br>`{r['pair_id']}` {DIRECTIONS[r['direction']]} | "
                         f"{r['reference']} | {_answers(r, 'david') if r['runs'] else ''} | {_answers(r, 'goliath') if r['runs'] else ''} | "
                         f"{r['why']}{' · ' + r['note'] if r.get('note') else ''} |")
        lines.append("")
    lines.append(END)
    text = md.read_text(encoding="utf-8") if md.exists() else f"# {md.stem}\n\n{START}\n{END}\n"
    head, _, rest = text.partition(START)
    _, _, tail = rest.partition(END)
    md.write_text(head + "\n".join(lines) + tail, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", type=Path)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", default="", help="countries, e.g. MX,CO")
    a = ap.parse_args()
    path = a.candidates if a.candidates.is_absolute() else ROOT / a.candidates
    return asyncio.run(run(path, a.runs, {c for c in a.only.split(",") if c}))


if __name__ == "__main__":
    sys.exit(main())
