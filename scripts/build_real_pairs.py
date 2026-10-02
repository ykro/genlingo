"""Training (and dev) pairs anchored in REAL sentences (round-2 web usage, training half).

    uv run --project duel python scripts/build_real_pairs.py

Each real sentence gives two pairs: the real sentence -> the curator's rewrite into the other
generation, and the rewrite -> the real sentence (so papás -> Gen Z also learns to *produce* real
Gen Z speech). Every pair passes the same term-bank checks as the test set
(scripts/validate_test_set.py) and never overlaps a test sentence. Origin is `web`: the sentence
is real and attributed; the rewrite is the curator's (never Gemini's).
One sentence in five (stable hash, both directions together) is held out as dev: data decisions are
made on dev, never on the test set. Dev pairs also never overlap a training file.
"""

from __future__ import annotations

from collections import Counter

from _common import DATA
from build_test_set import source_licenses
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl
from genlingo_duel.terms import TermBank
from real_usage import is_dev, usage_rows
from genlingo_duel.overlap import TextIndex
from validate_test_set import check, norm

OUT = DATA / "pairs" / "real_train.jsonl"
DEV = DATA / "pairs" / "dev_real.jsonl"  # 20 % of the sentences, held out (real_usage.is_dev)


def main() -> None:
    bank = TermBank(read_jsonl(DATA / "terms.jsonl"), ignore_ambiguous=True)
    licenses = source_licenses((DATA / "SOURCES.md").read_text(encoding="utf-8"))
    # Test sentences in use (rejected ones don't count), raw and normalized substrings included.
    test_text = TextIndex(x for r in read_jsonl(DATA / "pairs" / "test_web.jsonl") if r["status"] != "rejected"
                          for x in (r["source"], r["target"]))
    seen: set[str] = set()
    pairs, reasons = [], Counter()
    for row in usage_rows("train"):
        real, rewrite = row["example"].strip(), row["rewrite"].strip()
        forward = "genz_to_parent" if row["generation"] == "genz" else "parent_to_genz"
        backward = "parent_to_genz" if forward == "genz_to_parent" else "genz_to_parent"
        lic = licenses.get(row["source_id"], {})
        split = "dev" if is_dev(row["id"]) else "train"
        for direction, source, target, kind in ((forward, real, rewrite, "real_source"), (backward, rewrite, real, "real_target")):
            pair = {
                "id": f"real-{row['id']}-{'f' if kind == 'real_source' else 'b'}",
                "direction": direction, "source": source, "target": target, "country": row["country"],
                "age_range": "16-24", "split": split, "status": "auto_validated", "origin": "web",
                "provenance": {"url": row["source_url"], "license": lic.get("license") or "see data/SOURCES.md",
                               "source_id": row["source_id"], "owner": lic.get("owner"), "usage_id": row["id"],
                               "example_origin": row.get("example_origin", "source"), "kind": kind, "reference_by": "curator"},
            }
            reason = check(bank, pair, row.get("term_ids", []), test_text, seen)
            seen.add(norm(source))
            reasons[reason or "ok"] += 1
            if reason is None:
                Pair.model_validate(pair)
                pairs.append(pair)
    # Dev must not appear in any training file either (synthetic pairs quote real sentences sometimes).
    synthetic = TextIndex(x for f in ("synthetic.jsonl", "synthetic_multi.jsonl", "human.jsonl")
                          for r in read_jsonl(DATA / "pairs" / f) for x in (r["source"], r["target"]))
    train = [p for p in pairs if p["split"] == "train"]
    real = TextIndex(x for p in train for x in (p["source"], p["target"]))  # two rewrites can be near-identical
    dev = [p for p in pairs if p["split"] == "dev" and not any(idx.overlaps(p["source"]) or idx.overlaps(p["target"])
                                                               for idx in (synthetic, real))]
    n = write_jsonl(OUT, train)
    d = write_jsonl(DEV, dev)
    print(f"{n} real training pairs -> {OUT.relative_to(DATA.parent)}, {d} dev pairs -> {DEV.relative_to(DATA.parent)}; "
          f"checks: {dict(reasons)}")


if __name__ == "__main__":
    main()
