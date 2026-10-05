"""`make reset`: back to a clean stage in seconds.

Clears the local rounds, audience queue and scoreboard (SQLite) and, when the audience feed is
on, this event's rounds and votes in Firestore (up to 3 attempts). If the cloud part fails (e.g.
offline), the local reset still stands, the failure is printed with its cause and the exit code is 1.
"""

from __future__ import annotations

import time

from _common import ROOT  # noqa: F401
from genlingo_duel.scoreboard import Scoreboard
from genlingo_duel.settings import get_settings


# Why the cloud cleanup looks like this: google-cloud-firestore's stream() with the default retry
# crashes with AttributeError ('_UnaryStreamMultiCallable' object has no attribute '_retry') on
# any error mid-stream, hiding the real one. The old loop kept the rounds stream open (3 s
# deadline) while deleting, so a slow pass hit the deadline mid-stream. Now: an explicit retry,
# the round list is read in full first, votes are listed without a stream (list_documents) and
# deletes go in batches. Up to ATTEMPTS passes; what is left is reported, never skipped silently.
ATTEMPTS = 3
BATCH = 400  # Firestore allows 500 writes per batch


def _retry():
    from google.api_core import exceptions as gexc
    from google.api_core.retry import Retry, if_exception_type

    return Retry(
        predicate=if_exception_type(gexc.ServiceUnavailable, gexc.DeadlineExceeded, gexc.InternalServerError),
        initial=0.2, maximum=1.0, timeout=8,
    )


def _delete_event_rounds(db, event_id: str) -> int:
    """One pass: delete every round of the event and its votes. Returns the rounds deleted."""
    from google.cloud.firestore_v1.base_query import FieldFilter

    retry = _retry()
    query = db.collection("rounds").where(filter=FieldFilter("event", "==", event_id))
    rounds = [snap.reference for snap in query.stream(retry=retry, timeout=10)]
    refs = []
    for rnd in rounds:
        refs.extend(rnd.collection("votes").list_documents(retry=retry, timeout=10))
        refs.append(rnd)  # after its votes
    for i in range(0, len(refs), BATCH):
        batch = db.batch()
        for ref in refs[i : i + BATCH]:
            batch.delete(ref)
        batch.commit(retry=retry, timeout=10)
    return len(rounds)


def reset_firestore(s, attempts: int = ATTEMPTS, db=None, pause_s: float = 0.5) -> tuple[bool, str]:
    """(done, message). Retries the whole pass; a pass is idempotent (deleted rounds are gone)."""
    if db is None:
        from google.cloud import firestore

        db = firestore.Client(project=s.project, database=s.firestore_database)
    deleted, errors = 0, []
    for attempt in range(1, attempts + 1):
        try:
            deleted += _delete_event_rounds(db, s.event_id)
            tries = f" (intento {attempt} de {attempts})" if attempt > 1 else ""
            return True, f"{deleted} rondas del evento «{s.event_id}» borradas en Firestore{tries}"
        except Exception as exc:  # network, deadline, permissions: retry, then report
            errors.append(f"{type(exc).__name__}: {str(exc)[:120]}")
            time.sleep(pause_s * attempt)
    return False, (f"Firestore NO quedó limpio tras {attempts} intentos ({deleted} rondas borradas); "
                   f"último error: {errors[-1]}")


def main() -> int:
    s = get_settings()
    t0 = time.time()
    Scoreboard(s.db_path).reset()
    msg = "local: rondas, cola y marcador en cero"
    if not s.audience_feed:
        print(f"{msg} ({time.time() - t0:.1f} s)")
        return 0
    done, cloud = reset_firestore(s)
    print(f"{msg}; {cloud} ({time.time() - t0:.1f} s)")
    if not done:
        # Offline on stage the local reset is what matters; say so plainly instead of hiding it.
        print("!! El marcador local sí está en cero. Con red, vuelve a correr make reset para limpiar Firestore "
              "(si no, los teléfonos pueden ver rondas viejas).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
