"""The term bank as code: find slang terms in a sentence, by country and generation.

Used by the data generator (to validate pairs), the glossary retrieval (David's prompt) and the
eval (term-level metrics). Matching is deterministic and forgiving with inflections:
"güey / wey" matches "wey", "agüitarse" matches "me agüité".
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

STOPWORDS = set(
    """a al algo como con de del el ella ellas ellos en es esa ese eso esta este esto ha hay la las le les lo los
    me mi mis muy no nos o para pero por que qué se si sí su sus te ti tu tú un una uno unos unas y ya yo
    estar está están estoy estaba fue ser soy son era tan más mas bien todo toda todos así aquí ahí""".split()
)
_SUFFIXES = ("", "s", "es", "a", "o", "as", "os", "ito", "ita", "itos", "itas")
_VERB_ENDINGS = ("arse", "erse", "irse", "ear", "ar", "er", "ir")


def normalize(text: str) -> str:
    text = text.lower().replace("ñ", "\u0001")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).replace("\u0001", "ñ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-zñ0-9 ]+", " ", text)).strip()


def variants(term: str) -> list[str]:
    """'güey / wey' -> ['guey', 'wey']; '¡no manches!' -> ['no manches']."""
    return [v for v in (normalize(part) for part in re.split(r"/|,", term)) if v and not v.endswith("...")]


def _pattern(variant: str) -> re.Pattern:
    words = variant.split()
    if len(words) == 1:
        w = words[0]
        stem = next((w[: -len(e)] for e in _VERB_ENDINGS if w.endswith(e) and len(w) - len(e) >= 4), None)
        if stem:  # verbs: any conjugation sharing the stem ("agüitarse" -> "agüitado", "agüite")
            return re.compile(rf"\b{re.escape(stem)}\w*")
        if len(w) >= 4:
            return re.compile(rf"\b{re.escape(w)}(?:{'|'.join(_SUFFIXES[1:])})?\b")
    return re.compile(rf"\b{re.escape(variant)}\b")


class TermBank:
    def __init__(self, terms: Iterable[dict], *, ignore_ambiguous: bool = False):
        """`ignore_ambiguous=True` skips terms flagged as ambiguous (they also mean something ordinary,
        e.g. "cámara", "servir", "alta"; see scripts/flag_ambiguous_terms.py). Metrics and test-set
        validation use it; the generator doesn't need it (it asks for the term explicitly)."""
        terms = list(terms)
        self.terms = {t["id"]: t for t in terms if not (ignore_ambiguous and t.get("ambiguous"))}
        self._patterns = {tid: [_pattern(v) for v in variants(t["term"])] for tid, t in self.terms.items()}

    def found(self, term_id: str, text: str) -> bool:
        norm = normalize(text)
        return any(p.search(norm) for p in self._patterns.get(term_id, []))

    def genz_terms(self, country: str) -> list[str]:
        return [tid for tid, t in self.terms.items() if t["generation"] == "genz" and t["country"] in (country, "LATAM")]

    def ids(self, generation: str | None = None, countries: Iterable[str] | None = None) -> list[str]:
        cs = set(countries) if countries is not None else None
        return [
            tid
            for tid, t in self.terms.items()
            if (generation is None or t["generation"] == generation) and (cs is None or t["country"] in cs)
        ]

    def found_in(self, text: str, term_ids: Iterable[str]) -> list[str]:
        return [t for t in term_ids if self.found(t, text)]

    def foreign_in(self, text: str, country: str) -> list[str]:
        """Terms of another country (LATAM is neutral: allowed everywhere; a LATAM phrase allows no country slang)."""
        allowed = {country, "LATAM"}
        # Ambiguous entries are ordinary words too ("cámara", "alta"): never evidence of foreign slang.
        return [t for t, v in self.terms.items() if v["country"] not in allowed and not v.get("ambiguous") and self.found(t, text)]
