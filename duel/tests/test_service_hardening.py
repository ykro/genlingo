"""Review fixes: per-David scoreboard, Firestore never blocks a round, glossary fallback, local-only reset."""

import dataclasses
import threading
import time

from fastapi.testclient import TestClient

from genlingo_duel.arena import Arena
from genlingo_duel.main import create_app

DUEL = {"phrase": "estuvo bien mid", "direction": "genz_to_parent", "country": "MX"}


class SlowFeed:
    """Stands in for AudienceFeed: every Firestore call takes 2 s."""

    def __init__(self):
        self.scoreboard = None
        self.published = threading.Event()
        self.calls = []

    def publish_round(self, rnd):
        time.sleep(2)
        self.calls.append(("publish", rnd["id"]))
        self.published.set()

    def mark_shown(self, phrase_id):
        time.sleep(2)
        self.calls.append(("shown", phrase_id))

    def tally(self, round_id):
        time.sleep(2)
        return 1, 0

    def close_round(self, round_id):
        self.calls.append(("close", round_id))

    def stop(self):
        pass


def test_scoreboard_counts_only_the_requested_david(settings):
    with TestClient(create_app(settings)) as c:
        c.post("/duel", json=DUEL)
        c.post("/duel", json={**DUEL, "david_tag": "genlingo-2026-09"})
        c.post("/duel", json={**DUEL, "david_tag": "genlingo-2026-09"})
        now, old = c.get("/scoreboard").json(), c.get("/scoreboard", params={"david_tag": "genlingo-2026-09"}).json()
    assert now["rounds"] == 1 and old["rounds"] == 2 and now["rounds_all_davids"] == 3
    assert now["david_tag"] == "genlingo-test" and old["david_tag"] == "genlingo-2026-09"


def test_firestore_writes_run_in_the_background(settings):
    feed = SlowFeed()
    with TestClient(create_app(settings, feed=feed)) as c:
        t0 = time.perf_counter()
        r = c.post("/duel", json={**DUEL, "phrase_id": "abc"})
        elapsed = time.perf_counter() - t0
        assert r.status_code == 200 and elapsed < 1.5  # the 2 s Firestore write didn't block the round
        assert feed.published.wait(5)


def test_offline_skips_firestore_and_latency_does_not_grow(settings):
    feed = SlowFeed()
    offline = dataclasses.replace(settings, force_offline=True, audience_feed=True)
    with TestClient(create_app(offline, feed=feed)) as c:
        t0 = time.perf_counter()
        r = c.post("/duel", json=DUEL).json()
        elapsed = time.perf_counter() - t0
        votes = c.get(f"/rounds/{r['id']}/votes").json()
        closed = c.post(f"/rounds/{r['id']}/close").json()
    assert r["goliath"]["status"] == "offline" and elapsed < 1.5
    assert votes["live"] is False and closed["id"] == r["id"]
    time.sleep(0.2)
    assert feed.calls == []


def test_glossary_failure_degrades_to_no_glossary(settings, monkeypatch):
    s = dataclasses.replace(settings, goliath_prompt_style="glossary")

    async def broken(self):
        raise RuntimeError("embedding model not found")

    monkeypatch.setattr(Arena, "get_glossary", broken)
    with TestClient(create_app(s)) as c:
        r = c.post("/duel", json=DUEL)
    assert r.status_code == 200
    g = r.json()["goliath"]
    assert g["status"] == "ok" and g["extra"]["glossary"] == [] and "embedding" in g["extra"]["glossary_error"]


def test_reset_only_from_localhost(settings):
    with TestClient(create_app(settings)) as c:
        assert c.post("/reset", headers={"Origin": "https://evil.example"}).status_code == 403
        assert c.post("/reset", headers={"Origin": "http://127.0.0.1:3000"}).status_code == 200
        assert c.post("/reset").status_code == 200
        cors = c.options("/scoreboard", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in cors.headers


def test_ids_and_tags_are_validated(settings):
    with TestClient(create_app(settings)) as c:
        assert c.get("/rounds/../../etc").status_code in (404, 422)
        assert c.get("/rounds/not-a-round-id").status_code == 422
        assert c.post("/rounds/zzzzzzzzzzzz/close").status_code == 422
        assert c.post("/duel", json={**DUEL, "david_tag": "bad tag; rm -rf"}).status_code == 422


def test_specialty_rounds_take_gt_pairs_in_a_fixed_seeded_order(settings, make_pair):
    import json

    rows = [{**make_pair(i), "country": "GT" if i % 2 else "MX", "status": "auto_validated"} for i in range(1, 9)]
    (settings.data_dir / "pairs" / "test_web.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def run():
        with TestClient(create_app(dataclasses.replace(settings, db_path=settings.db_path.with_name(f"s{time.time_ns()}.sqlite")))) as c:
            return [c.post("/rounds/evaluation", json={"specialty": True}).json() for _ in range(3)]

    first, second = run(), run()
    assert [r["pair_id"] for r in first] == [r["pair_id"] for r in second]  # same seed, same order
    assert all(r["country"] == "GT" and r["label"] == "Ronda de especialidad: slang chapín" for r in first)
    assert len({r["pair_id"] for r in first}) == 3
