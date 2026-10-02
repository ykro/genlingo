"""Flag term-bank entries that are also ordinary Spanish words, so term-level metrics don't count them.

    uv run --project duel python scripts/flag_ambiguous_terms.py <transcripts.json>

"cámara", "servir", "alta" or "mucha" (for "muchá") are slang in some sentences and plain words in
most. We count how often each term matches in a corpus of general, non-slang speech (radio and read
speech transcripts: Hugging Face `shraavb/spanish-slang-stt-data`, CC BY 4.0, ~39k sentences). A term
matching in at least THRESHOLD sentences is marked `ambiguous: true` (with the count): the eval and the
test-set validation ignore it; the glossary still shows its meaning.
"""

from __future__ import annotations

import json
import sys

from _common import DATA
from genlingo_duel.dataset import read_jsonl, write_jsonl
from genlingo_duel.terms import TermBank, normalize

THRESHOLD = 15


def main() -> None:
    texts = [normalize(r["transcript"]) for r in json.load(open(sys.argv[1]))]
    path = DATA / "terms.jsonl"
    terms = list(read_jsonl(path))
    bank = TermBank(terms)
    flagged = 0
    for t in terms:
        hits = sum(1 for x in texts if any(p.search(x) for p in bank._patterns[t["id"]]))
        t["ambiguity_hits"] = hits
        t["ambiguous"] = hits >= THRESHOLD
        flagged += t["ambiguous"]
    write_jsonl(path, terms)
    print(f"{flagged} of {len(terms)} terms flagged ambiguous (>= {THRESHOLD} matches in {len(texts)} general sentences)")


if __name__ == "__main__":
    main()
