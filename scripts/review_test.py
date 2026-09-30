"""Presenter review of the test set, as a spreadsheet round-trip.

    make review-test                     # export data/review/test_review.csv
    make review-test-apply               # apply the decisions back to data/pairs/test_web.jsonl

In the CSV, fill `decision` with `a` (approve) or `r` (reject), and optionally write a better
reference in `corrected_target`. Blank decision = still pending. Only approved pairs are used
on stage and in the headline eval numbers.
"""

from __future__ import annotations

import csv
import sys

from _common import DATA
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl

TEST = DATA / "pairs" / "test_web.jsonl"
CSV = DATA / "review" / "test_review.csv"
COLUMNS = ["id", "status", "direction", "country", "source", "target", "decision", "corrected_target", "url"]


def export() -> None:
    CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = list(read_jsonl(TEST))
    with CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({"id": r["id"], "status": r["status"], "direction": r["direction"], "country": r["country"],
                        "source": r["source"], "target": r["target"], "decision": "", "corrected_target": "",
                        "url": r["provenance"].get("url", "")})
    pending = sum(r["status"] == "pending_review" for r in rows)
    print(f"{len(rows)} pairs ({pending} pending) -> {CSV.relative_to(DATA.parent)}")


def apply() -> None:
    decisions = {}
    with CSV.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            decisions[row["id"]] = row
    updated, counts = [], {"approved": 0, "rejected": 0, "unchanged": 0}
    for r in read_jsonl(TEST):
        d = decisions.get(r["id"], {})
        choice = (d.get("decision") or "").strip().lower()
        if choice in {"a", "approve", "approved", "si", "sí"}:
            r["status"] = "approved"
            counts["approved"] += 1
        elif choice in {"r", "reject", "rejected", "no"}:
            r["status"] = "rejected"
            counts["rejected"] += 1
        else:
            counts["unchanged"] += 1
        if (d.get("corrected_target") or "").strip():
            r["target"] = d["corrected_target"].strip()
            r["provenance"]["reference_by"] = "presenter"
        Pair.model_validate(r)
        updated.append(r)
    write_jsonl(TEST, updated)
    print(counts)


if __name__ == "__main__":
    {"export": export, "apply": apply}[sys.argv[1] if len(sys.argv) > 1 else "export"]()
