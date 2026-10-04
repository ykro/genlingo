"""Attach the latencies of an exclusive run to a quality run and re-render its report.

    uv run --project duel python evals/attach_latency.py evals/results/<quality>.json evals/results/<latency>.json

Quality evals may share the laptop with other models (only chrF++ and term metrics count there);
p50/p95 come from a short run with nothing else loaded in Ollama (`run_eval.py --limit 50`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))
sys.path.insert(0, str(ROOT / "evals"))

from report import write_report  # noqa: E402


def main() -> None:
    quality, latency = Path(sys.argv[1]), Path(sys.argv[2])
    raw, lr = json.loads(quality.read_text()), json.loads(latency.read_text())
    by: dict[str, list[float]] = {}
    for r in lr["results"]:
        if "error" not in r and r.get("latency_ms") is not None:
            by.setdefault(r["model"], []).append(r["latency_ms"])
    raw["latency"] = {"file": latency.name, "n": len(lr["pairs"]), "by_model": by}
    quality.write_text(json.dumps(raw, ensure_ascii=False, indent=1))
    out = ROOT / "evals" / ("report_dev.md" if raw.get("split") == "dev" else "report.md")
    write_report(raw, out, runs_dir=ROOT / "train" / "runs")
    print(f"latency from {latency.name} ({len(by)} models) -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
