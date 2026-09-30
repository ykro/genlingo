"""Schema and hygiene checks over the real data files in data/ (the dataset's contract)."""

import json
import re
from collections import Counter

import pytest

from _common import DATA
from generate_pairs import normalize
from genlingo_duel.dataset import load_pairs, read_jsonl

TERM_FIELDS = {"id", "term", "generation", "meaning", "country", "example", "example_origin", "source_id", "source_url"}
USAGE_FIELDS = {"id", "term_ids", "generation", "example", "rewrite", "country", "source_id", "source_url", "example_origin"}

needs = lambda rel: pytest.mark.skipif(not (DATA / rel).exists(), reason=f"{rel} not built yet")  # noqa: E731


def source_ids() -> set[str]:
    return set(re.findall(r"^\|\s*(S\d+)\s*\|", (DATA / "SOURCES.md").read_text(), flags=re.M))


@needs("terms.jsonl")
def test_term_bank_schema_and_sources():
    terms = list(read_jsonl(DATA / "terms.jsonl"))
    assert len(terms) >= 100
    ids = source_ids()
    for t in terms:
        assert TERM_FIELDS <= t.keys(), t
        assert t["generation"] in {"genz", "parent"} and t["country"] in {"MX", "GT", "CO", "LATAM"}
        assert t["source_id"] in ids, f"{t['id']} cites unknown source {t['source_id']}"
        assert t["source_url"].startswith("http")
    assert len({t["id"] for t in terms}) == len(terms)


@needs("raw/web_usage.jsonl")
def test_web_usage_schema_and_no_overlap_with_generator_examples():
    usage = list(read_jsonl(DATA / "raw" / "web_usage.jsonl"))
    term_ids = {t["id"] for t in read_jsonl(DATA / "terms.jsonl")}
    ids = source_ids()
    for u in usage:
        assert USAGE_FIELDS <= u.keys(), u
        assert set(u["term_ids"]) <= term_ids, u["id"]
        assert u["source_id"] in ids
    term_examples = {normalize(t["example"]) for t in read_jsonl(DATA / "terms.jsonl")}
    assert not term_examples & {normalize(u["example"]) for u in usage}


@needs("pairs/test_web.jsonl")
def test_all_pairs_valid_and_test_split_never_synthetic():
    pairs = load_pairs(DATA)  # raises on any schema/provenance violation
    assert len({p.id for p in pairs}) == len(pairs), "duplicate ids"
    assert not [p for p in pairs if p.split == "test" and p.origin == "synthetic"]


@needs("pairs/synthetic.jsonl")
def test_no_test_sentence_leaks_into_training():
    pairs = load_pairs(DATA)
    test_text = {normalize(x) for p in pairs if p.split == "test" for x in (p.source, p.target)}
    leaks = [p.id for p in pairs if p.split == "train" and (normalize(p.source) in test_text or normalize(p.target) in test_text)]
    assert not leaks, leaks[:5]


@needs("pairs/synthetic.jsonl")
def test_synthetic_is_balanced_by_direction_and_traceable():
    syn = [p for p in load_pairs(DATA) if p.origin == "synthetic"]
    c = Counter(p.direction for p in syn)
    assert abs(c["genz_to_parent"] - c["parent_to_genz"]) <= 0.05 * len(syn)
    meta = json.loads((DATA / "pairs" / "synthetic.meta.json").read_text())
    assert all(p.provenance["model"] == meta["model"] and "seed" in p.provenance for p in syn)
