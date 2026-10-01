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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "duel"))

from genlingo_duel.terms import STOPWORDS, TermBank, normalize, variants  # noqa: F401  (re-exported)


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
