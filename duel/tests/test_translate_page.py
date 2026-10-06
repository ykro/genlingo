import json

from fastapi.testclient import TestClient

from genlingo_duel import dataset
from genlingo_duel.main import create_app
from genlingo_duel.settings import REPO_ROOT
from genlingo_duel.translate_page import examples_path


def test_page_is_served_and_needs_nothing_from_the_internet(settings):
    with TestClient(create_app(settings)) as c:
        res = c.get("/traducir")
    assert res.status_code == 200 and "Traducir" in res.text and "Gen Z → papás" in res.text
    assert "https://" not in res.text  # no fonts or scripts from a CDN: it must work offline


def test_translate_is_david_only_and_records_nothing(settings):
    settings.force_offline = True  # no internet: David still translates
    with TestClient(create_app(settings)) as c:
        res = c.post("/translate", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent"})
        assert res.status_code == 200
        body = res.json()
        assert body["text"] and body["latency_ms"] > 0 and body["model"] == "genlingo-test"
        assert "goliath" not in body
        assert c.get("/rounds").json() == []
        assert c.post("/translate", json={"phrase": "", "direction": "genz_to_parent"}).status_code == 422


def test_examples_come_from_the_data_file(settings):
    examples_path(settings.data_dir).write_text(json.dumps({"examples": [
        {"text": "qué chilero", "direction": "genz_to_parent", "david": "qué bonito", "source": "https://x", "license": "MIT"},
    ]}))
    with TestClient(create_app(settings)) as c:
        assert c.get("/translate/examples").json() == [{"text": "qué chilero", "direction": "genz_to_parent"}]


def test_stage_examples_are_guatemalan_test_pairs_with_source():
    data = REPO_ROOT / "data"
    examples = json.loads(examples_path(data).read_text(encoding="utf-8"))["examples"]
    pairs = {p.id: p for p in dataset.test_pairs(data)}
    assert {e["direction"] for e in examples} == {"genz_to_parent", "parent_to_genz"}
    for e in examples:
        p = pairs[e["pair_id"]]  # still in the test set: David never trained on it
        assert p.country == "GT" and p.direction == e["direction"] and p.source == e["text"]
        assert e["source"].startswith("https://") and e["license"] and e["david"]
