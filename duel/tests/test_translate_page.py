import json

from fastapi.testclient import TestClient

from genlingo_duel import dataset
from genlingo_duel.main import create_app
from genlingo_duel.settings import REPO_ROOT
from genlingo_duel.term_check import term_checks
from genlingo_duel.terms import TermBank
from genlingo_duel.translate_page import examples_path


def _example_file(settings):
    examples_path(settings.data_dir).write_text(json.dumps({"examples": [
        {"pair_id": "e1", "text": "estuvo bien mid", "direction": "genz_to_parent", "reference": "estuvo regular",
         "source": "https://x", "license": "MIT", "david": "estuvo regular"},
    ]}))


def test_page_is_served_with_its_fonts_and_nothing_from_the_internet(settings):
    with TestClient(create_app(settings)) as c:
        page = c.get("/traducir")
        assert page.status_code == 200 and "Traducir" in page.text and "Goliath" in page.text
        assert "https://" not in page.text  # no CDN: it must work offline
        assert "prefers-color-scheme: dark" not in page.text  # light only
        assert c.get("/traducir/fonts/Figtree-latin.woff2").status_code == 200
        assert c.get("/traducir/fonts/../../.env").status_code == 404


def test_each_side_translates_on_its_own_and_nothing_is_recorded(settings):
    with TestClient(create_app(settings)) as c:
        d = c.post("/translate/david", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent"}).json()
        g = c.post("/translate/goliath", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent"}).json()
        assert d["status"] == g["status"] == "ok"
        assert d["model"] == "genlingo-test" and g["model"] == "goliath-model"
        assert d["cost_usd"] == 0 and g["cost_usd"] > 0 and d["latency_ms"] > 0
        assert "terms" not in d  # typed text: just the translations, time and cost
        assert c.get("/rounds").json() == []
        assert c.post("/translate/judge", json={"phrase": "x", "direction": "genz_to_parent"}).status_code == 422


def test_offline_goliath_says_so_and_david_still_translates(settings):
    settings.force_offline = True
    with TestClient(create_app(settings)) as c:
        g = c.post("/translate/goliath", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent"}).json()
        d = c.post("/translate/david", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent"}).json()
    assert g["status"] == "offline" and d["status"] == "ok" and d["text"]


def test_an_example_comes_back_with_the_term_check(settings):
    _example_file(settings)
    with TestClient(create_app(settings)) as c:
        ex = c.get("/translate/examples").json()
        assert ex == [{"id": "e1", "text": "estuvo bien mid", "direction": "genz_to_parent", "reference": "estuvo regular",
                       "source": "https://x", "license": "MIT", "slang": ["mid"]}]
        d = c.post("/translate/david", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent", "example_id": "e1"}).json()
        assert d["terms"] == [{"term": "mid", "expected": "regular, mediocre", "ok": True}]
        # the check belongs to the example's phrase: edited text gets no check
        edited = c.post("/translate/david", json={"phrase": "estuvo bien mid hoy", "direction": "genz_to_parent", "example_id": "e1"}).json()
        assert "terms" not in edited


def test_term_check_rules():
    bank = TermBank([
        {"id": "g1", "term": "chivas", "meaning": "cosas, pertenencias", "generation": "genz", "country": "GT"},
        {"id": "p1", "term": "refacción", "meaning": "merienda", "generation": "parent", "country": "GT"},
        {"id": "g2", "term": "refa", "meaning": "merienda", "generation": "genz", "country": "GT"},
    ])
    cps = {"p1": "g2"}
    check = lambda phrase, d, hyp: [t["ok"] for t in term_checks(bank, cps, phrase, d, "GT", hyp)]  # noqa: E731
    assert check("agarrá tus chivas", "genz_to_parent", "agarrá tus cosas") == [True]
    assert check("agarrá tus chivas", "genz_to_parent", "agarrá tus chivas") == [False]  # slang left in
    assert check("agarrá tus chivas", "genz_to_parent", "agarrá tus chunches") == [False]  # other slang
    assert check("algo de refacción", "parent_to_genz", "algo de refa") == [True]
    assert check("algo de refacción", "parent_to_genz", "unos munchies") == [False]


def test_stage_examples_are_guatemalan_test_pairs_with_source_and_live_record():
    data = REPO_ROOT / "data"
    examples = json.loads(examples_path(data).read_text(encoding="utf-8"))["examples"]
    pairs = {p.id: p for p in dataset.test_pairs(data)}
    assert {e["direction"] for e in examples} == {"genz_to_parent", "parent_to_genz"}
    for e in examples:
        p = pairs[e["pair_id"]]  # still in the test set: David never trained on it
        assert p.country == "GT" and p.direction == e["direction"] and p.source == e["text"] and p.target == e["reference"]
        assert e["source"].startswith("https://") and e["license"] and e["why"]
        assert len(e["live_runs"]) >= 3 and all(r["david"] == e["david"] for r in e["live_runs"])
