"""Merge the raw results of several eval runs over the same pairs and rewrite the report.

    uv run --project duel python evals/merge_results.py evals/results/A.json evals/results/B.json

A Cloud Run GPU job can run at most 1 hour, and the whole test set through every model takes longer, so
`make eval` runs the Davids and the rest (base models and Goliath) as two jobs and merges them here.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from report import write_report  # noqa: E402


def merge(paths: list[Path]) -> dict:
    runs = [json.loads(p.read_text()) for p in paths]
    ids = [p["id"] for p in runs[0]["pairs"]]
    assert all([p["id"] for p in r["pairs"]] == ids for r in runs), "the runs are over different pairs"
    out = {**runs[0], "models": [], "results": [], "merged_from": [p.name for p in paths]}
    for r in runs:
        out["models"] += r["models"]
        out["results"] += r["results"]
    return out


def main() -> None:
    paths = [Path(a) for a in sys.argv[1:]]
    raw = merge(paths)
    split = raw.get("split", "test")
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-merged.json" if split == "test" else f"{split}-{time.strftime('%Y%m%d-%H%M%S')}-merged.json"
    (ROOT / "evals" / "results" / name).write_text(json.dumps(raw, ensure_ascii=False, indent=1))
    report = ROOT / "evals" / ("report.md" if split == "test" else f"report_{split}.md")
    write_report(raw, report, runs_dir=ROOT / "train" / "runs")
    print(f"merged {len(paths)} runs -> evals/results/{name}, {report.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
