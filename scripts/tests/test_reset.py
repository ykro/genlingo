"""`make reset`: the Firestore cleanup retries and reports what happened instead of skipping silently."""

from types import SimpleNamespace

import reset

SETTINGS = SimpleNamespace(event_id="ensayo", project="p", firestore_database="genlingo")


def test_retries_a_failed_pass_and_reports_the_attempt(monkeypatch):
    calls = []

    def flaky(db, event_id):
        calls.append(event_id)
        if len(calls) == 1:
            raise AttributeError("'_UnaryStreamMultiCallable' object has no attribute '_retry'")
        return 2

    monkeypatch.setattr(reset, "_delete_event_rounds", flaky)
    done, msg = reset.reset_firestore(SETTINGS, db=object(), pause_s=0)
    assert done and len(calls) == 2
    assert "2 rondas" in msg and "intento 2 de 3" in msg


def test_reports_failure_with_its_cause_after_all_attempts(monkeypatch):
    def down(db, event_id):
        raise ConnectionError("sin red")

    monkeypatch.setattr(reset, "_delete_event_rounds", down)
    done, msg = reset.reset_firestore(SETTINGS, db=object(), pause_s=0)
    assert not done
    assert "NO quedó limpio tras 3 intentos" in msg and "ConnectionError: sin red" in msg
