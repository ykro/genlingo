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
from genlingo_duel.glossary import render as render_glossary  # noqa: E402
from genlingo_duel.prompts import COUNTRIES, translation_messages  # noqa: E402
from genlingo_duel.settings import get_settings, goliath_prices  # noqa: E402
from report import write_report  # noqa: E402


def model_plan(s, only: list[str] | None, with_goliath: bool, available: set[str]) -> list[dict]:
    """Every variant is (model, prompt style). Labels are what the report shows.

    - base models (BASE_MODEL_TAGS) with the plain v2 prompt; the first one also with the glossary,
      to separate "the glossary helps" from "fine-tuning helps";
    - Davids (DAVID_TAGS, default LOCAL_MODEL_TAG), each with the prompt style he was trained on,
      plus <tag>-f16 when it was pulled;
    - Goliath plain and Goliath with the same glossary David gets: the fair comparison.
    """
    import os

    from genlingo_duel.arena import prompt_style_for

    def add(name, role, kind, style, **kw):
        label = name + (" + glosario" if style == "v2+glossary" else "")
        plan.append({"name": name, "label": label, "role": role, "kind": kind, "style": style, **kw})

    plan: list[dict] = []
    bases = [t.strip() for t in os.environ.get("BASE_MODEL_TAGS", "").split(",") if t.strip()]
    for i, tag in enumerate(bases):
        add(tag, "base", "ollama", "v2")
        if i == 0:
            add(tag, "base", "ollama", "v2+glossary")
    davids = [t.strip() for t in os.environ.get("DAVID_TAGS", s.david_tag).split(",") if t.strip()]
    for tag in davids:
        role = "david" if tag == s.david_tag else "david_alt"
        add(tag, role, "ollama", prompt_style_for(s, tag), quant="Q4_K_M")
        add(f"{tag}-f16", "david_f16" if role == "david" else "david_alt_f16", "ollama", prompt_style_for(s, tag), quant="F16")
    if with_goliath and s.gemini_model:
        add(s.gemini_model, "goliath", "gemini", "v2")
        add(s.gemini_model, "goliath_glossary", "gemini", "v2+glossary")
    if only:
        plan = [m for m in plan if m["name"] in only or m["role"] in only or m["label"] in only]
    for m in plan:
        if m["kind"] == "ollama" and available is not None and not ({m["name"], f"{m['name']}:latest"} & available):
            m["skip"] = "no está en Ollama (make pull-model)"
    return plan


async def run_model(m: dict, client, pairs, price: Price, concurrency: int, context: dict) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    use_glossary = m["style"] == "v2+glossary"

    async def one(p):
        block, retrieval_ms = context.get(p.id, ("", 0.0)) if use_glossary else ("", 0.0)
        msgs = translation_messages(p.source, p.direction, p.country, m["style"], block)
        async with sem:
            try:
                c = await client.complete(msgs, model=m["name"])
            except Exception as exc:
                return {"pair_id": p.id, "model": m["label"], "error": f"{type(exc).__name__}: {exc}"[:200]}
        return {
            "pair_id": p.id,
            "model": m["label"],
            "text": clean_translation(c.text),
            # Retrieval is part of the answer: its time counts, as on stage.
            "latency_ms": round(c.latency_ms + retrieval_ms, 1),
            "input_tokens": c.input_tokens,
            "output_tokens": c.output_tokens,
            "cost_usd": cost_usd(price, c.input_tokens, c.output_tokens),
        }

    return list(await asyncio.gather(*(one(p) for p in pairs)))


async def glossary_context(s, pairs) -> dict:
    """Glossary block + retrieval time per test pair, computed once and shared by all variants."""
    from genlingo_duel.arena import Arena

    arena = Arena.from_settings(s)
    g = await arena.get_glossary()
    await g.embed(["calentamiento"])  # load the embedding model before timing
    out = {}
    for p in pairs:
        t0 = time.perf_counter()
        entries = await g.entries(p.source, p.direction, p.country)
        out[p.id] = (render_glossary(entries, COUNTRIES[p.country]), (time.perf_counter() - t0) * 1000)
    return out


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
    context = await glossary_context(s, pairs) if any(m["style"] == "v2+glossary" and not m.get("skip") for m in plan) else {}

    results, meta = [], []
    for m in plan:
        if m.get("skip"):
            print(f"-- {m['label']}: {m['skip']}")
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
        rows = await run_model(m, client, pairs, price, conc, context)
        m["wall_s"] = round(time.time() - t0, 1)
        errors = sum(1 for r in rows if "error" in r)
        print(f"-- {m['label']}: {len(rows) - errors} ok, {errors} errors, {m['wall_s']} s")
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
