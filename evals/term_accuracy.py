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

from genlingo_duel.term_check import equivalents, term_checks  # noqa: E402,F401  (equivalents re-exported)
from genlingo_duel.terms import STOPWORDS, TermBank, normalize, variants  # noqa: E402,F401  (re-exported)


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


# ---------------------------------------------------------------------------------------------
# Amendment 1 (evals/niche.md, registered 2026-10-02 10:50): meaning-aware metrics. They use the
# meaning-validated counterpart table (data/counterparts.jsonl): term_id -> counterpart_id or None.
# ---------------------------------------------------------------------------------------------
def correct_slang(bank: TermBank, cps: dict[str, str | None], pair: dict, hypothesis: str) -> bool | None:
    """Jerga correcta: every slang term of the pair gets a ✓ in the page's term-by-term check
    (duel/genlingo_duel/term_check.py, rules there), with the pair's reference as the human translation.
    None = the bank can't judge the pair."""
    checks = term_checks(bank, cps, pair["source"], pair["direction"], pair["country"], hypothesis, pair.get("target") or None)
    return all(c["ok"] for c in checks) if checks else None


def change_recall_synonyms(bank: TermBank, cps: dict[str, str | None], pair: dict, hypothesis: str) -> float | None:
    """Cambios acertados con sinónimos: same word, same 5-letter stem, or a linked term of the bank."""
    wanted = reference_changes(pair["source"], pair["target"])
    if not wanted:
        return None
    hyp_words = set(normalize(hypothesis).split())
    hyp_stems = {w[:5] for w in hyp_words if len(w) > 3}
    ref_terms = bank.found_in(pair["target"], list(bank.terms))
    linked_hit = {w for t in ref_terms for w in normalize(bank.terms[t]["term"]).split()
                  if any(bank.found(e, hypothesis) for e in equivalents(cps, t) if e in bank.terms)}
    hit = {w for w in wanted if w in hyp_words or (len(w) > 3 and w[:5] in hyp_stems) or w in linked_hit}
    return len(hit) / len(wanted)
