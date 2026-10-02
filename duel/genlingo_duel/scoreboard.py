"""Rounds, votes and the scoreboard, persisted in a local SQLite file.

Local on purpose: the presenter view must keep working with Wi-Fi off, and `make reset`
must bring everything back to zero in well under 10 seconds.

Who wins a round:
- evaluation round (test-set phrase with a reference): higher chrF++ wins;
- audience round (phrase from the room, no reference): the audience vote decides;
- if Goliath is offline or fails, David wins by default: showing up is part of the job.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Literal

from duel_core import ContenderResult, percentile

RoundType = Literal["evaluation", "audience"]
CHRF_TIE_MARGIN = 0.5  # chrF++ points; smaller gaps are noise on a single sentence

SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    round_type TEXT NOT NULL,
    phrase TEXT NOT NULL,
    direction TEXT NOT NULL,
    country TEXT NOT NULL,
    reference TEXT,
    pair_id TEXT,
    phrase_id TEXT,
    david_tag TEXT,
    david TEXT NOT NULL,
    goliath TEXT NOT NULL,
    winner TEXT,
    win_reason TEXT,
    votes_david INTEGER NOT NULL DEFAULT 0,
    votes_goliath INTEGER NOT NULL DEFAULT 0,
    label TEXT
);
CREATE TABLE IF NOT EXISTS audience_queue (
    phrase_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    direction TEXT NOT NULL,
    country TEXT NOT NULL,
    approved_at REAL NOT NULL,
    received_at REAL NOT NULL,
    shown INTEGER NOT NULL DEFAULT 0
);
"""


def decide_by_chrf(david: ContenderResult, goliath: ContenderResult) -> tuple[str | None, str]:
    if david.status == "ok" and goliath.status != "ok":
        return "david", f"goliath_{goliath.status}"
    if goliath.status == "ok" and david.status != "ok":
        return "goliath", f"david_{david.status}"
    if david.status != "ok":
        return None, "both_failed"
    d, g = david.chrf or 0.0, goliath.chrf or 0.0
    if abs(d - g) < CHRF_TIE_MARGIN:
        return "draw", "chrf"
    return ("david" if d > g else "goliath"), "chrf"


def decide_by_votes(votes_david: int, votes_goliath: int) -> tuple[str, str]:
    if votes_david == votes_goliath:
        return "draw", "votes"
    return ("david" if votes_david > votes_goliath else "goliath"), "votes"


class Scoreboard:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        cols = {r[1] for r in self.db.execute("PRAGMA table_info(rounds)")}
        if "label" not in cols:  # scoreboards created before round labels existed
            self.db.execute("ALTER TABLE rounds ADD COLUMN label TEXT")
            self.db.commit()

    # ---- rounds -------------------------------------------------------------------------
    def record_round(
        self,
        *,
        round_type: RoundType,
        phrase: str,
        direction: str,
        country: str,
        results: dict[str, ContenderResult],
        reference: str | None = None,
        pair_id: str | None = None,
        phrase_id: str | None = None,
        david_tag: str | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        david, goliath = results["david"], results["goliath"]
        winner, reason = None, None
        if round_type == "evaluation" or goliath.status != "ok" or david.status != "ok":
            winner, reason = decide_by_chrf(david, goliath)
        rid = uuid.uuid4().hex[:12]
        self.db.execute(
            "INSERT INTO rounds (id, created_at, round_type, phrase, direction, country, reference, pair_id,"
            " phrase_id, david_tag, david, goliath, winner, win_reason, label) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rid, time.time(), round_type, phrase, direction, country, reference, pair_id, phrase_id,
                david_tag or david.model, json.dumps(david.to_dict()), json.dumps(goliath.to_dict()), winner, reason, label,
            ),
        )
        if phrase_id:
            self.db.execute("UPDATE audience_queue SET shown = 1 WHERE phrase_id = ?", (phrase_id,))
        self.db.commit()
        return self.get_round(rid)  # type: ignore[return-value]

    def set_votes(self, round_id: str, votes_david: int, votes_goliath: int) -> dict[str, Any] | None:
        row = self.get_round(round_id)
        if row is None:
            return None
        winner, reason = row["winner"], row["win_reason"]
        if row["round_type"] == "audience" and reason in (None, "votes"):
            winner, reason = decide_by_votes(votes_david, votes_goliath)
        self.db.execute(
            "UPDATE rounds SET votes_david = ?, votes_goliath = ?, winner = ?, win_reason = ? WHERE id = ?",
            (votes_david, votes_goliath, winner, reason, round_id),
        )
        self.db.commit()
        return self.get_round(round_id)

    @staticmethod
    def _row(r: sqlite3.Row) -> dict[str, Any]:
        d = dict(r)
        d["number"] = d.pop("n", None)
        d["david"], d["goliath"] = json.loads(d["david"]), json.loads(d["goliath"])
        return d

    def get_round(self, round_id: str) -> dict[str, Any] | None:
        r = self.db.execute(
            "SELECT *, (SELECT COUNT(*) FROM rounds r2 WHERE r2.created_at <= rounds.created_at) AS n FROM rounds WHERE id = ?",
            (round_id,),
        ).fetchone()
        return self._row(r) if r else None

    def list_rounds(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT *, (SELECT COUNT(*) FROM rounds r2 WHERE r2.created_at <= rounds.created_at) AS n"
            " FROM rounds ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row(r) for r in rows]

    def used_pair_ids(self) -> set[str]:
        return {r[0] for r in self.db.execute("SELECT pair_id FROM rounds WHERE pair_id IS NOT NULL")}

    # ---- scoreboard ---------------------------------------------------------------------
    def summary(self, david_tag: str | None = None) -> dict[str, Any]:
        """Totals for one David (rounds played by `david_tag`), or for every round when None."""
        if david_tag:
            rows = self.db.execute("SELECT * FROM rounds WHERE david_tag = ?", (david_tag,)).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM rounds").fetchall()
        rounds = [self._row(r) for r in rows]
        total = self.db.execute("SELECT COUNT(*) FROM rounds").fetchone()[0]
        out: dict[str, Any] = {"rounds": len(rounds), "rounds_all_davids": total,
                               "draws": sum(1 for r in rounds if r["winner"] == "draw")}
        for name in ("david", "goliath"):
            mine = [r[name] for r in rounds]
            ok = [m for m in mine if m["status"] == "ok"]
            chrfs = [m["chrf"] for m in ok if m.get("chrf") is not None]
            out[name] = {
                "wins": sum(1 for r in rounds if r["winner"] == name),
                "avg_chrf": round(sum(chrfs) / len(chrfs), 2) if chrfs else None,
                "p50_latency_ms": percentile([m["latency_ms"] for m in ok], 50),
                "cost_usd": round(sum(m["cost_usd"] for m in ok), 6),
                "votes": sum(r[f"votes_{name}"] for r in rounds),
                "offline_rounds": sum(1 for m in mine if m["status"] == "offline"),
            }
        return out

    # ---- audience queue (filled by the Firestore feed) ----------------------------------
    def enqueue_phrase(self, phrase_id: str, text: str, direction: str, country: str, approved_at: float) -> bool:
        cur = self.db.execute(
            "INSERT OR IGNORE INTO audience_queue (phrase_id, text, direction, country, approved_at, received_at)"
            " VALUES (?,?,?,?,?,?)",
            (phrase_id, text, direction, country, approved_at, time.time()),
        )
        self.db.commit()
        return cur.rowcount > 0

    def pending_phrases(self) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM audience_queue WHERE shown = 0 ORDER BY approved_at").fetchall()
        return [dict(r) for r in rows]

    def reset(self) -> None:
        self.db.executescript("DELETE FROM rounds; DELETE FROM audience_queue;")
        self.db.commit()
