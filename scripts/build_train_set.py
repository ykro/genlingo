"""Render approved training pairs into chat JSONL for train/train_lora.py.

    uv run --project duel python scripts/build_train_set.py [--style v2+glossary] [--out data/train/chat.jsonl]

Uses the exact prompt of the duel (genlingo_duel.prompts), including the glossary retrieved from
the term bank the same way the duel retrieves it on stage: David is trained on the same messages
he receives, so there is no train/serve prompt mismatch. The style is recorded next to the data
(chat.meta.json) and, after training, in the run file, so the duel knows how to prompt each David.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from _common import DATA
from duel_core import OllamaClient
from genlingo_duel.dataset import read_jsonl, train_pairs
from genlingo_duel.glossary import Glossary, hashing_embedder
from genlingo_duel.glossary import render as render_glossary
from genlingo_duel.prompts import COUNTRIES, STYLES, prompt_version, translation_messages
from genlingo_duel.settings import get_settings
from genlingo_duel.terms import TermBank


async def build(style: str, out: Path) -> dict:
    s = get_settings()
    pairs = train_pairs(DATA)
    glossary = None
    if style == "v2+glossary":
        bank = TermBank(read_jsonl(DATA / "terms.jsonl"))
        if s.mock_ai or not s.embedding_model:
            glossary = await Glossary(bank, hashing_embedder()).load()
        else:
            ollama = OllamaClient(s.ollama_url)
            glossary = await Glossary(bank, lambda t: ollama.embed(t, model=s.embedding_model),
                                      cache=DATA / ".cache" / "term_embeddings.json", model=s.embedding_model).load()
    out.parent.mkdir(parents=True, exist_ok=True)
    with_glossary = 0
    with out.open("w", encoding="utf-8") as fh:
        for p in pairs:
            block = ""
            if glossary is not None:
                entries = await glossary.entries(p.source, p.direction, p.country)
                block = render_glossary(entries, COUNTRIES[p.country])
                with_glossary += bool(entries)
            msgs = translation_messages(p.source, p.direction, p.country, style, block)
            msgs.append({"role": "assistant", "content": p.target})
            fh.write(json.dumps({"id": p.id, "origin": p.origin, "messages": msgs}, ensure_ascii=False) + "\n")
    by_origin: dict[str, int] = {}
    for p in pairs:
        by_origin[p.origin] = by_origin.get(p.origin, 0) + 1
    meta = {"prompt_style": style, "prompt_version": prompt_version(style), "examples": len(pairs), "by_origin": by_origin,
            "with_glossary": with_glossary, "embedding_model": s.embedding_model if glossary else None}
    out.with_name(out.stem + ".meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="v2+glossary", choices=STYLES)
    ap.add_argument("--out", default=str(DATA / "train" / "chat.jsonl"))
    args = ap.parse_args()
    meta = asyncio.run(build(args.style, Path(args.out)))
    print(f"{meta['examples']} training examples {meta['by_origin']} ({meta['prompt_version']}) -> {args.out}")


if __name__ == "__main__":
    main()
