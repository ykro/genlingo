from term_accuracy import TermBank, change_recall, foreign_slang, normalize, slang_handled, variants

BANK = TermBank([
    {"id": "t1", "term": "güey / wey", "generation": "genz", "country": "MX"},
    {"id": "t2", "term": "¡no manches!", "generation": "genz", "country": "MX"},
    {"id": "t3", "term": "agüitarse", "generation": "genz", "country": "MX"},
    {"id": "t4", "term": "pisto", "generation": "genz", "country": "GT"},
    {"id": "t5", "term": "cringe / dar cringe", "generation": "genz", "country": "LATAM"},
    {"id": "t6", "term": "chido", "generation": "parent", "country": "MX"},
])


def pair(direction, source, target="x", country="MX"):
    return {"direction": direction, "source": source, "target": target, "country": country}


def test_variants_and_normalize():
    assert variants("güey / wey") == ["guey", "wey"]
    assert variants("¡no manches!") == ["no manches"]
    assert normalize("¡Qué ONDA, Güey!") == "que onda guey"


def test_matching_handles_inflections_and_conjugations():
    assert BANK.found("t1", "oye wey ven")
    assert BANK.found("t3", "me agüité todo el día")
    assert not BANK.found("t4", "pistola")  # whole words only


def test_genz_to_parent_slang_must_be_gone():
    p = pair("genz_to_parent", "no manches, güey")
    assert slang_handled(BANK, p, ["t1", "t2"], "no puede ser, amigo") is True
    assert slang_handled(BANK, p, ["t1", "t2"], "no manches, amigo") is False
    assert slang_handled(BANK, p, ["t1"], "no manches, güey") is False  # copying fails
    assert slang_handled(BANK, pair("genz_to_parent", "hola señor"), [], "x") is None  # nothing to judge


def test_parent_to_genz_needs_genz_slang_of_the_country():
    p = pair("parent_to_genz", "qué vergüenza")
    assert slang_handled(BANK, p, [], "qué cringe") is True  # LATAM counts
    assert slang_handled(BANK, p, [], "qué vergüenza") is False
    assert foreign_slang(BANK, p, "no tengo pisto") is True  # Guatemalan slang in a Mexican phrase
    assert foreign_slang(BANK, p, "no tengo pisto, güey") is False


def test_change_recall_only_counts_what_the_reference_changed():
    assert change_recall("la neta no tengo feria", "la verdad no tengo dinero", "la verdad no tengo dinero") == 1.0
    assert change_recall("la neta no tengo feria", "la verdad no tengo dinero", "la neta no tengo feria") == 0.0
    assert change_recall("hola", "hola", "hola") is None
