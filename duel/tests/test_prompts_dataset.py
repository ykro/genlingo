import pytest
from pydantic import ValidationError

from genlingo_duel.dataset import Pair
from genlingo_duel.prompts import translation_messages


def test_prompt_is_identical_shape_and_mentions_country_and_direction():
    m = translation_messages("está bien chilero", "genz_to_parent", "GT")
    assert m[0]["role"] == "system" and "Guatemala" in m[0]["content"]
    assert m[0]["content"].index("Generación Z") < m[0]["content"].index("papás")
    assert m[-1] == {"role": "user", "content": "está bien chilero"}
    back = translation_messages("qué bonito", "parent_to_genz", "GT")[0]["content"]
    assert back.index("papás") < back.index("Generación Z")


def test_synthetic_pairs_can_never_be_test(make_pair):
    with pytest.raises(ValidationError):
        Pair.model_validate(make_pair(1, split="test", origin="synthetic"))
    Pair.model_validate(make_pair(1, split="train", origin="synthetic"))


def test_web_pair_needs_url_and_license(make_pair):
    row = make_pair(1)
    row["provenance"] = {"url": "https://x"}
    with pytest.raises(ValidationError):
        Pair.model_validate(row)
