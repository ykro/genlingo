"""Real usage sentences from the web, and how they are split between test and training.

Collection rounds live in data/raw/: web_usage.jsonl (2026-09-30, all test),
web_usage_2026-10-01.jsonl (split deterministically by id: half test, half *training* pairs anchored
in real sentences, scripts/build_real_pairs.py) and web_usage_2026-10-02.jsonl and web_usage_2026-10-06.jsonl (training and dev only).
A sentence is never in two of test, dev and training.
"""

from __future__ import annotations

import hashlib

from _common import DATA
from genlingo_duel.dataset import read_jsonl

# round 1: all test; round 2: half test, half training; round 3: training (and dev), never test —
# the test set and the niches were frozen before round 3 existed.
ROUNDS = {"web_usage.jsonl": "test", "web_usage_2026-10-01.jsonl": "split", "web_usage_2026-10-02.jsonl": "train",
          # round 4 (2026-10-06): pan-Hispanic Gen Z and Mexico, training only (the probe has its own sources)
          "web_usage_2026-10-06.jsonl": "train"}


def assignment(row_id: str) -> str:
    return "test" if int(hashlib.sha1(row_id.encode()).hexdigest()[:8], 16) % 2 == 0 else "train"


DEV_SHARE = 5  # 1 in 5 training-half sentences is held out as dev (both directions together)


def is_dev(row_id: str) -> bool:
    """Stable: the same sentence is always dev or always train, whatever else changes."""
    return int(hashlib.sha1(f"dev|{row_id}".encode()).hexdigest()[:8], 16) % DEV_SHARE == 0


def usage_rows(split: str) -> list[dict]:
    """Usage rows assigned to `split` ("test" or "train")."""
    out = []
    for name, policy in ROUNDS.items():
        for row in read_jsonl(DATA / "raw" / name):
            target = policy if policy in ("test", "train") else assignment(row["id"])
            if target == split:
                out.append(row)
    return out
