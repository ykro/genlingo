"""Bridge between the audience app (Firestore, in the cloud) and the duel service (laptop).

Phones write phrases to Firestore; the presenter approves them in /admin; this feed listens
for approved phrases and drops them into the local queue the presenter view reads. It uses a
Firestore snapshot listener (push, well under the 3 s budget) and falls back to polling.

The other direction: when a round is on screen it is published to Firestore so phones can
vote, and the tally is read back into the local scoreboard.

Everything here is best effort: with Wi-Fi off the feed goes quiet and the duel keeps working.

Firestore data model (database `genlingo`), written by the web app's API routes:
    phrases/{id}      text, direction, country, uid, event, status (pending|approved|rejected|shown),
                      createdAt, approvedAt
    rounds/{id}       event, phrase, direction, country, david, goliath, status (voting|closed)
    rounds/{id}/votes/{uid}   choice (david|goliath), createdAt  -- one vote per person
    pairs/{id}        human-contributed pairs, reviewed in /admin, exported with `make export`
    rateLimits/{uid}  lastPhraseAt (20 s between phrases, enforced server side)
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Any

from .scoreboard import Scoreboard

log = logging.getLogger("genlingo.audience_feed")


def _ts(value: Any) -> float:
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, (int, float)):
        return float(value)
    return time.time()


class AudienceFeed:
    def __init__(self, scoreboard: Scoreboard, *, project: str, database: str, event_id: str, client: Any = None):
        self.scoreboard, self.event_id = scoreboard, event_id
        self.project, self.database = project, database
        self._client = client
        self._watch = None
        self._poller: threading.Thread | None = None
        self._stop = threading.Event()
        self.last_sync: float | None = None

    @property
    def client(self):
        if self._client is None:
            from google.cloud import firestore

            self._client = firestore.Client(project=self.project, database=self.database)
        return self._client

    # ---- phrases in ---------------------------------------------------------------------
    def handle_docs(self, docs: list[tuple[str, dict[str, Any]]]) -> int:
        """Enqueue approved phrases. Pure w.r.t. Firestore so it can be tested offline."""
        added = 0
        for doc_id, d in docs:
            if d.get("status") != "approved" or d.get("event") != self.event_id:
                continue
            if self.scoreboard.enqueue_phrase(
                doc_id, d["text"], d["direction"], d["country"], _ts(d.get("approvedAt"))
            ):
                added += 1
        self.last_sync = time.time()
        return added

    def _approved_query(self):
        from google.cloud.firestore_v1.base_query import FieldFilter

        return (
            self.client.collection("phrases")
            .where(filter=FieldFilter("event", "==", self.event_id))
            .where(filter=FieldFilter("status", "==", "approved"))
        )

    def poll_once(self) -> int:
        docs = [(snap.id, snap.to_dict() or {}) for snap in self._approved_query().stream(timeout=5)]
        return self.handle_docs(docs)

    def start(self, poll_every_s: float = 2.0) -> None:
        """Listener for low latency + poller as a safety net (listeners can die silently)."""
        try:
            self._watch = self._approved_query().on_snapshot(
                lambda snaps, _changes, _at: self.handle_docs([(s.id, s.to_dict() or {}) for s in snaps])
            )
        except Exception as exc:  # no network at startup is fine
            log.warning("snapshot listener not started: %s", exc)

        def loop() -> None:
            while not self._stop.wait(poll_every_s):
                try:
                    self.poll_once()
                except Exception as exc:
                    log.debug("poll failed (offline?): %s", exc)

        self._poller = threading.Thread(target=loop, name="audience-feed", daemon=True)
        self._poller.start()

    def stop(self) -> None:
        self._stop.set()
        if self._watch is not None:
            self._watch.unsubscribe()

    def mark_shown(self, phrase_id: str) -> None:
        try:
            self.client.collection("phrases").document(phrase_id).update({"status": "shown"}, timeout=3)
        except Exception as exc:
            log.debug("mark_shown failed: %s", exc)

    # ---- rounds out, votes in -----------------------------------------------------------
    def publish_round(self, rnd: dict[str, Any]) -> None:
        from google.cloud import firestore

        try:
            self.client.collection("rounds").document(rnd["id"]).set(
                {
                    "event": self.event_id,
                    "phrase": rnd["phrase"],
                    "direction": rnd["direction"],
                    "country": rnd["country"],
                    "david": rnd["david"].get("text", ""),
                    "goliath": rnd["goliath"].get("text", ""),
                    "roundType": rnd["round_type"],
                    "number": rnd.get("number"),
                    "status": "voting",
                    "createdAt": firestore.SERVER_TIMESTAMP,
                },
                timeout=3,
            )
        except Exception as exc:
            log.warning("publish_round failed: %s", exc)

    def tally(self, round_id: str) -> tuple[int, int]:
        votes = self.client.collection("rounds").document(round_id).collection("votes").stream(timeout=5)
        d = g = 0
        for v in votes:
            choice = (v.to_dict() or {}).get("choice")
            d += choice == "david"
            g += choice == "goliath"
        return d, g

    def close_round(self, round_id: str) -> None:
        try:
            self.client.collection("rounds").document(round_id).update({"status": "closed"}, timeout=3)
        except Exception as exc:
            log.debug("close_round failed: %s", exc)
