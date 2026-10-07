"""The combinations niche (evals/niche.md, amendment 2): its rule, and that its sentences never reach training."""

import sys

import pytest

from _common import DATA, ROOT
from genlingo_duel.terms import TermBank

sys.path.insert(0, str(ROOT / "evals"))
from combos import distinct_terms, is_combo  # noqa: E402

BANK = TermBank([
    {"id": "g1", "term": "chido", "meaning": "bueno", "generation": "genz", "country": "MX"},
    {"id": "g2", "term": "bien chido", "meaning": "muy bueno", "generation": "genz", "country": "MX"},
    {"id": "g3", "term": "güey / wey", "meaning": "amigo", "generation": "genz", "country": "MX"},
    {"id": "g4", "term": "cringe", "meaning": "vergüenza ajena", "generation": "genz", "country": "LATAM"},
    {"id": "g5", "term": "pisto", "meaning": "dinero", "generation": "genz", "country": "GT"},
])


def test_nested_terms_count_once_and_other_countries_do_not_count():
    assert distinct_terms(BANK, "está bien chido", "MX") == ["g2"]
    assert sorted(distinct_terms(BANK, "wey, está bien chido y qué cringe", "MX")) == ["g2", "g3", "g4"]
    assert distinct_terms(BANK, "wey, no tengo pisto", "MX") == ["g3"]


def test_the_gen_z_side_decides_in_both_directions():
    g2p = {"direction": "genz_to_parent", "source": "wey, qué cringe", "target": "amigo, qué pena", "country": "MX"}
    p2g = {"direction": "parent_to_genz", "source": "amigo, qué pena", "target": "wey, qué cringe", "country": "MX"}
    assert is_combo(BANK, g2p) and is_combo(BANK, p2g)
    assert not is_combo(BANK, {**g2p, "source": "qué cringe"})


@pytest.mark.skipif(not (DATA / ".private" / "eval" / "combos.jsonl").exists(), reason="no niche file (make data-pull)")
def test_niche_is_real_and_never_in_training_or_dev():
    from genlingo_duel.dataset import PAIR_FILES, load_pairs, read_jsonl
    from genlingo_duel.overlap import TextIndex

    niche = [r for r in read_jsonl(DATA / "eval" / "combos.jsonl") if r["status"] == "auto_validated"]
    assert niche and all(r["origin"] == "web" and r["split"] == "test" for r in niche)
    rels = [r for k, r in PAIR_FILES.items() if k != "test_web"]
    seen = TextIndex(x for p in load_pairs(DATA, rels) for x in (p.source, p.target))
    leaks = [r["id"] for r in niche if seen.overlaps(r["source"]) or seen.overlaps(r["target"])]
    assert not leaks, leaks[:5]
