from datetime import datetime, timezone

from fastapi.testclient import TestClient

from genlingo_duel.audience_feed import AudienceFeed
from genlingo_duel.main import create_app
from genlingo_duel.scoreboard import Scoreboard


def test_only_approved_phrases_of_this_event_reach_the_queue(tmp_path):
    board = Scoreboard(tmp_path / "s.sqlite")
    feed = AudienceFeed(board, project="p", database="genlingo", event_id="gdg", client=object())
    t = datetime(2027, 3, 1, tzinfo=timezone.utc)
    docs = [
        ("a", {"status": "approved", "event": "gdg", "text": "no manches", "direction": "genz_to_parent", "country": "MX", "approvedAt": t}),
        ("b", {"status": "pending", "event": "gdg", "text": "espera", "direction": "genz_to_parent", "country": "MX"}),
        ("c", {"status": "approved", "event": "otro", "text": "otro evento", "direction": "genz_to_parent", "country": "MX"}),
    ]
    assert feed.handle_docs(docs) == 1
    assert feed.handle_docs(docs) == 0  # idempotent: snapshots repeat documents
    assert [p["phrase_id"] for p in board.pending_phrases()] == ["a"]


def test_dueling_a_queued_phrase_marks_it_shown(settings):
    app = create_app(settings)
    board = app.state.board
    board.enqueue_phrase("a", "qué oso", "genz_to_parent", "MX", 1.0)
    with TestClient(app) as c:
        assert len(c.get("/queue").json()) == 1
        c.post("/duel", json={"phrase": "qué oso", "direction": "genz_to_parent", "country": "MX", "phrase_id": "a"})
        assert c.get("/queue").json() == []
