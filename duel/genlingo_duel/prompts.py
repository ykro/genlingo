"""Genlingo's translation prompt: the only prompt both David and Goliath ever see.

The same template renders the fine-tuning data (`scripts/build_train_set.py`), so David is
trained on exactly the format he is asked in on stage. `country` goes into the prompt because
"está bien chido" (MX) and "está bien chilero" (GT) are the same sentence in different places.
"""

from __future__ import annotations

from typing import Literal

from duel_core import Message, PromptTemplate

Direction = Literal["genz_to_parent", "parent_to_genz"]
DIRECTIONS: tuple[Direction, ...] = ("genz_to_parent", "parent_to_genz")

COUNTRIES = {
    "MX": "México",
    "GT": "Guatemala",
    "CO": "Colombia",
    "LATAM": "Latinoamérica (español neutro)",
}

GENZ = "la Generación Z (jóvenes de 16 a 24 años)"
PARENTS = "sus papás (adultos de 45 a 60 años)"

DIRECTION_TEXT: dict[Direction, tuple[str, str]] = {
    "genz_to_parent": (GENZ, PARENTS),
    "parent_to_genz": (PARENTS, GENZ),
}

TRANSLATE = PromptTemplate(
    version="translate-v1",
    system=(
        "Eres un traductor generacional del español de {country_name}. "
        "Reescribe la frase del habla de {source_gen} al habla de {target_gen}, "
        "conservando el significado, el tono y más o menos la misma longitud. "
        "Responde solo con la frase traducida, en una línea, sin comillas ni explicaciones."
    ),
    user="{phrase}",
)


def translation_messages(phrase: str, direction: Direction, country: str) -> list[Message]:
    if direction not in DIRECTION_TEXT:
        raise ValueError(f"dirección desconocida: {direction}")
    if country not in COUNTRIES:
        raise ValueError(f"país desconocido: {country}")
    source_gen, target_gen = DIRECTION_TEXT[direction]
    return TRANSLATE.render(
        country_name=COUNTRIES[country], source_gen=source_gen, target_gen=target_gen, phrase=phrase.strip()
    )
