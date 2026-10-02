"""Validate the web test set automatically against the term bank (no human in the loop).

    uv run --project duel python scripts/validate_test_set.py

Each candidate pair (status pending_review) becomes `auto_validated` or `rejected`, with the reason
in provenance.validation:
- Gen Z -> papás: the source must contain a Gen Z term of its country (or neutral LATAM), and the
  reference must have replaced it;
- papás -> Gen Z: the reference must contain a Gen Z term of its country (or LATAM);
- no term from another country in the reference;
- sane length (<= 40 words, reference 0.4x-2.5x the source);
- no duplicates inside the test set and no overlap with any training file (synthetic, real-anchored,
  audience), including a test sentence quoted inside a longer training sentence or vice versa
  (raw and normalized substrings, genlingo_duel.overlap).
A human pass is optional: decisions a person made with `make review-test` (approved/rejected)
are never overwritten.
"""

from __future__ import annotations

from collections import Counter

from _common import DATA
from genlingo_duel.dataset import read_jsonl, write_jsonl
from genlingo_duel.overlap import TextIndex, norm
from genlingo_duel.terms import TermBank

TEST = DATA / "pairs" / "test_web.jsonl"
TRAIN_FILES = ("synthetic.jsonl", "real_train.jsonl", "human.jsonl")

__all__ = ["check", "norm", "training_index"]


def training_index() -> TextIndex:
    """Every sentence of every training file (both sides of each pair)."""
    return TextIndex(x for f in TRAIN_FILES for r in read_jsonl(DATA / "pairs" / f)
                     if r.get("split") == "train" for x in (r["source"], r["target"]))


def check(bank: TermBank, pair: dict, linked: list[str], other: TextIndex, seen: set[str]) -> str | None:
    src, ref, country = pair["source"], pair["target"], pair["country"]
    allowed = [country, "LATAM"]
    ws, wr = len(src.split()), len(ref.split())
    if ws > 40 or wr > 40 or not 0.4 <= wr / max(1, ws) <= 2.5:
        return "length"
    if norm(src) in seen:
        return "duplicate_in_test"
    if other.overlaps(src) or other.overlaps(ref):
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
    # The test set is validated with the bank frozen alongside it (data/eval/terms_test.jsonl), so later
    # rounds that grow the bank don't silently change which test pairs exist.
    frozen = DATA / "eval" / "terms_test.jsonl"
    bank = TermBank(read_jsonl(frozen if frozen.exists() else DATA / "terms.jsonl"), ignore_ambiguous=True)
    linked = {u["id"]: u.get("term_ids", []) for u in read_jsonl(DATA / "raw" / "web_usage.jsonl")}
    train_text = training_index()
    rows, seen, reasons = list(read_jsonl(TEST)), set(), Counter()
    for r in rows:
        if r["status"] in ("approved", "rejected") and r["provenance"].get("validation", {}).get("by") != "auto":
            seen.add(norm(r["source"]))
            continue  # a person decided; keep it
        if r["provenance"].get("validation", {}).get("reason") == "overlaps_training":
            seen.add(norm(r["source"]))
            continue  # once leaked, always out: an earlier David trained on it (even if that data is archived now)
        reason = check(bank, r, linked.get(r["provenance"].get("usage_id"), []), train_text, seen)
        seen.add(norm(r["source"]))
        r["status"] = "rejected" if reason else "auto_validated"
        r["provenance"]["validation"] = {"by": "auto", "reason": reason}
        reasons[reason or "ok"] += 1
    write_jsonl(TEST, rows)
    print(dict(reasons))


if __name__ == "__main__":
    main()
