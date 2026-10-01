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

# v2: the country comes first and is explicit (no slang from other countries), and an optional
# glossary from our term bank closes the system prompt.
TRANSLATE_V2 = PromptTemplate(
    version="translate-v2",
    system=(
        "Variante: español de {country_name}. Usa solo expresiones de {country_name}; "
        "no mezcles jerga de otros países.\n"
        "Reescribe la frase del habla de {source_gen} al habla de {target_gen}: cambia la jerga por "
        "su equivalente de la otra generación, conserva el significado, el tono y más o menos la "
        "misma longitud. Responde solo con la frase traducida, en una línea, sin comillas ni explicaciones."
        "{glossary}"
    ),
    user="{phrase}",
)

# Prompt styles: the duel uses, for each David tag, the style its training data was rendered
# with (train/runs/<tag>.json); base models and Goliath can use any of them.
STYLES = ("v1", "v2", "v2+glossary")


def translation_messages(
    phrase: str,
    direction: Direction,
    country: str,
    style: str = "v1",
    glossary: str = "",
) -> list[Message]:
    if direction not in DIRECTION_TEXT:
        raise ValueError(f"dirección desconocida: {direction}")
    if country not in COUNTRIES:
        raise ValueError(f"país desconocido: {country}")
    if style not in STYLES:
        raise ValueError(f"estilo de prompt desconocido: {style}")
    source_gen, target_gen = DIRECTION_TEXT[direction]
    fields = dict(country_name=COUNTRIES[country], source_gen=source_gen, target_gen=target_gen, phrase=phrase.strip())
    if style == "v1":
        return TRANSLATE.render(**fields)
    return TRANSLATE_V2.render(**fields, glossary=glossary if style == "v2+glossary" else "")


def prompt_version(style: str) -> str:
    return {"v1": TRANSLATE.version, "v2": TRANSLATE_V2.version, "v2+glossary": TRANSLATE_V2.version + "+glossary"}[style]
