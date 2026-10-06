"""Term-by-term check for the comparison page: which slang terms each translation got right.

The same rules as the eval's *jerga correcta* (evals/term_accuracy.py), one term at a time, so the
page can show a ✓ or ✗ next to each term:

- Gen Z → papás: the Gen Z term is gone and its meaning (or its validated parents' counterpart, or the
  word the human reference used for it) is in the translation ("chivas" → "cosas").
- papás → Gen Z: the parents' term was replaced by its validated Gen Z counterpart or an equivalent
  ("refacción" → "refa").

Deterministic: no model judges the models.
"""

from __future__ import annotations

from .terms import STOPWORDS, TermBank, normalize


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


def _label(term: str) -> str:
    return term.split("/")[0].strip()


def term_checks(bank: TermBank, cps: dict[str, str | None], phrase: str, direction: str,
                country: str, hypothesis: str, reference: str | None = None) -> list[dict]:
    """[{term, expected, ok}] for each slang term of `phrase` the bank can judge; [] if none.
    `reference`: the human translation, when there is one; the words it introduced also count."""
    ref_words = _stems(reference) - _stems(phrase) if reference else set()
    out: list[dict] = []
    seen: set[str] = set()  # one line per term even if the bank has two entries for it
    if direction == "genz_to_parent":
        for t in bank.found_in(phrase, bank.ids("genz")):
            if _label(bank.terms[t]["term"]) in seen:
                continue
            seen.add(_label(bank.terms[t]["term"]))
            meaning = bank.terms[t]["meaning"]
            cp = cps.get(t)
            if bank.found(t, hypothesis):
                ok = False  # the slang was left in
            else:
                hyp = _stems(hypothesis)
                ok = bool(cp and cp in bank.terms and bank.found(cp, hypothesis)) or bool((_stems(meaning) | ref_words) & hyp)
            out.append({"term": _label(bank.terms[t]["term"]), "expected": meaning, "ok": ok})
        return out
    allowed = {country, "LATAM"}
    for t in bank.found_in(phrase, bank.ids("parent")):
        cp = cps.get(t)
        if not cp:
            continue
        accept = {e for e in equivalents(cps, cp)
                  if e in bank.terms and bank.terms[e]["generation"] == "genz" and bank.terms[e]["country"] in allowed}
        if not accept:
            continue
        out.append({
            "term": _label(bank.terms[t]["term"]),
            "expected": " · ".join(sorted(_label(bank.terms[e]["term"]) for e in accept)),
            "ok": any(bank.found(e, hypothesis) for e in accept),
        })
    return out
