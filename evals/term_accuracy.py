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


# ---------------------------------------------------------------------------------------------
# Amendment 1 (evals/niche.md, registered 2026-10-02 10:50): meaning-aware metrics. They use the
# meaning-validated counterpart table (data/counterparts.jsonl): term_id -> counterpart_id or None.
# ---------------------------------------------------------------------------------------------
def _stems(text: str) -> set[str]:
    return {w[:5] for w in normalize(text).split() if len(w) > 3 and w not in STOPWORDS}


def equivalents(cps: dict[str, str | None], tid: str) -> set[str]:
    """tid, its validated counterpart, and same-generation terms that share that counterpart."""
    out = {tid}
    cp = cps.get(tid)
    if cp:
        out.add(cp)
        out |= {t for t, c in cps.items() if c == cp}
        out |= {t for t, c in cps.items() if t == cp and c}
    return out


def correct_slang(bank: TermBank, cps: dict[str, str | None], pair: dict, hypothesis: str) -> bool | None:
    """Jerga correcta: the slang produced means the same as what had to be said. None = not judgeable."""
    src, ref, country = pair["source"], pair["target"], pair["country"]
    allowed = [country, "LATAM"]
    if pair["direction"] == "parent_to_genz":
        accept: set[str] = set()
        for t in bank.found_in(ref, bank.ids("genz", allowed)):
            accept |= equivalents(cps, t)
        for t in bank.found_in(src, bank.ids("parent")):
            if cps.get(t):
                accept |= equivalents(cps, cps[t])
        accept = {t for t in accept if t in bank.terms and bank.terms[t]["generation"] == "genz"}
        if not accept:
            return None
        return any(bank.found(t, hypothesis) for t in accept)
    slang = bank.found_in(src, bank.ids("genz"))
    if not slang:
        return None
    if any(bank.found(t, hypothesis) for t in slang):
        return False
    hyp_stems = _stems(hypothesis)
    for t in slang:
        cp = cps.get(t)
        if cp and cp in bank.terms and bank.found(cp, hypothesis):
            continue
        if not (_stems(bank.terms[t]["meaning"]) & hyp_stems):
            return False
    return True


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
