from genlingo_duel.overlap import TextIndex, norm


def test_norm_strips_case_accents_and_punctuation():
    assert norm("¿En serio? Qué MAMERA, parce.") == "en serio que mamera parce"


def test_exact_and_normalized_match():
    idx = TextIndex(["Qué mamera, parce."])
    assert idx.overlaps("que mamera parce")
    assert not idx.overlaps("qué chimba, parce")


def test_test_sentence_quoted_inside_a_longer_training_sentence():
    # a training dialogue that quotes a test sentence
    idx = TextIndex(["-Dale, vamos. Mi primo dijo que tampoco iba al partido. -¿En serio? Qué mamera, parce."])
    assert idx.overlaps("¿En serio? Qué mamera, parce.")


def test_training_sentence_inside_the_test_sentence_and_normalized_substring():
    # a training sentence that contains the test sentence with different punctuation
    idx = TextIndex(["Llega a las cuatro sin avisar, ¿y cree que la casa es un hotel?"])
    assert idx.overlaps("¿Y cree que la casa es un hotel?")
    assert TextIndex(["y cree que la casa es un hotel"]).overlaps("Oiga, ¿y cree que la casa es un hotel o qué?")


def test_short_phrases_need_an_exact_match():
    idx = TextIndex(["¿En serio? No te creo nada, mae."])
    assert not idx.overlaps("¿En serio?")
    assert TextIndex(["¿En serio?"]).overlaps("en serio")
    assert not TextIndex(["¿En serio?"]).overlaps("¿En serio? Qué mamera, parce.")


def test_word_boundaries():
    idx = TextIndex(["la fiesta estuvo bien chida anoche"])
    assert not idx.overlaps("fiesta estuvo bien chidaa")
