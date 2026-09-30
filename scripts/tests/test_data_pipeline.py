from build_test_set import build, source_licenses
from generate_pairs import balance, filter_pairs, mock_generate, normalize, plan_calls, to_pairs

TERMS = [
    {"id": f"t-{c.lower()}-{i}", "term": f"term{i}", "generation": "genz" if i % 3 else "parent", "meaning": "algo",
     "country": c, "example": f"ejemplo {i}", "source_id": "S01", "source_url": "https://x"}
    for c in ("MX", "GT", "CO", "LATAM") for i in range(5)
]


def test_plan_is_balanced_by_direction_and_country():
    calls = plan_calls(TERMS, 200, seed=7)
    assert len(calls) == 40
    dirs = [c["direction"] for c in calls]
    assert dirs.count("genz_to_parent") == dirs.count("parent_to_genz")
    countries = [c["term"]["country"] for c in calls]
    assert {countries.count(c) for c in ("MX", "GT", "CO", "LATAM")} == {10}
    assert len({c["seed"] for c in calls}) == len(calls)  # one seed per call, recorded per pair


def test_filter_drops_duplicates_leaks_and_identical():
    calls = plan_calls(TERMS, 20, seed=1)
    pairs = [p for c in calls for p in to_pairs(c, mock_generate(c), "mock")]
    pairs.append(dict(pairs[0], id="dup"))
    pairs.append(dict(pairs[1], id="same", target=pairs[1]["source"]))
    forbidden = {normalize(pairs[2]["source"])}
    kept, dropped = filter_pairs(pairs, forbidden)
    assert dropped["duplicate"] >= 1 and dropped["leak"] == 1
    assert dropped["identical"] + dropped["schema"] == 1  # exact copies fail the schema itself
    assert all(p["provenance"]["prompt_version"] and p["split"] == "train" for p in kept)
    bal = balance(kept, 10)
    assert sum(p["direction"] == "genz_to_parent" for p in bal) == sum(p["direction"] == "parent_to_genz" for p in bal)


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
    assert all(p["origin"] == "web" and p["split"] == "test" for p in pairs)
