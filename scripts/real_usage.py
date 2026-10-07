"""Real usage sentences from the web, and how they are split between test and training.

Collection rounds live in data/raw/: web_usage.jsonl (2026-09-30, all test),
web_usage_2026-10-01.jsonl (split deterministically by id: half test, half *training* pairs anchored
in real sentences, scripts/build_real_pairs.py) and web_usage_2026-10-02.jsonl and web_usage_2026-10-06.jsonl (training and dev only).
Round 5 (web_usage_2026-10-07.jsonl) holds sentences that combine several slang terms: half of those that meet
the combinations rule (evals/combos.py) are held out for the combinations niche (evals/niche.md, amendment 2;
scripts/build_combos_set.py), by a stable hash of the id; the rest go to training and dev like round 3.
A sentence is never in two of test, dev, the combinations niche and training.
"""

from __future__ import annotations

import hashlib

from _common import DATA
from genlingo_duel.dataset import read_jsonl

# round 1: all test; round 2: half test, half training; round 3: training (and dev), never test —
# the test set and the niches were frozen before round 3 existed.
ROUNDS = {"web_usage.jsonl": "test", "web_usage_2026-10-01.jsonl": "split", "web_usage_2026-10-02.jsonl": "train",
          # round 4 (2026-10-06): pan-Hispanic Gen Z and Mexico, training only (the probe has its own sources)
          "web_usage_2026-10-06.jsonl": "train",
          # round 5 (2026-10-07): multi-term combinations; half of the combinations -> the niche, the rest training/dev
          "web_usage_2026-10-07.jsonl": "combos"}


def assignment(row_id: str) -> str:
    return "test" if int(hashlib.sha1(row_id.encode()).hexdigest()[:8], 16) % 2 == 0 else "train"


DEV_SHARE = 5  # 1 in 5 training-half sentences is held out as dev (both directions together)


def is_dev(row_id: str) -> bool:
    """Stable: the same sentence is always dev or always train, whatever else changes."""
    return int(hashlib.sha1(f"dev|{row_id}".encode()).hexdigest()[:8], 16) % DEV_SHARE == 0


def held_for_combos(row_id: str) -> bool:
    """Stable: half of the round-5 combinations are held out for the niche, decided by the id alone."""
    return int(hashlib.sha1(f"combos|{row_id}".encode()).hexdigest()[:8], 16) % 2 == 0


_FROZEN = None


def is_combo_row(row: dict) -> bool:
    """The niche's rule on the real Gen Z sentence of a usage row (frozen test bank, evals/combos.py)."""
    global _FROZEN
    import sys

    sys.path.insert(0, str(DATA.parent / "evals"))
    from combos import frozen_bank, is_combo

    if _FROZEN is None:
        _FROZEN = frozen_bank(DATA)
    if row["generation"] != "genz":
        return False
    return is_combo(_FROZEN, {"source": row["example"], "target": row["rewrite"], "direction": "genz_to_parent",
                              "country": row["country"]})


def usage_rows(split: str) -> list[dict]:
    """Usage rows assigned to `split` ("test", "train" or "combos")."""
    out = []
    for name, policy in ROUNDS.items():
        for row in read_jsonl(DATA / "raw" / name):
            if policy == "combos":
                # editor-written examples (one template for many countries) are not real speech: training only
                real = row.get("kind") != "editorial example"
                target = "combos" if real and is_combo_row(row) and held_for_combos(row["id"]) else "train"
            else:
                target = policy if policy in ("test", "train") else assignment(row["id"])
            if target == split:
                out.append(row)
    return out
