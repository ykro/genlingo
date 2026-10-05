"""`make eval`: run the test set through every model and write evals/report.md.

    uv run --project duel python evals/run_eval.py [--limit N] [--models a,b] [--no-goliath]

Models compared (all from env vars):
  - base candidates  BASE_MODEL_TAGS      (e.g. Gemma 4 E2B vs E4B, not fine-tuned)
  - David            LOCAL_MODEL_TAG      (fine-tuned, Q4) and LOCAL_MODEL_TAG-f16 if pulled
  - Goliath          GEMINI_MODEL

Eval rules baked in: same prompt for everyone, test pairs are never synthetic, local
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
from genlingo_duel.dataset import load_pairs, test_pairs  # noqa: E402
from genlingo_duel.glossary import render as render_glossary  # noqa: E402
from genlingo_duel.prompts import COUNTRIES, GLOSSARY_STYLES, translation_messages  # noqa: E402
from genlingo_duel.rerank import NBestClient, term_bank_scorer  # noqa: E402
from genlingo_duel.settings import get_settings, goliath_prices  # noqa: E402
from report import write_report  # noqa: E402


def model_plan(s, only: list[str] | None, with_goliath: bool, available: set[str], nbest: int = 1) -> list[dict]:
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
        label = name + {"glossary": " + glosario", "lexicon": " + léxico"}.get(style, "") + kw.pop("suffix", "")
        plan.append({"name": name, "label": label, "role": role, "kind": kind, "style": style, **kw})

    # The glossary everyone else gets is the one the stage David uses (lexicon or glossary).
    stage_style = prompt_style_for(s, s.david_tag)
    gstyle = stage_style if stage_style in GLOSSARY_STYLES else "glossary"

    plan: list[dict] = []
    bases = [t.strip() for t in os.environ.get("BASE_MODEL_TAGS", "").split(",") if t.strip()]
    for i, tag in enumerate(bases):
        add(tag, "base", "ollama", "country")
        if i == 0:
            add(tag, "base", "ollama", gstyle)
    davids = [t.strip() for t in os.environ.get("DAVID_TAGS", s.david_tag).split(",") if t.strip()]
    for tag in davids:
        role = "david" if tag == s.david_tag else "david_alt"
        add(tag, role, "ollama", prompt_style_for(s, tag), quant=quant_of(s, tag))
        if nbest > 1 and prompt_style_for(s, tag) in GLOSSARY_STYLES:  # same David, N candidates reranked
            add(tag, role + "_nbest", "ollama", prompt_style_for(s, tag), quant=quant_of(s, tag), nbest=nbest,
                suffix=f" · N-best {nbest}")
        if available is None or {f"{tag}-f16", f"{tag}-f16:latest"} & available:  # only if it was pulled
            add(f"{tag}-f16", "david_f16" if role == "david" else "david_alt_f16", "ollama", prompt_style_for(s, tag), quant="F16")
    if with_goliath and s.gemini_model:
        add(s.gemini_model, "goliath", "gemini", "country")
        add(s.gemini_model, "goliath_glossary", "gemini", gstyle)
    if only:
        plan = [m for m in plan if m["name"] in only or m["role"] in only or m["label"] in only]
    for m in plan:
        if m["kind"] == "ollama" and available is not None and not ({m["name"], f"{m['name']}:latest"} & available):
            m["skip"] = "no está en Ollama (make pull-model)"
    return plan


def quant_of(s, tag: str) -> str:
    """Quantization of a David export: from the tag suffix (-q5_k_m, -iq-q4_k_m…), else from its run file."""
    import re

    from genlingo_duel.runs import load_run

    m = re.search(r"-(?:iq-)?(q\d_k_m|q\d_k|q8_0)$", tag)
    if m:
        return m.group(1).upper()
    run = load_run(s.runs_dir, tag) or {}
    return run.get("quant") or (run.get("finish") or {}).get("quant") or (run.get("metrics") or {}).get("quant") or "Q4_K_M"


async def run_model(m: dict, client, pairs, price: Price, concurrency: int, context: dict, bank=None) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    ctx = context.get(m["style"], {})

    async def one(p):
        block, retrieval_ms, entries = ctx.get(p.id, ("", 0.0, []))
        msgs = translation_messages(p.source, p.direction, p.country, m["style"], block)
        c_client = client
        if m.get("nbest", 1) > 1:
            c_client = NBestClient(client, m["nbest"], term_bank_scorer(bank, p.source, p.direction, p.country, entries))
        async with sem:
            try:
                c = await c_client.complete(msgs, model=m["name"])
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


async def glossary_context(s, pairs, styles: set[str]) -> tuple[dict, object]:
    """Per glossary style: (block, retrieval ms, entries) per pair, computed once and shared by all variants."""
    from genlingo_duel.arena import Arena

    arena = Arena.from_settings(s)
    g = await arena.get_glossary()
    await g.embed(["calentamiento"])  # load the embedding model before timing
    out: dict[str, dict] = {}
    for style in styles:
        out[style] = {}
        for p in pairs:
            t0 = time.perf_counter()
            if GLOSSARY_STYLES[style] == "lex":
                entries = await g.lex_entries(p.source, p.direction, p.country)
            else:
                entries = await g.entries(p.source, p.direction, p.country)
            out[style][p.id] = (render_glossary(entries, COUNTRIES[p.country]), (time.perf_counter() - t0) * 1000, entries)
    return out, g.bank


async def main_async(args) -> None:
    s = get_settings()
    if args.split == "dev":  # data decisions are made here; the test set is touched once per round
        pairs = [p for p in load_pairs(s.data_dir, ["pairs/dev_real.jsonl"]) if p.status in ("auto_validated", "approved")]
    else:
        pairs = test_pairs(s.data_dir)
    reviewed = True
    if not pairs:  # before validate_test_set ran: rehearsal numbers, clearly labelled
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
    plan = model_plan(s, only, not args.no_goliath, available, nbest=args.nbest)
    gstyles = {m["style"] for m in plan if m["style"] in GLOSSARY_STYLES and not m.get("skip")}
    context, bank = await glossary_context(s, pairs, gstyles) if gstyles else ({}, None)

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
        rows = await run_model(m, client, pairs, price, conc, context, bank)
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
    if args.merge_with:
        # Add these variants to an earlier run (same test set): the report compares all of them.
        prev = json.loads(Path(args.merge_with).read_text())
        assert [p["id"] for p in prev["pairs"]] == [p["id"] for p in raw["pairs"]], "different test set"
        new_labels = {m.get("label", m["name"]) for m in raw["models"]}
        kept = [m for m in prev["models"] if m.get("label", m["name"]) not in new_labels]
        if any(m.get("role") == "david" for m in raw["models"]):  # one on-stage David: the current LOCAL_MODEL_TAG
            for m in kept:
                if m.get("role") in ("david", "david_f16"):
                    m["role"] = m["role"].replace("david", "david_alt", 1)
        raw["models"] = kept + raw["models"]
        raw["results"] = [r for r in prev["results"] if r["model"] not in new_labels] + raw["results"]
        raw["merged_from"] = Path(args.merge_with).name
    raw["split"] = args.split
    if args.latency_from:  # quality from this run, latency from a separate exclusive run of the same models
        lr = json.loads(Path(args.latency_from).read_text())
        by = {}
        for r in lr["results"]:
            if "error" not in r and r.get("latency_ms") is not None:
                by.setdefault(r["model"], []).append(r["latency_ms"])
        raw["latency"] = {"file": Path(args.latency_from).name, "n": len(lr["pairs"]), "by_model": by}
    name = f"{stamp}.json" if args.split == "test" else f"dev-{stamp}.json"
    (out_dir / name).write_text(json.dumps(raw, ensure_ascii=False, indent=1))
    report_path = ROOT / "evals" / ("report.md" if args.split == "test" else "report_dev.md")
    report = write_report(raw, report_path, runs_dir=s.runs_dir)
    print(f"report -> {report_path.relative_to(ROOT)} ({len(report)} chars), raw -> evals/results/{name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--models", default="")
    ap.add_argument("--no-goliath", action="store_true")
    ap.add_argument("--merge-with", default="", help="earlier raw results to merge these variants into")
    ap.add_argument("--split", choices=["test", "dev"], default="test", help="dev: data decisions; test: once per round")
    ap.add_argument("--latency-from", default="", help="raw results of an exclusive latency run (p50/p95 come from there)")
    ap.add_argument("--nbest", type=int, default=int(__import__("os").environ.get("EVAL_NBEST", "1")),
                    help="also run each glossary-trained David with N candidates reranked by the term bank")
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
