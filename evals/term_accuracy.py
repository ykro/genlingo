"""Term-level metrics: did the model actually translate the slang?

chrF++ against one reference rewards surface overlap: returning the phrase untouched already
scores ~50 on our test set, because a register rewrite keeps most words. These two metrics look
only at what has to change, so copying the source scores (close to) zero on both:

1. **Jerga resuelta** (slang handled), checked against the term bank (data/terms.jsonl):
   - Gen Z -> papás: none of the Gen Z terms found in the source is left in the output.
   - papás -> Gen Z: the output uses at least one Gen Z term of the bank (pair's country or LATAM).
   It checks that the register moved, not that the meaning is right.
2. **Cambios acertados** (reference-change recall): of the content words the human reference
   introduced (words in the reference but not in the source, e.g. "neta" -> "verdad"), the share
   that also appear in the output. It does check meaning, but only exact words: a valid synonym
   ("en serio" for "de veras") counts as a miss for every model alike.

Both are deterministic: no model (and in particular not Gemini) judges Gemini.
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
    def __init__(self, terms: Iterable[dict]):
        self.terms = {t["id"]: t for t in terms}
        self._patterns = {tid: [_pattern(v) for v in variants(t["term"])] for tid, t in self.terms.items()}

    def found(self, term_id: str, text: str) -> bool:
        norm = normalize(text)
        return any(p.search(norm) for p in self._patterns.get(term_id, []))

    def genz_terms(self, country: str) -> list[str]:
        return [tid for tid, t in self.terms.items() if t["generation"] == "genz" and t["country"] in (country, "LATAM")]


def slang_handled(bank: TermBank, pair: dict, linked_term_ids: list[str], hypothesis: str) -> bool | None:
    """True/False, or None when the pair can't be judged (no bank term found where needed)."""
    if not hypothesis.strip():
        return False
    if pair["direction"] == "genz_to_parent":
        in_source = [t for t in linked_term_ids if bank.terms.get(t, {}).get("generation") == "genz" and bank.found(t, pair["source"])]
        if not in_source:
            in_source = [t for t in bank.genz_terms(pair["country"]) if bank.found(t, pair["source"])]
        if not in_source:
            return None
        return not any(bank.found(t, hypothesis) for t in in_source)
    return any(bank.found(t, hypothesis) for t in bank.genz_terms(pair["country"]))


def reference_changes(source: str, reference: str) -> set[str]:
    src = set(normalize(source).split())
    return {w for w in normalize(reference).split() if w not in src and w not in STOPWORDS and len(w) > 2}


def change_recall(source: str, reference: str, hypothesis: str) -> float | None:
    wanted = reference_changes(source, reference)
    if not wanted:
        return None
    got = set(normalize(hypothesis).split())
    return len(wanted & got) / len(wanted)


def foreign_slang(bank: TermBank, pair: dict, hypothesis: str) -> bool:
    """Output uses Gen Z slang of another country (and none of its own): e.g. Guatemalan "pisto" in a Mexican phrase."""
    own = set(bank.genz_terms(pair["country"]))
    other = [t for t, v in bank.terms.items() if v["generation"] == "genz" and t not in own]
    return any(bank.found(t, hypothesis) for t in other) and not any(bank.found(t, hypothesis) for t in own)
