from fastapi.testclient import TestClient

from genlingo_duel.main import create_app


def client(settings):
    return TestClient(create_app(settings))


def test_health_mock(settings):
    with client(settings) as c:
        h = c.get("/health").json()
    assert h["mock"] and h["online"] and h["david_tag"] == "genlingo-test"


def test_audience_duel_returns_both_sides_with_latency_tokens_cost(settings):
    with client(settings) as c:
        r = c.post("/duel", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent", "country": "MX"}).json()
    assert r["round_type"] == "audience"
    for side in ("david", "goliath"):
        assert r[side]["status"] == "ok"
        assert r[side]["latency_ms"] > 0 and r[side]["output_tokens"] > 0
        assert r[side]["chrf"] is None  # no reference in audience rounds
    assert r["david"]["cost_usd"] == 0 and r["goliath"]["cost_usd"] > 0
    assert r["winner"] is None  # decided by the audience vote


def test_votes_decide_audience_round(settings):
    with client(settings) as c:
        rid = c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "MX"}).json()["id"]
        r = c.post(f"/rounds/{rid}/votes", json={"david": 30, "goliath": 12}).json()
        assert r["winner"] == "david" and r["win_reason"] == "votes"
        sb = c.get("/scoreboard").json()
    assert sb["david"]["wins"] == 1 and sb["david"]["votes"] == 30


def test_evaluation_round_uses_reviewed_test_pair_and_chrf(settings):
    with client(settings) as c:
        r = c.post("/rounds/evaluation", json={}).json()
        assert r["round_type"] == "evaluation" and r["pair_id"] in {"p1", "p2"}  # p3 is pending review
        assert r["david"]["chrf"] is not None and r["winner"] in {"david", "goliath", "draw"}
        c.post("/rounds/evaluation", json={})
        # both approved pairs used: no more evaluation phrases
        assert c.post("/rounds/evaluation", json={}).status_code == 404


def test_offline_goliath_david_keeps_working_and_wins(settings):
    settings.force_offline = True
    with client(settings) as c:
        assert c.get("/health").json()["online"] is False
        r = c.post("/duel", json={"phrase": "x", "direction": "parent_to_genz", "country": "GT"}).json()
    assert r["goliath"]["status"] == "offline" and r["david"]["status"] == "ok"
    assert r["winner"] == "david" and r["win_reason"] == "goliath_offline"


def test_david_tag_override_is_recorded(settings):
    with client(settings) as c:
        r = c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "MX", "david_tag": "genlingo-2027-02"}).json()
    assert r["david"]["model"] == "genlingo-2027-02" and r["david_tag"] == "genlingo-2027-02"


def test_scoreboard_includes_training_cost_and_reset(settings):
    with client(settings) as c:
        c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "MX"})
        sb = c.get("/scoreboard").json()
        assert sb["rounds"] == 1 and sb["david_training"]["estimated_cost_usd"] == 0.42
        assert sb["goliath"]["cost_usd"] > 0
        c.post("/reset")
        assert c.get("/scoreboard").json()["rounds"] == 0


def test_bad_country_and_direction_rejected(settings):
    with client(settings) as c:
        assert c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "AR"}).status_code == 422
        assert c.post("/duel", json={"phrase": "x", "direction": "sideways", "country": "MX"}).status_code == 422


def test_rounds_are_numbered(settings):
    with client(settings) as c:
        a = c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "MX"}).json()
        b = c.post("/duel", json={"phrase": "y", "direction": "genz_to_parent", "country": "MX"}).json()
        assert (a["number"], b["number"]) == (1, 2)
        assert c.get("/rounds").json()[0]["number"] == 2


def test_live_votes_without_feed_returns_stored_tally(settings):
    with client(settings) as c:
        rid = c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "MX"}).json()["id"]
        c.post(f"/rounds/{rid}/votes", json={"david": 3, "goliath": 1})
        assert c.get(f"/rounds/{rid}/votes").json() == {"david": 3, "goliath": 1, "live": False}


def test_goliath_cost_uses_the_price_in_force_today(settings):
    from datetime import date

    settings.gemini_price_schedule = f"2020-01-01:1.0/10.0,{date.today().replace(year=date.today().year + 1)}:99/99"
    with client(settings) as c:
        r = c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "MX"}).json()
    assert r["goliath"]["price"] == {"input_per_million": 1.0, "output_per_million": 10.0, "effective_from": "2020-01-01"}
    assert r["david"]["price"]["input_per_million"] == 0


def test_david_gets_his_glossary_goliath_the_plain_v2_prompt(settings):
    import json as _json

    (settings.runs_dir / "genlingo-glossary.json").write_text(_json.dumps({"tag": "genlingo-glossary", "prompt_style": "v2+glossary"}))
    with client(settings) as c:
        r = c.post("/duel", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent", "country": "MX",
                                  "david_tag": "genlingo-glossary"}).json()
    assert r["david"]["extra"]["prompt"] == "translate-v2+glossary"
    assert "mid" in r["david"]["extra"]["glossary"]
    assert r["goliath"]["extra"] == {"prompt": "translate-v2", "glossary": [], "retrieval_ms": 0.0}


def test_last_months_david_keeps_his_old_prompt(settings):
    with client(settings) as c:
        r = c.post("/duel", json={"phrase": "x", "direction": "genz_to_parent", "country": "MX"}).json()
    assert r["david"]["extra"]["prompt"] == "translate-v1"


def test_quantized_exports_map_to_their_training_run(settings):
    with client(settings) as c:
        sb = c.get("/scoreboard", params={"david_tag": "genlingo-test-q5_k_m"}).json()
        assert sb["david_training"]["estimated_cost_usd"] == 0.42
        assert c.get("/scoreboard", params={"david_tag": "genlingo-test-f16"}).json()["david_training"]["duration_s"] == 900
