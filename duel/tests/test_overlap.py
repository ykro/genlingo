from genlingo_duel.overlap import TextIndex, norm


def test_norm_strips_case_accents_and_punctuation():
    assert norm("¿En serio? Qué CHURRETA, parce.") == "en serio que churreta parce"


def test_exact_and_normalized_match():
    idx = TextIndex(["Qué churreta, parce."])
    assert idx.overlaps("que churreta parce")
    assert not idx.overlaps("qué chimba, parce")


def test_test_sentence_quoted_inside_a_longer_training_sentence():
    # real-w2-0169-f quoted test-w-0099 inside a dialogue
    idx = TextIndex(["-Dale, vamos. Mi primo dijo que tampoco iba al partido. -¿En serio? Qué churreta, parce."])
    assert idx.overlaps("¿En serio? Qué churreta, parce.")


def test_training_sentence_inside_the_test_sentence_and_normalized_substring():
    # syn-0612d72dba contained the test source with different punctuation
    idx = TextIndex(["Vuelve a las cuatro sin llamar, ¿usted qué cree, que esto es un hotel?"])
    assert idx.overlaps("Usted qué cree ¿que esto es un hotel?")
    assert TextIndex(["usted qué cree que esto es un hotel"]).overlaps("Oiga, ¿usted qué cree que esto es un hotel o qué?")


def test_short_phrases_need_an_exact_match():
    idx = TextIndex(["¿En serio? No te creo nada, mae."])
    assert not idx.overlaps("¿En serio?")
    assert TextIndex(["¿En serio?"]).overlaps("en serio")
    assert not TextIndex(["¿En serio?"]).overlaps("¿En serio? Qué churreta, parce.")


def test_word_boundaries():
    idx = TextIndex(["la fiesta estuvo bien chida anoche"])
    assert not idx.overlaps("fiesta estuvo bien chidaa")
