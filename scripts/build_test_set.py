"""Turn real web usage examples into TEST pairs (status pending_review).

    uv run --project duel python scripts/build_test_set.py

The source side is a sentence someone actually wrote (found on the web, see SOURCES.md). The
reference is the dataset curator's rewrite of that sentence into the other generation's speech,
based on the meaning the source gives. Gemini never writes a test reference: if it did, chrF++
would reward Goliath for sounding like himself. The presenter reviews every pair before it is
used on stage (`make review-test`).

Existing review decisions are kept: re-running never resets a pair the presenter already
approved or rejected.
"""

from __future__ import annotations

import re

from _common import DATA
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl
from real_usage import usage_rows

AGE = {"genz": "16-24", "parent": "45-60"}


def source_licenses(sources_md: str) -> dict[str, dict[str, str]]:
    """Parse the SOURCES.md table: | id | url | owner | license | ... |"""
    out = {}
    for line in sources_md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"S\d+", cells[0]):
            out[cells[0]] = {"url": cells[1], "owner": cells[2], "license": cells[3]}
    return out


def build(usage_rows: list[dict], licenses: dict[str, dict[str, str]], previous: dict[str, dict]) -> list[dict]:
    pairs = []
    for row in usage_rows:
        direction = "genz_to_parent" if row["generation"] == "genz" else "parent_to_genz"
        pid = f"test-{row['id']}"
        lic = licenses.get(row["source_id"], {})
        pair = {
            "id": pid,
            "direction": direction,
            "source": row["example"].strip(),
            "target": row["rewrite"].strip(),
            "country": row["country"],
            "age_range": "16-24",
            "split": "test",
            "status": "pending_review",
            "origin": "web",
            "provenance": {
                "url": row["source_url"],
                "license": lic.get("license") or "see data/SOURCES.md",
                "source_id": row["source_id"],
                "owner": lic.get("owner"),
                "usage_id": row["id"],
                "example_origin": row.get("example_origin", "source"),
                "speaker_age_range": AGE[row["generation"]],
                "reference_by": "curator",
            },
        }
        prev = previous.get(pid)
        if prev and prev["status"] != "pending_review":
            pair["status"], pair["target"] = prev["status"], prev["target"]  # keep review decisions
            if "validation" in prev.get("provenance", {}):
                pair["provenance"]["validation"] = prev["provenance"]["validation"]
        Pair.model_validate(pair)
        pairs.append(pair)
    return pairs


def main() -> None:
    usage = usage_rows("test")  # round 1 + the test half of round 2 (scripts/real_usage.py)
    licenses = source_licenses((DATA / "SOURCES.md").read_text(encoding="utf-8"))
    out = DATA / "pairs" / "test_web.jsonl"
    previous = {r["id"]: r for r in read_jsonl(out)}
    n = write_jsonl(out, build(usage, licenses, previous))
    print(f"{n} test pairs -> {out.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
