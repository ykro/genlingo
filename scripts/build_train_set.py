"""Render approved training pairs into chat JSONL for train/train_lora.py.

    uv run --project duel python scripts/build_train_set.py [--style lexicon] [--out data/train/chat.jsonl]

Uses the exact prompt of the duel (genlingo_duel.prompts), including the glossary retrieved from
the term bank the same way the duel retrieves it on stage: David is trained on the same messages
he receives, so there is no train/serve prompt mismatch. The style is recorded next to the data
(chat.meta.json) and, after training, in the run file, so the duel knows how to prompt each David.

lexicon (the default): the glossary is built exactly as on stage (Glossary.lex_entries), and then the
answer is made visible on purpose: in GOLD_SHARE of the examples every target-side term of the
reference is in the glossary (added if retrieval missed it), in the rest it is removed, so David
learns to use the glossary when it has the answer and to cope when it doesn't. Entries are shuffled.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
from pathlib import Path

GOLD_SHARE = 0.85

from _common import DATA
from duel_core import OllamaClient
from genlingo_duel.dataset import read_jsonl, train_pairs
from genlingo_duel.glossary import LEX_K, Glossary, hashing_embedder, load_counterparts
from genlingo_duel.glossary import render as render_glossary
from genlingo_duel.prompts import COUNTRIES, GLOSSARY_STYLES, STYLES, prompt_version, translation_messages
from genlingo_duel.settings import get_settings
from genlingo_duel.terms import TermBank


def _ids(files: set[str]) -> list[set[str]]:
    return [{r["id"] for r in read_jsonl(DATA / f)} for f in files]


def with_gold(glossary: Glossary, bank: TermBank, entries: list[dict], p) -> tuple[list[dict], list[str], bool]:
    """Show every target-side term of the reference in GOLD_SHARE of the examples, hide it in the rest."""
    target_gen = "genz" if p.direction == "parent_to_genz" else "parent"
    gold = bank.found_in(p.target, bank.ids(target_gen, [p.country, "LATAM"]))
    rng = random.Random(hashlib.sha1(p.id.encode()).hexdigest())
    if not gold:
        return entries, gold, False
    show = rng.random() < GOLD_SHARE
    out = []
    for e in entries:
        cp = e.get("counterpart")
        if not show and e["id"] in gold:
            continue
        if not show and cp and cp["id"] in gold:
            e = {**e, "counterpart": None}
        out.append(e)
    if show:
        present = {e["id"] for e in out} | {e["counterpart"]["id"] for e in out if e.get("counterpart")}
        for g in gold:
            if g in present:
                continue
            if len(out) >= LEX_K:  # make room: drop a retrieved neighbour, never a link or the foreign term
                near = [i for i, e in enumerate(out) if e.get("role") == "near"]
                if not near:
                    break
                out.pop(near[-1])
            out.append(glossary._entry(g, role="near"))
    rng.shuffle(out)
    return out, gold, show


async def build(style: str, out: Path, exclude: tuple[str, ...] = ()) -> dict:
    s = get_settings()
    from genlingo_duel.dataset import PAIR_FILES

    skip = {PAIR_FILES[k] for k in exclude}  # ablations: leave a whole data file out
    skip_ids = set().union(*_ids(skip)) if skip else set()
    pairs = [p for p in train_pairs(DATA) if p.id not in skip_ids]
    glossary = None
    bank = TermBank(read_jsonl(DATA / "terms.jsonl"))
    if style in GLOSSARY_STYLES:
        cps = load_counterparts(DATA / "counterparts.jsonl")
        if s.mock_ai or not s.embedding_model:
            glossary = await Glossary(bank, hashing_embedder(), counterparts=cps).load()
        else:
            ollama = OllamaClient(s.ollama_url)
            glossary = await Glossary(bank, lambda t: ollama.embed(t, model=s.embedding_model),
                                      cache=DATA / ".cache" / "term_embeddings.json", model=s.embedding_model,
                                      counterparts=cps).load()
    gold_rows = gold_shown = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with_glossary = 0
    with out.open("w", encoding="utf-8") as fh:
        for p in pairs:
            block = ""
            if glossary is not None:
                if GLOSSARY_STYLES[style] == "lex":
                    entries = await glossary.lex_entries(p.source, p.direction, p.country)
                    entries, gold, shown = with_gold(glossary, bank, entries, p)
                    gold_rows += bool(gold)
                    gold_shown += bool(gold) and shown
                else:
                    entries = await glossary.entries(p.source, p.direction, p.country)
                block = render_glossary(entries, COUNTRIES[p.country])
                with_glossary += bool(entries)
            msgs = translation_messages(p.source, p.direction, p.country, style, block)
            msgs.append({"role": "assistant", "content": p.target})
            fh.write(json.dumps({"id": p.id, "origin": p.origin, "messages": msgs}, ensure_ascii=False) + "\n")
    by_origin: dict[str, int] = {}
    for p in pairs:
        by_origin[p.origin] = by_origin.get(p.origin, 0) + 1
    meta = {"excluded": list(exclude), "prompt_style": style, "prompt_version": prompt_version(style), "examples": len(pairs), "by_origin": by_origin,
            "with_glossary": with_glossary, "embedding_model": s.embedding_model if glossary else None,
            "gold_in_glossary": round(gold_shown / gold_rows, 3) if gold_rows else None}
    out.with_name(out.stem + ".meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="lexicon", choices=STYLES)
    ap.add_argument("--out", default=str(DATA / "train" / "chat.jsonl"))
    ap.add_argument("--exclude", default="", help="comma-separated PAIR_FILES keys to leave out (ablations)")
    args = ap.parse_args()
    meta = asyncio.run(build(args.style, Path(args.out), tuple(k for k in args.exclude.split(",") if k)))
    print(f"{meta['examples']} training examples {meta['by_origin']} ({meta['prompt_version']}) -> {args.out}")


if __name__ == "__main__":
    main()
