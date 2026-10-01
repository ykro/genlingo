from build_test_set import build, source_licenses
from generate_pairs import expected_terms, filter_pairs, mock_generate, plan_calls, render, to_pairs, validate
from genlingo_duel.terms import TermBank

BANK = TermBank([
    {"id": "mx-g1", "term": "feria", "meaning": "dinero", "generation": "genz", "country": "MX"},
    {"id": "mx-g2", "term": "chido", "meaning": "bueno", "generation": "genz", "country": "MX"},
    {"id": "mx-p1", "term": "lana", "meaning": "dinero", "generation": "parent", "country": "MX"},
    {"id": "gt-g1", "term": "pisto", "meaning": "dinero", "generation": "genz", "country": "GT"},
    {"id": "gt-p1", "term": "billete", "meaning": "dinero", "generation": "parent", "country": "GT"},
    {"id": "co-g1", "term": "luca", "meaning": "mil pesos, dinero", "generation": "genz", "country": "CO"},
    {"id": "co-p1", "term": "plata", "meaning": "dinero", "generation": "parent", "country": "CO"},
    {"id": "la-g1", "term": "cringe", "meaning": "vergüenza ajena", "generation": "genz", "country": "LATAM"},
    {"id": "la-p1", "term": "qué pena", "meaning": "vergüenza", "generation": "parent", "country": "LATAM"},
])
VEC = {tid: [1.0, float(i % 3)] for i, tid in enumerate(BANK.terms)}


def call(kind, country="MX", anchor="mx-g1", counterpart="mx-p1", trap=None, direction=None):
    d = direction or ("parent_to_genz" if kind.startswith("p2g") else "genz_to_parent")
    return {"i": 0, "kind": kind, "country": country, "direction": d, "anchor": anchor, "counterpart": counterpart, "trap": trap, "seed": 7}


def pair(c, source, target):
    return {"direction": c["direction"], "source": source, "target": target, "country": c["country"]}


def test_plan_leans_to_parent_to_genz_and_stays_in_country():
    calls = plan_calls(BANK, VEC, 400, seed=3)
    p2g = sum(c["direction"] == "parent_to_genz" for c in calls)
    assert 0.55 <= p2g / len(calls) <= 0.65
    for c in calls:
        assert BANK.terms[c["anchor"]]["country"] in (c["country"], "LATAM")
        if c["counterpart"]:
            assert BANK.terms[c["counterpart"]]["country"] in (c["country"], "LATAM")
        if c["trap"]:
            assert BANK.terms[c["trap"]]["country"] not in (c["country"], "LATAM")
    assert len({c["seed"] for c in calls}) == len(calls)


def test_render_names_term_counterpart_and_trap():
    c = call("p2g_trap", trap="gt-g1")
    system, user = render(BANK, c)
    assert "México" in system and "«feria»" in user and "«pisto»" in user and "Guatemala" in user


def test_validate_requires_the_substitution():
    c = call("p2g_genz")
    assert validate(BANK, c, pair(c, "no traigo dinero", "no traigo feria")) is None
    assert validate(BANK, c, pair(c, "no traigo dinero", "no traigo nada, qué cringe")) == "target_missing_term"
    assert validate(BANK, c, pair(c, "no traigo dinero", "no traigo feria ni pisto")) == "foreign_term"
    assert validate(BANK, c, pair(c, "no traigo feria", "no traigo feria, chido")) == "genz_slang_in_source"


def test_validate_genz_to_parent_removes_slang():
    c = call("g2p_genz")
    assert validate(BANK, c, pair(c, "no traigo feria", "no traigo dinero")) is None
    assert validate(BANK, c, pair(c, "no traigo feria", "no traigo feria, hijo")) == "slang_left_in_target"
    assert validate(BANK, c, pair(c, "no traigo dinero", "no traigo dinero, hijo")) == "source_missing_term"
    c2 = call("g2p_parent", anchor="mx-p1", counterpart="mx-g1")
    assert expected_terms(c2) == ("mx-g1", "mx-p1")
    assert validate(BANK, c2, pair(c2, "no traigo feria", "no traigo lana")) is None


def test_filter_counts_reasons_and_mock_pairs_validate():
    calls = plan_calls(BANK, VEC, 40, seed=1)
    pairs = [p for c in calls for p in to_pairs(c, mock_generate(BANK, c), "mock")]
    kept, dropped = filter_pairs(BANK, {c["seed"]: c for c in calls}, pairs, set())
    assert kept and all(p["provenance"]["prompt_version"] == "pairs-v3" for p in kept)
    assert all(isinstance(v, int) for v in dropped.values())


def test_test_set_builder_maps_direction_license_and_keeps_review():
    md = "| id | url | owner | license |\n|---|---|---|---|\n| S01 | https://x | Wikcionario | CC BY-SA 4.0 |\n"
    lic = source_licenses(md)
    usage = [
        {"id": "w-1", "term_ids": ["t"], "generation": "genz", "example": "está bien mid", "rewrite": "está regular",
         "country": "MX", "source_id": "S01", "source_url": "https://x", "example_origin": "source"},
        {"id": "w-2", "term_ids": ["t"], "generation": "parent", "example": "qué chévere", "rewrite": "qué bacano, parce",
         "country": "CO", "source_id": "S01", "source_url": "https://x", "example_origin": "source"},
    ]
    previous = {"test-w-1": {"status": "approved", "target": "estuvo más o menos"}}
    pairs = build(usage, lic, previous)
    assert pairs[0]["direction"] == "genz_to_parent" and pairs[1]["direction"] == "parent_to_genz"
    assert pairs[0]["status"] == "approved" and pairs[0]["target"] == "estuvo más o menos"
    assert pairs[1]["status"] == "pending_review" and pairs[1]["provenance"]["license"] == "CC BY-SA 4.0"
