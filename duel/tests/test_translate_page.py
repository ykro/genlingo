import dataclasses
import json

import httpx
from fastapi.testclient import TestClient

from genlingo_duel import dataset
from genlingo_duel.arena import Arena
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


def test_page_is_served_with_its_fonts_and_nothing_from_another_site(settings):
    with TestClient(create_app(settings)) as c:
        page = c.get("/")
        assert page.status_code == 200 and "Traducir" in page.text and "Goliath" in page.text
        assert "https://" not in page.text  # no CDN: fonts and code come from the page itself
        assert "prefers-color-scheme: dark" not in page.text  # light only
        assert "laptop" not in page.text and "Sin conexión" not in page.text  # David runs in the cloud now
        assert c.get("/fonts/Figtree-latin.woff2").status_code == 200
        assert c.get("/fonts/../../.env").status_code == 404


def test_each_side_translates_on_its_own_and_nothing_is_recorded(settings):
    with TestClient(create_app(settings)) as c:
        d = c.post("/api/translate/david", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent"}).json()
        g = c.post("/api/translate/goliath", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent"}).json()
        assert d["status"] == g["status"] == "ok"
        assert d["model"] == "genlingo-test" and g["model"] == "goliath-model"
        assert d["latency_ms"] > 0 and g["cost_usd"] > 0
        # David's cost is his GPU seconds: the translation's time × the service's rate per second
        assert d["cost_usd"] == round(d["latency_ms"] / 1000 * settings.david_usd_per_s, 7)
        # typed text is checked against the term bank alone ("mid" is in it)
        assert d["checked"] == "typed" and [t["term"] for t in d["terms"]] == ["mid"]
        assert c.post("/api/translate/judge", json={"phrase": "x", "direction": "genz_to_parent"}).status_code == 422
        # nothing else is exposed: no rounds, votes or scoreboard
        for path in ("/rounds", "/scoreboard", "/queue", "/duel", "/reset"):
            assert c.get(path).status_code in (404, 405)


def test_an_example_comes_back_with_the_term_check(settings):
    _example_file(settings)
    with TestClient(create_app(settings)) as c:
        ex = c.get("/api/examples").json()
        assert ex == [{"id": "e1", "text": "estuvo bien mid", "direction": "genz_to_parent", "reference": "estuvo regular",
                       "source": "https://x", "license": "MIT", "slang": ["mid"]}]
        d = c.post("/api/translate/david", json={"phrase": "estuvo bien mid", "direction": "genz_to_parent", "example_id": "e1"}).json()
        assert d["terms"] == [{"term": "mid", "expected": "regular, mediocre", "ok": True}]
        assert d["checked"] == "example"
        # the reference belongs to the example's phrase: edited text is checked like typed text
        edited = c.post("/api/translate/david", json={"phrase": "estuvo bien mid hoy", "direction": "genz_to_parent", "example_id": "e1"}).json()
        assert edited["checked"] == "typed"


def test_typed_text_without_known_slang_says_there_is_nothing_to_check(settings):
    with TestClient(create_app(settings)) as c:
        d = c.post("/api/translate/david", json={"phrase": "mañana voy al mercado", "direction": "genz_to_parent"}).json()
        assert d["status"] == "ok" and d["terms"] == [] and d["checked"] == "typed"
        st = c.get("/api/status").json()
        assert st["david_usd_per_hour"] == round(settings.david_usd_per_s * 3600, 2)
        assert st["goliath_usd_per_m"]["input"] > 0 and st["terms_in_bank"] > 0


class FakeDavid:
    """Stands in for David's Ollama: cold until warmed, counts the calls."""

    def __init__(self, fail=False):
        self.models: list[str] = []
        self.calls: list[str] = []
        self.fail = fail

    async def loaded_models(self, timeout_s=10.0):
        self.calls.append("ps")
        if self.fail:
            raise RuntimeError("instance did not start")
        return list(self.models)

    async def warm_up(self, model, timeout_s=600.0):
        self.calls.append(f"load {model}")
        self.models.append(model)

    async def warm_up_embedding(self, model, timeout_s=600.0):
        self.calls.append(f"load {model}")
        self.models.append(model)

    async def complete(self, messages, *, model):
        from duel_core import Completion

        self.calls.append(f"translate {model}")
        return Completion(text="estuvo regular", model=model, latency_ms=400)


def _cloud_app(settings, fake):
    settings.mock_ai = False
    settings.embedding_model = "emb"
    arena = Arena.from_settings(dataclasses.replace(settings, mock_ai=True))
    arena.settings = settings
    arena.david_client = fake
    arena.glossary = object()  # already loaded
    return create_app(settings, arena)


def test_opening_the_page_wakes_david_once_and_reports_when_he_is_ready(settings):
    fake = FakeDavid()
    with TestClient(_cloud_app(settings, fake)) as c:
        assert c.get("/api/status").json()["david"]["phase"] == "idle"
        assert c.post("/api/david/wake").json()["phase"] == "ready"
        # load both models, then throwaway translations until three in a row are fast (here: the first three)
        assert fake.calls == ["ps", "load genlingo-test", "load emb"] + ["translate genlingo-test"] * 3
        # while the page stays open, its pings only check that he is still loaded
        assert c.post("/api/david/wake").json()["phase"] == "ready"
        assert fake.calls[-1] == "ps" and fake.calls.count("load genlingo-test") == 1


def test_david_is_ready_only_once_he_answers_fast(settings):
    from genlingo_duel import main

    fake = FakeDavid()
    latencies = iter([4000, 300, 5000, 400, 450, 380])

    async def complete(messages, *, model):
        from duel_core import Completion

        fake.calls.append("translate")
        return Completion(text="estuvo regular", model=model, latency_ms=next(latencies))

    fake.complete = complete
    with TestClient(_cloud_app(settings, fake)) as c:
        assert c.post("/api/david/wake").json()["phase"] == "ready"
    assert fake.calls.count("translate") == 6 and main.FAST_IN_A_ROW == 3


def test_a_failed_wake_up_says_so_and_the_next_call_retries(settings):
    fake = FakeDavid(fail=True)
    with TestClient(_cloud_app(settings, fake)) as c:
        st = c.post("/api/david/wake").json()
        assert st["phase"] == "error" and "did not start" in st["error"]
        fake.fail = False
        assert c.post("/api/david/wake").json()["phase"] == "ready"


def test_david_is_assumed_cold_after_cloud_run_would_have_stopped_him(settings, monkeypatch):
    from genlingo_duel import main

    fake = FakeDavid()
    with TestClient(_cloud_app(settings, fake)) as c:
        c.post("/api/david/wake")
        c.app.state.david.last_seen -= main.IDLE_COLD_S + 1
        assert c.get("/api/status").json()["david"]["phase"] == "idle"


def test_https_david_url_gets_an_id_token(monkeypatch):
    from genlingo_duel import arena as arena_mod, cloud_auth

    monkeypatch.setattr(cloud_auth, "_fetch", lambda audience: f"token-for-{audience}")
    client = arena_mod.david_client_for("https://genlingo-david-x.run.app/")
    req = httpx.Request("GET", "https://genlingo-david-x.run.app/api/ps")
    flow = client._http.auth.auth_flow(req)
    assert next(flow).headers["Authorization"] == "Bearer token-for-https://genlingo-david-x.run.app"
    assert arena_mod.david_client_for("http://127.0.0.1:11434")._http.auth is None


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


def test_page_examples_are_guatemalan_test_pairs_that_david_gets_right_and_goliath_does_not():
    data = REPO_ROOT / "data"
    examples = json.loads(examples_path(data).read_text(encoding="utf-8"))["examples"]
    pairs = {p.id: p for p in dataset.test_pairs(data)}
    bank = TermBank(dataset.read_jsonl(data / "eval" / "terms_test.jsonl"), ignore_ambiguous=True)
    from genlingo_duel.glossary import load_counterparts

    cps = load_counterparts(data / "counterparts.jsonl")
    assert {e["direction"] for e in examples} == {"genz_to_parent", "parent_to_genz"}
    for e in examples:
        p = pairs[e["pair_id"]]  # still in the test set: David never trained on it
        assert p.country == "GT" and p.direction == e["direction"] and p.source == e["text"] and p.target == e["reference"]
        assert e["source"].startswith("https://") and e["license"] and e["why"]
        assert len(e["live_runs"]) >= 3
        for run in e["live_runs"]:
            check = lambda hyp: [t["ok"] for t in term_checks(bank, cps, e["text"], e["direction"], "GT", hyp, e["reference"])]  # noqa: E731
            assert check(run["david"]) and all(check(run["david"])), run
            assert run["goliath"] is None or not all(check(run["goliath"])), run


def test_a_visitor_over_the_per_minute_limit_gets_a_plain_message(settings):
    settings.limit_translate_per_min = 4
    with TestClient(create_app(settings)) as c:
        body = {"phrase": "estuvo bien mid", "direction": "genz_to_parent"}
        ok = [c.post("/api/translate/david", json=body, headers={"x-forwarded-for": "1.1.1.1"}).status_code for _ in range(4)]
        over = c.post("/api/translate/david", json=body, headers={"x-forwarded-for": "1.1.1.1"})
        assert ok == [200] * 4 and over.status_code == 429 and "Espera un minuto" in over.json()["detail"]
        # another visitor is not affected
        assert c.post("/api/translate/david", json=body, headers={"x-forwarded-for": "2.2.2.2"}).status_code == 200


def test_the_daily_gemini_cap_stops_goliath_only(settings):
    settings.limit_gemini_per_day = 2
    with TestClient(create_app(settings)) as c:
        body = {"phrase": "estuvo bien mid", "direction": "genz_to_parent"}
        assert [c.post("/api/translate/goliath", json=body).status_code for _ in range(2)] == [200, 200]
        over = c.post("/api/translate/goliath", json=body)
        assert over.status_code == 429 and "límite diario" in over.json()["detail"]
        assert c.post("/api/translate/david", json=body).status_code == 200


def test_the_daily_cap_counts_starts_of_david_not_keep_alive_pings():
    from genlingo_duel.limits import Limits
    lim = Limits(wakes_per_day=1)
    lim.count_daily("wake")
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        lim.count_daily("wake")
    assert e.value.status_code == 429 and "encendidos de David" in e.value.detail
