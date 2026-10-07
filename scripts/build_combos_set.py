"""The combinations niche (evals/niche.md, amendment 2): real sentences with 2+ slang terms -> data/eval/combos.jsonl.

    uv run --project duel python scripts/build_combos_set.py

Two sources, both real web sentences (origin=web, never synthetic: a Gemini reference would favour Goliath):
1. the frozen test set's pairs (pairs/test_web.jsonl, auto_validated) whose Gen Z side has 2+ distinct Gen Z terms
   of the frozen bank (evals/combos.py), copied with their ids;
2. round-5 sentences held out for the niche (scripts/real_usage.py: held_for_combos), each in both directions,
   like the probe: the real Gen Z sentence -> the curator's parents' version, and that version -> the real sentence.

Every pair passes the test set's checks with the frozen bank (validate_test_set.check) and must not overlap,
not even as a substring, any training or dev file (all of them, including the synthetic Gen Z, multi-term and
round-5 files). A pair that fails stays in the file as `rejected` with its reason, so the niche never changes
silently. Pairs are chosen by these rules alone, never by looking at a model's output.
"""

from __future__ import annotations

import sys
from collections import Counter

from _common import DATA, ROOT
from build_test_set import source_licenses
from genlingo_duel.dataset import PAIR_FILES, Pair, read_jsonl, write_jsonl
from genlingo_duel.overlap import TextIndex
from real_usage import usage_rows
from validate_test_set import check, norm

sys.path.insert(0, str(ROOT / "evals"))
from combos import distinct_terms, frozen_bank, genz_side, is_combo  # noqa: E402

OUT = DATA / "eval" / "combos.jsonl"
SET = "combos-2026-10-07"


def training_and_dev_index() -> TextIndex:
    """Every sentence of every training and dev file (both sides)."""
    rels = [r for k, r in PAIR_FILES.items() if k != "test_web"]
    return TextIndex(x for rel in rels for r in read_jsonl(DATA / rel) for x in (r["source"], r["target"]))


def round5_pairs(licenses: dict) -> list[dict]:
    out = []
    for row in usage_rows("combos"):
        lic = licenses.get(row["source_id"], {})
        real, rewrite = row["example"].strip(), row["rewrite"].strip()
        for direction, source, target, kind in (("genz_to_parent", real, rewrite, "real_source"),
                                                ("parent_to_genz", rewrite, real, "real_target")):
            out.append({
                "id": f"combo-{row['id']}-{'f' if kind == 'real_source' else 'b'}",
                "direction": direction, "source": source, "target": target, "country": row["country"],
                "age_range": "16-24", "split": "test", "status": "pending_review", "origin": "web",
                "provenance": {"url": row["source_url"], "license": lic.get("license") or "see data/SOURCES.md",
                               "source_id": row["source_id"], "owner": lic.get("owner"), "usage_id": row["id"],
                               "example_origin": row.get("example_origin", "source"), "kind": kind,
                               "reference_by": "curator", "set": SET, "term_ids": row.get("term_ids", [])},
            })
    return out


def main() -> None:
    bank = frozen_bank(DATA)
    licenses = source_licenses((DATA / "SOURCES.md").read_text(encoding="utf-8"))
    other = training_and_dev_index()
    candidates = []
    for r in read_jsonl(DATA / "pairs" / "test_web.jsonl"):
        if r["status"] == "auto_validated" and is_combo(bank, r):
            r = {**r, "provenance": {**r["provenance"], "set": "test_web"}}
            candidates.append(r)
    candidates += round5_pairs(licenses)
    rows, reasons, seen = [], Counter(), {}
    for p in candidates:
        linked = p["provenance"].get("term_ids", [])
        key = (norm(p["source"]), p["direction"])
        reason = None
        if not is_combo(bank, p):
            reason = "fewer_than_2_terms"
        elif key in seen:
            reason = "duplicate_in_niche"
        else:
            # check() handles length, foreign slang, slang kept/missing and overlap; `seen` per direction because
            # each sentence enters twice on purpose (once per direction)
            reason = check(bank, p, linked, other, set())
        seen[key] = True
        p["status"] = "rejected" if reason else "auto_validated"
        p["provenance"]["validation"] = {"by": "auto", "reason": reason}
        p["provenance"]["combo_terms"] = distinct_terms(bank, genz_side(p), p["country"])
        reasons[reason or "ok"] += 1
        Pair.model_validate(p)
        rows.append(p)
    write_jsonl(OUT, rows)
    ok = [p for p in rows if p["status"] == "auto_validated"]
    by = Counter((p["country"], p["direction"], p["provenance"]["set"]) for p in ok)
    print(f"{len(ok)} combination pairs -> {OUT.relative_to(ROOT)}; checks: {dict(reasons)}")
    for k in sorted(by):
        print("  ", *k, by[k])


if __name__ == "__main__":
    main()
