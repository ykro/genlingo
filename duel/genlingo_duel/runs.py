"""Map a David tag to its training run file (train/runs/<tag>.json).

Exports of one training run (-f16, -q5_k_m, -iq-q4_k_m…) are the same David, compressed
differently: they share the run's prompt style and its training cost.
"""

from __future__ import annotations

import json
from pathlib import Path


def run_file_for(runs_dir: Path, tag: str) -> Path | None:
    parts = tag.split("-")
    for n in range(len(parts), 1, -1):
        path = runs_dir / f"{'-'.join(parts[:n])}.json"
        if path.exists():
            return path
    return None


def load_run(runs_dir: Path, tag: str) -> dict | None:
    path = run_file_for(runs_dir, tag)
    return json.loads(path.read_text()) if path else None
