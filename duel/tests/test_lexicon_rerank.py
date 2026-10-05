"""Lexicon glossary (country + counterparts), term-bank reranking and the meaning-aware metrics."""

import asyncio
import sys
from pathlib import Path

from duel_core import Completion
from genlingo_duel.glossary import Glossary, hashing_embedder, render
from genlingo_duel.rerank import NBestClient, term_bank_scorer
from genlingo_duel.terms import TermBank

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))
from term_accuracy import change_recall_synonyms, correct_slang  # noqa: E402

BANK = TermBank([
    {"id": "gt-g1", "term": "pisto", "meaning": "dinero", "generation": "genz", "country": "GT"},
    {"id": "gt-g2", "term": "chilero", "meaning": "bonito, agradable", "generation": "genz", "country": "GT"},
    {"id": "gt-p1", "term": "billete", "meaning": "dinero", "generation": "parent", "country": "GT"},
    {"id": "mx-g1", "term": "feria", "meaning": "dinero", "generation": "genz", "country": "MX"},
    {"id": "la-g1", "term": "cringe", "meaning": "vergüenza ajena", "generation": "genz", "country": "LATAM"},
])
CPS = {"gt-g1": "gt-p1", "gt-p1": "gt-g1", "gt-g2": None, "mx-g1": None, "la-g1": None}


def lex(phrase, direction="parent_to_genz", country="GT"):
    g = asyncio.run(Glossary(BANK, hashing_embedder(), counterparts=CPS).load())
    return asyncio.run(g.lex_entries(phrase, direction, country))


def test_lex_glossary_links_the_counterpart_and_marks_the_foreign_term():
    entries = lex("no traigo billete para la fiesta")
    link = next(e for e in entries if e["role"] == "link")
    assert link["term"] == "billete" and link["counterpart"]["term"] == "pisto"
    foreign = [e for e in entries if e["role"] == "foreign"]
    assert len(foreign) == 1 and foreign[0]["country"] == "MX"
    block = render(entries, "Guatemala")
    assert "«billete» (papás) = «pisto» (Gen Z)" in block and "NO de Guatemala" in block
    assert entries == lex("no traigo billete para la fiesta")  # same phrase, same order


def test_scorer_prefers_the_counterpart_and_punishes_foreign_slang():
    entries = lex("no traigo billete para la fiesta")
    score = term_bank_scorer(BANK, "no traigo billete para la fiesta", "parent_to_genz", "GT", entries)
    assert score("no traigo pisto para la fiesta") > score("no traigo dinero para la fiesta")
    assert score("no traigo feria para la fiesta") < score("no traigo dinero para la fiesta")


class Fixed:
    def __init__(self, texts):
        self.texts = list(texts)

    async def complete(self, messages, *, model):
        return Completion(text=self.texts.pop(0), model=model, latency_ms=100.0, input_tokens=10, output_tokens=5)


def test_nbest_keeps_the_best_scoring_candidate():
    entries = lex("no traigo billete")
    scorer = term_bank_scorer(BANK, "no traigo billete", "parent_to_genz", "GT", entries)
    client = NBestClient(Fixed(["no traigo dinero", "no traigo feria", "no traigo pisto"]), 3, scorer)
    c = asyncio.run(client.complete([], model="david"))
    assert c.text == "no traigo pisto" and c.output_tokens == 15 and len(client.last) == 3


def test_correct_slang_requires_the_same_meaning():
    p2g = {"source": "no traigo billete", "target": "no traigo pisto", "country": "GT", "direction": "parent_to_genz"}
    assert correct_slang(BANK, CPS, p2g, "no traigo pisto") is True
    assert correct_slang(BANK, CPS, p2g, "qué chilero, no traigo nada") is False  # Gen Z slang, wrong meaning
    g2p = {"source": "no traigo pisto", "target": "no traigo dinero", "country": "GT", "direction": "genz_to_parent"}
    assert correct_slang(BANK, CPS, g2p, "no traigo dinero") is True  # the meaning, in plain words
    assert correct_slang(BANK, CPS, g2p, "no traigo billete") is True  # the validated counterpart
    assert correct_slang(BANK, CPS, g2p, "no traigo nada") is False


def test_change_recall_with_synonyms_counts_stems_and_linked_terms():
    pair = {"source": "estuvo muy bonito", "target": "estuvo bien chilero", "country": "GT", "direction": "parent_to_genz"}
    assert change_recall_synonyms(BANK, CPS, pair, "estuvo bien chileros") == 1.0
    assert change_recall_synonyms(BANK, CPS, pair, "estuvo muy bonito") == 0.0
