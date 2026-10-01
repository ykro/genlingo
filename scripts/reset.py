"""`make reset`: back to a clean stage in seconds.

Clears the local rounds, audience queue and scoreboard (SQLite) and, when the audience feed is
on and there is network, this event's rounds and votes in Firestore. Offline, the cloud part is
skipped: the local reset alone is enough to restart the show.
"""

from __future__ import annotations

import time

from _common import ROOT  # noqa: F401
from genlingo_duel.scoreboard import Scoreboard
from genlingo_duel.settings import get_settings


def reset_firestore(s, budget_s: float = 6.0) -> str:
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter

    t0 = time.time()
    db = firestore.Client(project=s.project, database=s.firestore_database)
    n = 0
    rounds = db.collection("rounds").where(filter=FieldFilter("event", "==", s.event_id)).stream(timeout=3)
    for rnd in rounds:
        for vote in rnd.reference.collection("votes").stream(timeout=3):
            vote.reference.delete(timeout=3)
        rnd.reference.delete(timeout=3)
        n += 1
        if time.time() - t0 > budget_s:
            return f"{n} rondas borradas (parcial, tiempo agotado)"
    return f"{n} rondas borradas en Firestore"


def main() -> None:
    s = get_settings()
    t0 = time.time()
    Scoreboard(s.db_path).reset()
    msg = "local: rondas, cola y marcador en cero"
    if s.audience_feed:
        try:
            msg += f"; {reset_firestore(s)}"
        except Exception as exc:  # offline on stage: local reset is what matters
            msg += f"; Firestore omitido ({type(exc).__name__})"
    print(f"{msg} ({time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
