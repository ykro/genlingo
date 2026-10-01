"""`make eval`: run the test set through every model and write evals/report.md.

    uv run --project duel python evals/run_eval.py [--limit N] [--models a,b] [--no-goliath]

Models compared (all from env vars):
  - base candidates  BASE_MODEL_TAGS      (e.g. Gemma 4 E2B vs E4B, not fine-tuned)
  - David            LOCAL_MODEL_TAG      (fine-tuned, Q4) and LOCAL_MODEL_TAG-f16 if pulled
  - Goliath          GEMINI_MODEL

Honest-eval rules baked in: same prompt for everyone, test pairs are never synthetic, local
models are warmed up first (a cold load is not "latency"), and every per-sentence result is
saved so David's losses can be shown, not just his wins.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))
sys.path.insert(0, str(ROOT / "evals"))

from duel_core import GeminiClient, MockClient, OllamaClient, Price, clean_translation, cost_usd  # noqa: E402
from genlingo_duel.dataset import test_pairs  # noqa: E402
from genlingo_duel.prompts import translation_messages  # noqa: E402
from genlingo_duel.settings import get_settings, goliath_prices  # noqa: E402
from report import write_report  # noqa: E402


def model_plan(s, only: list[str] | None, with_goliath: bool, available: set[str]) -> list[dict]:
    import os

    plan = []
    for tag in [t.strip() for t in os.environ.get("BASE_MODEL_TAGS", "").split(",") if t.strip()]:
        plan.append({"name": tag, "role": "base", "kind": "ollama"})
    if s.david_tag:
        plan.append({"name": s.david_tag, "role": "david", "kind": "ollama", "quant": "Q4_K_M"})
        plan.append({"name": f"{s.david_tag}-f16", "role": "david_f16", "kind": "ollama", "quant": "F16"})
    if with_goliath and s.gemini_model:
        plan.append({"name": s.gemini_model, "role": "goliath", "kind": "gemini"})
    if only:
        plan = [m for m in plan if m["name"] in only or m["role"] in only]
    for m in plan:
        if m["kind"] == "ollama" and available is not None and not ({m["name"], f"{m['name']}:latest"} & available):
            m["skip"] = "no está en Ollama (make pull-model)"
    return plan


async def run_model(m: dict, client, pairs, price: Price, concurrency: int) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)

    async def one(p):
        msgs = translation_messages(p.source, p.direction, p.country)
        async with sem:
            try:
                c = await client.complete(msgs, model=m["name"])
            except Exception as exc:
                return {"pair_id": p.id, "model": m["name"], "error": f"{type(exc).__name__}: {exc}"[:200]}
        return {
            "pair_id": p.id,
            "model": m["name"],
            "text": clean_translation(c.text),
            "latency_ms": round(c.latency_ms, 1),
            "input_tokens": c.input_tokens,
            "output_tokens": c.output_tokens,
            "cost_usd": cost_usd(price, c.input_tokens, c.output_tokens),
        }

    return list(await asyncio.gather(*(one(p) for p in pairs)))


async def main_async(args) -> None:
    s = get_settings()
    pairs = test_pairs(s.data_dir)
    reviewed = True
    if not pairs:  # before the presenter's review: rehearsal numbers, clearly labelled
        pairs, reviewed = test_pairs(s.data_dir, include_pending=True), False
    if args.limit:
        # Deterministic, stratified-ish sample: every k-th pair keeps country/direction mix.
        k = max(1, len(pairs) // args.limit)
        pairs = pairs[::k][: args.limit]
    if not pairs:
        sys.exit("no test pairs: run scripts/build_test_set.py first")

    ollama = MockClient(lambda msgs: msgs[-1]["content"]) if s.mock_ai else OllamaClient(s.ollama_url, temperature=0.0)
    available, sizes = None, {}
    if not s.mock_ai:
        models = await ollama.list_models()
        available = {x["name"] for x in models} | {x["model"] for x in models}
        sizes = {x["name"]: x.get("size") for x in models}
    only = [x.strip() for x in args.models.split(",")] if args.models else None
    plan = model_plan(s, only, not args.no_goliath, available)

    results, meta = [], []
    for m in plan:
        if m.get("skip"):
            print(f"-- {m['name']}: {m['skip']}")
            meta.append(m)
            continue
        if m["kind"] == "gemini":
            client = MockClient() if s.mock_ai else GeminiClient(s.project, s.location, temperature=0.0, thinking_level=s.gemini_thinking_level or None, timeout_s=60)
            price, conc = goliath_prices(s).at(), 4  # price in force on the eval date
            m["price"] = {"input_per_million": price.input_per_million, "output_per_million": price.output_per_million,
                          "effective_from": price.effective_from}
            nxt = goliath_prices(s).next_after()
            if nxt:
                m["next_price"] = {"input_per_million": nxt.input_per_million, "output_per_million": nxt.output_per_million,
                                   "effective_from": nxt.effective_from}
        else:
            client, price, conc = ollama, Price.free(), 1  # one at a time: latency as on stage
            if not s.mock_ai:
                await ollama.warm_up(m["name"])
            m["size_bytes"] = sizes.get(m["name"]) or sizes.get(f"{m['name']}:latest")
        t0 = time.time()
        rows = await run_model(m, client, pairs, price, conc)
        m["wall_s"] = round(time.time() - t0, 1)
        errors = sum(1 for r in rows if "error" in r)
        print(f"-- {m['name']}: {len(rows) - errors} ok, {errors} errors, {m['wall_s']} s")
        results += rows
        meta.append(m)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / "evals" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = {
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "reviewed": reviewed,
        "mock": s.mock_ai,
        "models": meta,
        "pairs": [p.model_dump() for p in pairs],
        "results": results,
        "david_tag": s.david_tag,
    }
    (out_dir / f"{stamp}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1))
    report = write_report(raw, ROOT / "evals" / "report.md", runs_dir=s.runs_dir)
    print(f"report -> evals/report.md ({len(report)} chars), raw -> evals/results/{stamp}.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--models", default="")
    ap.add_argument("--no-goliath", action="store_true")
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
