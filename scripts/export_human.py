"""`make export`: pull presenter-approved audience pairs from Firestore into data/.

    uv run --project duel python scripts/export_human.py

Audience pairs are `origin=human` with the event as provenance. A stable 20% (by id hash) goes
to the test split: sentences written by people in the room are test data no model wrote.
"""

from __future__ import annotations

import hashlib

from _common import DATA
from genlingo_duel.dataset import Pair, read_jsonl, write_jsonl
from genlingo_duel.settings import get_settings

OUT = DATA / "pairs" / "human.jsonl"
TEST_SHARE = 0.2


def split_for(pair_id: str) -> str:
    bucket = int(hashlib.sha1(pair_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "test" if bucket < TEST_SHARE else "train"


def to_pair(doc_id: str, d: dict) -> dict:
    return {
        "id": f"hum-{doc_id}",
        "direction": d["direction"],
        "source": d["source"].strip(),
        "target": d["target"].strip(),
        "country": d["country"],
        "age_range": d.get("ageRange") or "unknown",
        "split": split_for(doc_id),
        "status": "approved",
        "origin": "human",
        "provenance": {"event": d.get("event") or "unknown", "firestore_id": doc_id,
                       "created_at": str(d.get("createdAt") or "")},
    }


def main() -> None:
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter

    s = get_settings()
    db = firestore.Client(project=s.project, database=s.firestore_database)
    docs = db.collection("pairs").where(filter=FieldFilter("status", "==", "approved")).stream()
    existing = {r["id"]: r for r in read_jsonl(OUT)}
    for snap in docs:
        pair = to_pair(snap.id, snap.to_dict() or {})
        Pair.model_validate(pair)
        existing[pair["id"]] = pair
    n = write_jsonl(OUT, existing.values())
    print(f"{n} human pairs -> {OUT.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
