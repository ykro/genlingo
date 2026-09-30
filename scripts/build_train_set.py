"""Render approved training pairs into chat JSONL for train/train_lora.py.

    uv run --project duel python scripts/build_train_set.py [--out data/train/chat.jsonl]

Uses the exact prompt of the duel (genlingo_duel.prompts): David is trained on the same
messages he receives on stage, so there is no train/serve prompt mismatch.
"""

from __future__ import annotations

import argparse
import json

from _common import DATA
from genlingo_duel.dataset import train_pairs
from genlingo_duel.prompts import translation_messages


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DATA / "train" / "chat.jsonl"))
    args = ap.parse_args()
    pairs = train_pairs(DATA)
    out = __import__("pathlib").Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for p in pairs:
            msgs = translation_messages(p.source, p.direction, p.country)
            msgs.append({"role": "assistant", "content": p.target})
            fh.write(json.dumps({"id": p.id, "origin": p.origin, "messages": msgs}, ensure_ascii=False) + "\n")
    by_origin = {}
    for p in pairs:
        by_origin[p.origin] = by_origin.get(p.origin, 0) + 1
    print(f"{len(pairs)} training examples {by_origin} -> {out}")


if __name__ == "__main__":
    main()
