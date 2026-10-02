"""Fold a research round (data/raw/*_<date>) into the term bank and SOURCES.md.

    uv run --project duel python scripts/merge_research_round.py 2026-10-02   # the round's date

- terms_<date>.jsonl -> appended to terms.jsonl (skipping a term already present for the same country);
- sources_<date>.md -> its table rows appended to the SOURCES.md table, its notes under the round's title.
web_usage_<date>.jsonl stays in data/raw/: scripts/real_usage.py splits it (2026-10-01: test/train; 2026-10-02: train/dev).
Idempotent: running it twice adds nothing.
"""

from __future__ import annotations

import re
import sys

from _common import DATA
from genlingo_duel.dataset import read_jsonl, write_jsonl
from genlingo_duel.terms import normalize

RAW = DATA / "raw"
ROUND = sys.argv[1] if len(sys.argv) > 1 else "2026-10-01"
ROUND_TITLE = {"2026-10-01": "Round 2 (2026-10-01)", "2026-10-02": "Round 3 (2026-10-02)"}


def merge_terms() -> int:
    terms = list(read_jsonl(DATA / "terms.jsonl"))
    have = {(normalize(t["term"]), t["country"]) for t in terms} | {t["id"] for t in terms}
    added = 0
    for t in read_jsonl(RAW / f"terms_{ROUND}.jsonl"):
        if t["id"] in have or (normalize(t["term"]), t["country"]) in have:
            continue
        terms.append(t)
        have.add((normalize(t["term"]), t["country"]))
        added += 1
    write_jsonl(DATA / "terms.jsonl", terms)
    return added


def merge_sources() -> int:
    path = DATA / "SOURCES.md"
    text = path.read_text(encoding="utf-8")
    new = (RAW / f"sources_{ROUND}.md").read_text(encoding="utf-8")
    have = set(re.findall(r"^\|\s*(S\d+)\s*\|", text, flags=re.M))
    rows = [ln for ln in new.splitlines() if re.match(r"^\|\s*S\d+\s*\|", ln) and re.match(r"^\|\s*(S\d+)", ln).group(1) not in have]
    if not rows:
        return 0
    lines = text.splitlines()
    last = max(i for i, ln in enumerate(lines) if re.match(r"^\|\s*S\d+\s*\|", ln))
    lines[last + 1:last + 1] = rows
    notes = [ln for ln in new.splitlines() if ln.strip() and not ln.startswith("|") and not ln.startswith("#")]
    title = ROUND_TITLE.get(ROUND, ROUND)
    if notes and f"## {title}" not in text:
        lines += ["", f"## {title}: sources checked", "", *notes]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


if __name__ == "__main__":
    print(f"terms added: {merge_terms()}, sources added: {merge_sources()}")
