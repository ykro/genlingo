"""The ✓/✗ per slang term is the same rule on the page and in the eval, and it is strict about country.

- Gen Z → papás: the slang is gone AND its place is taken by the plain meaning, not by other slang.
  A Mexican "un chingo de chamba" answered "un friego de trabajo" is ✗ for "un chingo": "friego" is slang
  too, and the word that carries the meaning ("trabajo") belongs to "chamba", not to "un chingo".
- papás → Gen Z: the output uses slang valid for the example's country (the bank term or a
  meaning-validated counterpart of that country, or pan-Hispanic slang); the same meaning in another
  country's slang ("maje", Guatemala, in a Mexican sentence) is ✗.
"""

import sys
from pathlib import Path

import pytest

from genlingo_duel.term_check import term_checks
from genlingo_duel.terms import TermBank

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))
from term_accuracy import correct_slang  # noqa: E402

BANK = TermBank([
    {"id": "mx-chingo", "term": "un chingo", "meaning": "mucho, gran cantidad (vulgar leve)", "generation": "genz", "country": "MX"},
    {"id": "mx-chamba", "term": "chamba / chambear", "meaning": "trabajo; trabajar", "generation": "genz", "country": "MX"},
    {"id": "mx-hueso", "term": "hueso", "meaning": "trabajo, empleo", "generation": "parent", "country": "MX"},
    {"id": "mx-chido", "term": "chido", "meaning": "bonito, padre, agradable", "generation": "genz", "country": "MX"},
    {"id": "mx-guey", "term": "güey / wey", "meaning": "amigo, compa", "generation": "genz", "country": "MX"},
    {"id": "mx-compa", "term": "compa", "meaning": "amigo, compañero", "generation": "genz", "country": "MX"},
    {"id": "mx-oso", "term": "qué oso", "meaning": "qué vergüenza", "generation": "genz", "country": "MX"},
    {"id": "gt-maje", "term": "maje", "meaning": "amigo, cuate", "generation": "genz", "country": "GT"},
    {"id": "gt-chilero", "term": "chilero", "meaning": "bonito, agradable", "generation": "genz", "country": "GT"},
    {"id": "la-cuate", "term": "cuate", "meaning": "amigo", "generation": "parent", "country": "LATAM"},
    {"id": "la-titipuchal", "term": "un titipuchal", "meaning": "muchísimo", "generation": "parent", "country": "LATAM"},
    {"id": "la-pena", "term": "pena ajena", "meaning": "vergüenza por otro", "generation": "parent", "country": "LATAM"},
    {"id": "la-cringe", "term": "cringe", "meaning": "vergüenza ajena", "generation": "genz", "country": "LATAM"},
])
# Meaning-validated counterparts (data/counterparts.jsonl): Gen Z term -> parents' term and back.
CPS = {
    "mx-chamba": "mx-hueso", "mx-hueso": "mx-chamba",
    "mx-guey": "la-cuate", "mx-compa": "la-cuate", "gt-maje": "la-cuate", "la-cuate": "mx-guey",
    "la-pena": "la-cringe", "la-cringe": "la-pena", "mx-oso": "la-pena",
    "mx-chingo": None, "mx-chido": None, "gt-chilero": None, "la-titipuchal": None,
}


def page(phrase, direction, hyp, country="MX", reference=None):
    """{term: ok} as the page shows it."""
    return {t["term"]: t["ok"] for t in term_checks(BANK, CPS, phrase, direction, country, hyp, reference)}


def evals(phrase, direction, hyp, country="MX", reference=None):
    pair = {"source": phrase, "target": reference or "", "direction": direction, "country": country}
    return correct_slang(BANK, CPS, pair, hyp)


CHINGO = ("Tengo un chingo de chamba y no salgo hasta las nueve.", "genz_to_parent")
CHINGO_REF = "Tengo muchísimo trabajo y no salgo hasta las nueve."


def test_mx_chingo_answered_with_other_slang_is_wrong_even_if_the_sentence_has_the_right_words():
    hyp = "Tengo un friego de trabajo y no salgo hasta las nueve."
    # "trabajo" is chamba's meaning, not chingo's: it can't vouch for the word that replaced "un chingo".
    assert page(*CHINGO, hyp, reference=CHINGO_REF) == {"un chingo": False, "chamba": True}
    assert page(*CHINGO, hyp) == {"un chingo": False, "chamba": True}
    assert evals(*CHINGO, hyp, reference=CHINGO_REF) is False


@pytest.mark.parametrize("hyp", [
    "Tengo mucho trabajo y no salgo hasta las nueve.",
    "Tengo muchísimo trabajo y no salgo hasta las nueve.",  # a superlative of the meaning still counts
    "Tengo mucho hueso y no salgo hasta las nueve.",  # "hueso": the parents' counterpart of "chamba"
])
def test_mx_chingo_answered_with_the_plain_meaning_is_right(hyp):
    assert all(page(*CHINGO, hyp, reference=CHINGO_REF).values())
    assert evals(*CHINGO, hyp, reference=CHINGO_REF) is True


def test_a_parents_expression_with_the_same_meaning_takes_the_place_of_the_slang():
    phrase = "Había un chingo de personas."
    assert page(phrase, "genz_to_parent", "Había un titipuchal de gente.") == {"un chingo": True}


def test_slang_from_the_bank_in_the_place_of_the_term_is_wrong_even_next_to_the_meaning():
    phrase = "El concierto estuvo bien chido."
    assert page(phrase, "genz_to_parent", "El concierto estuvo muy bonito.") == {"chido": True}
    assert page(phrase, "genz_to_parent", "El concierto estuvo bonito y chilero.") == {"chido": False}  # Guatemalan slang
    assert evals(phrase, "genz_to_parent", "El concierto estuvo bonito y chilero.") is False


def test_slang_left_in_is_still_wrong():
    assert page(*CHINGO, "Tengo un chingo de trabajo.") == {"un chingo": False, "chamba": True}


CUATE = ("Salí con mi cuate al cine.", "parent_to_genz")


def test_same_country_synonym_is_right_in_parents_to_gen_z():
    assert page(*CUATE, "Salí con mi güey al cine.") == {"cuate": True}
    assert page(*CUATE, "Salí con mi compa al cine.") == {"cuate": True}  # another Mexican term, same counterpart
    assert evals(*CUATE, "Salí con mi compa al cine.", reference="Salí con mi güey al cine.") is True


def test_cross_country_slang_with_the_same_meaning_is_wrong_in_parents_to_gen_z():
    assert page(*CUATE, "Salí con mi maje al cine.") == {"cuate": False}  # Guatemalan, in a Mexican sentence
    assert evals(*CUATE, "Salí con mi maje al cine.", reference="Salí con mi güey al cine.") is False
    assert page(*CUATE, "Salí con mi güey, maje, al cine.") == {"cuate": False}  # mixed answer
    assert page(*CUATE, "Salí con mi maje al cine.", country="GT") == {"cuate": True}


def test_neutral_spanish_takes_only_pan_hispanic_slang():
    phrase = ("Ese video me dio pena ajena.", "parent_to_genz")
    assert page(*phrase, "Ese video me dio cringe.", country="LATAM") == {"pena ajena": True}
    assert page(*phrase, "Ese video, qué oso.", country="LATAM") == {"pena ajena": False}  # Mexican slang
    assert page(*phrase, "Ese video, qué oso.", country="MX") == {"pena ajena": True}
    assert page(*phrase, "Ese video me dio cringe.", country="MX") == {"pena ajena": True}  # pan-Hispanic is fine


def test_a_parents_word_the_reference_kept_is_not_required_to_change():
    phrase = ("Mi cuate tiene mucho hueso.", "parent_to_genz")
    ref = "Mi cuate tiene un chingo de chamba."
    assert page(*phrase, "Mi cuate tiene un chingo de chamba.", reference=ref) == {"hueso": True}
    assert evals(*phrase, "Mi cuate tiene un chingo de chamba.", reference=ref) is True


@pytest.mark.parametrize("phrase,direction,hyp,ref", [
    (*CHINGO, "Tengo un friego de trabajo y no salgo hasta las nueve.", CHINGO_REF),
    (*CHINGO, "Tengo mucho trabajo y no salgo hasta las nueve.", CHINGO_REF),
    (*CUATE, "Salí con mi maje al cine.", "Salí con mi güey al cine."),
    (*CUATE, "Salí con mi compa al cine.", "Salí con mi güey al cine."),
])
def test_the_eval_and_the_page_agree(phrase, direction, hyp, ref):
    checks = term_checks(BANK, CPS, phrase, direction, "MX", hyp, ref)
    assert evals(phrase, direction, hyp, reference=ref) is all(t["ok"] for t in checks)


def test_a_reordered_translation_keeps_its_meaning():
    bank = TermBank([{"id": "gt-paja", "term": "paja / pajas", "meaning": "mentira(s)", "generation": "genz", "country": "GT"}])
    checks = term_checks(bank, {}, "No le creas, todo lo que dice es paja.", "genz_to_parent", "GT",
                         "No le creás, puras mentiras son las que habla.")
    assert [t["ok"] for t in checks] == [True]


def test_in_parents_to_gen_z_the_slang_the_human_put_in_that_place_counts():
    bank = TermBank([*BANK.terms.values(),
                     {"id": "mx-canijo", "term": "canijo", "meaning": "difícil; travieso", "generation": "parent", "country": "MX"}])
    ref = "Pero a ese güey lo amo, neta."
    assert page_with(bank, "Pero a ese canijo lo amo.", "parent_to_genz", "Pero a ese wey lo amo.", reference=ref) == {"canijo": True}
    assert page_with(bank, "Pero a ese canijo lo amo.", "parent_to_genz", "Pero a ese maje lo amo.", reference=ref) == {"canijo": False}


def page_with(bank, phrase, direction, hyp, country="MX", reference=None):
    return {t["term"]: t["ok"] for t in term_checks(bank, CPS, phrase, direction, country, hyp, reference)}
