"""Validate the web test set automatically against the term bank (no human in the loop).

    uv run --project duel python scripts/validate_test_set.py

Each candidate pair (status pending_review) becomes `auto_validated` or `rejected`, with the reason
in provenance.validation:
- Gen Z -> papás: the source must contain a Gen Z term of its country (or neutral LATAM), and the
  reference must have replaced it;
- papás -> Gen Z: the reference must contain a Gen Z term of its country (or LATAM);
- no term from another country in the reference;
- sane length (<= 40 words, reference 0.4x-2.5x the source);
- no duplicates inside the test set and no overlap with any training sentence.
Decisions a person made with `make review-test` (approved/rejected) are never overwritten.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

from _common import DATA
from genlingo_duel.dataset import read_jsonl, write_jsonl
from genlingo_duel.terms import TermBank

TEST = DATA / "pairs" / "test_web.jsonl"


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ ]+", " ", text)).strip()


def check(bank: TermBank, pair: dict, linked: list[str], train_text: set[str], seen: set[str]) -> str | None:
    src, ref, country = pair["source"], pair["target"], pair["country"]
    allowed = [country, "LATAM"]
    ws, wr = len(src.split()), len(ref.split())
    if ws > 40 or wr > 40 or not 0.4 <= wr / max(1, ws) <= 2.5:
        return "length"
    if norm(src) in seen:
        return "duplicate_in_test"
    if norm(src) in train_text or norm(ref) in train_text:
        return "overlaps_training"
    if bank.foreign_in(ref, country):
        return "foreign_term_in_reference"
    genz = bank.ids("genz", allowed)
    if pair["direction"] == "genz_to_parent":
        in_source = [t for t in linked if t in genz and bank.found(t, src)] or bank.found_in(src, genz)
        if not in_source:
            return "no_genz_term_in_source"
        if any(bank.found(t, ref) for t in in_source):
            return "reference_keeps_slang"
    elif not bank.found_in(ref, genz):
        return "reference_without_genz_term"
    return None


def main() -> None:
    bank = TermBank(read_jsonl(DATA / "terms.jsonl"), ignore_ambiguous=True)
    linked = {u["id"]: u.get("term_ids", []) for u in read_jsonl(DATA / "raw" / "web_usage.jsonl")}
    train_text = {norm(x) for f in ("synthetic.jsonl", "human.jsonl") for r in read_jsonl(DATA / "pairs" / f)
                  if r.get("split") == "train" for x in (r["source"], r["target"])}
    rows, seen, reasons = list(read_jsonl(TEST)), set(), Counter()
    for r in rows:
        if r["status"] in ("approved", "rejected") and r["provenance"].get("validation", {}).get("by") != "auto":
            seen.add(norm(r["source"]))
            continue  # a person decided; keep it
        reason = check(bank, r, linked.get(r["provenance"].get("usage_id"), []), train_text, seen)
        seen.add(norm(r["source"]))
        r["status"] = "rejected" if reason else "auto_validated"
        r["provenance"]["validation"] = {"by": "auto", "reason": reason}
        reasons[reason or "ok"] += 1
    write_jsonl(TEST, rows)
    print(dict(reasons))


if __name__ == "__main__":
    main()
