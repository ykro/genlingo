"""Term-by-term check: which slang terms a translation got right (a ✓ or ✗ per term on the page).

The eval's *jerga correcta* (evals/term_accuracy.correct_slang) is this same check over a test pair: a
pair counts as correct when every term gets a ✓. So the page and the reports can't disagree.

Each term is judged in **its place** in the translation: the words between the words that stayed the
same around it (a word-by-word alignment of the phrase and the translation), plus any new words the
translation moved elsewhere that aren't in another term's place.

- **Gen Z → papás**: the Gen Z term is gone AND its place is taken by the plain meaning:
  - no other Gen Z term of the bank in that place, from any country ("¿qué onda?" for "¿qué pex?",
    "shuco" in a parents' sentence), and
  - the meaning is there: a word of the term's meaning in the bank, its validated parents' counterpart, a
    parents' expression with the same meaning ("un titipuchal" for "un chingo"), or the words the human
    reference put in that same place. A word that carries another term's meaning doesn't count: in
    "un chingo de chamba" → "un friego de trabajo", "trabajo" answers for "chamba", and "friego" (slang the
    bank doesn't know) doesn't mean "mucho", so "un chingo" gets a ✗.
- **papás → Gen Z**: the output uses slang valid for the phrase's country: the validated Gen Z
  counterpart, a term of that country (or pan-Hispanic) that shares it, or the slang the human
  reference put in that place. The same meaning in another country's slang is ✗ ("maje", Guatemala,
  for "cuate" in a Mexican phrase), and so is any other country's slang in the term's place. Neutral
  Spanish (LATAM) takes only pan-Hispanic slang. With a reference, only the parents' words the human
  changed are checked; when the bank knows none of them, the Gen Z terms the reference used are.

Deterministic: no model judges the models.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .terms import STOPWORDS, TermBank, normalize

_SUPERLATIVE = re.compile(r"isim[oa]s?$")  # "muchísimo" means "mucho", "buenísima" means "buena"


def _stem(word: str) -> str:
    return _SUPERLATIVE.sub("o", word)[:5]


def _stems(text: str) -> set[str]:
    return {_stem(w) for w in normalize(text).split() if len(w) > 3 and w not in STOPWORDS}


def _senses(meaning: str) -> list[str]:
    """The meaning's alternatives as whole phrases, without the notes: "sí (a veces con ironía)" -> ["si"]."""
    plain = re.sub(r"\([^)]*\)", " ", meaning)
    return [a for a in (normalize(x) for x in re.split(r"[,;:\"¡!¿?]|\btambién\b|\bo\b", plain)) if len(a) > 1]


def _says(place: str, phrase: str) -> bool:
    return bool(phrase) and re.search(rf"\b{re.escape(phrase)}\b", place) is not None


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


class _Place:
    """The words of a rewrite that stand in for one term (positions in the rewrite's words)."""

    def __init__(self, rewrite: str = "", words: list[str] = (), positions: set[int] = frozenset()):
        self.rewrite, self.positions = rewrite, set(positions)
        runs: list[list[str]] = []
        for j in sorted(self.positions):  # contiguous stretches, so a phrase is never assembled from scattered words
            if not runs or j - 1 not in self.positions:
                runs.append([])
            runs[-1].append(words[j])
        self.stretches = [" ".join(r) for r in runs]

    def has(self, bank: TermBank, term_id: str) -> bool:
        """The term is in the rewrite and touches this place ("qué onda" counts even if "qué" stayed the same)."""
        return any(self.positions & set(range(a, b)) for a, b in bank.spans(term_id, self.rewrite))

    def says(self, words: str) -> bool:
        return any(_says(x, words) for x in self.stretches)

    def stems(self) -> set[str]:
        return set().union(*(_stems(x) for x in self.stretches))


class _Places:
    """Where a phrase's words ended up in a rewrite of it: the words that stayed the same anchor the rest."""

    def __init__(self, phrase: str, rewrite: str):
        self.rewrite, self.words = rewrite, normalize(rewrite).split()
        sm = SequenceMatcher(None, normalize(phrase).split(), self.words, autojunk=False)
        self._same = [(b.a + k, b.b + k) for b in sm.get_matching_blocks() for k in range(b.size)]
        self._new = set(range(len(self.words))) - {j for _, j in self._same}

    def _between(self, span: tuple[int, int]) -> set[int]:
        """The rewrite's words between the unchanged words just before and just after span."""
        start, end = span
        lo = max((j + 1 for i, j in self._same if i < start), default=0)
        hi = min((j for i, j in self._same if i >= end), default=len(self.words))
        return set(range(lo, hi))

    def between_text(self, span: tuple[int, int]) -> str:
        return " ".join(self.words[j] for j in sorted(self._between(span)))

    def of(self, span: tuple[int, int] | None, others: list[tuple[int, int] | None] = ()) -> _Place:
        """The term's place: the words between its unchanged neighbours, plus the new words the rewrite moved
        elsewhere that aren't in another term's place (a reordered sentence keeps its meaning). No span: all of it."""
        if span is None:
            return _Place(self.rewrite, self.words, set(range(len(self.words))))
        own = self._between(span)
        taken = own.union(*(self._between(o) for o in others if o is not None and o != span))
        return _Place(self.rewrite, self.words, own | (self._new - taken))


def _groups(bank: TermBank, phrase: str, term_ids: list[str]) -> dict[str, list[str]]:
    """One line per term even if the bank has two entries for it (label -> ids)."""
    out: dict[str, list[str]] = {}
    for t in bank.found_in(phrase, term_ids):
        out.setdefault(_label(bank.terms[t]["term"]), []).append(t)
    return out


def _span(bank: TermBank, ids: list[str], phrase: str) -> tuple[int, int] | None:
    spans = [s for t in ids for s in bank.spans(t, phrase)]
    return min(spans) if spans else None


def _slang(bank: TermBank, countries: set[str] | None = None, exclude: set[str] = frozenset()) -> list[str]:
    """Gen Z terms (of `countries`, or every country), never the ordinary-word ones."""
    return [t for t, v in bank.terms.items() if v["generation"] == "genz" and t not in exclude and not v.get("ambiguous")
            and (countries is None or v["country"] in countries)]


def term_checks(bank: TermBank, cps: dict[str, str | None], phrase: str, direction: str,
                country: str, hypothesis: str, reference: str | None = None) -> list[dict]:
    """[{term, expected, ok}] for each slang term of `phrase` the bank can judge; [] if none.
    `reference`: the human translation, when there is one."""
    allowed = {country, "LATAM"}
    hyp = _Places(phrase, hypothesis)
    ref = _Places(phrase, reference) if reference else None
    if direction == "genz_to_parent":
        return _to_parents(bank, cps, phrase, allowed, hypothesis, hyp, ref)
    return _to_genz(bank, cps, phrase, allowed, hypothesis, hyp, ref, reference)


def _to_parents(bank, cps, phrase, allowed, hypothesis, hyp: _Places, ref: _Places | None) -> list[dict]:
    groups = _groups(bank, phrase, bank.ids("genz"))
    spans = {label: _span(bank, ids, phrase) for label, ids in groups.items()}
    other_slang = _slang(bank, exclude={t for ids in groups.values() for t in ids})
    parents_words = bank.ids("parent", allowed)
    phrase_stems = _stems(phrase)

    def claims(ids: list[str]) -> set[str]:
        """The words that carry these terms' meaning: their meaning in the bank and their counterparts."""
        out = set()
        for t in ids:
            out |= _stems(bank.terms[t]["meaning"])
            if cps.get(t) in bank.terms:
                out |= _stems(bank.terms[cps[t]]["term"])
        return out

    out = []
    for label, ids in groups.items():
        others = [s for g, s in spans.items() if g != label]
        place = hyp.of(spans[label], others)
        meaning = set().union(*(_stems(bank.terms[t]["meaning"]) for t in ids))
        ref_place = ref.of(spans[label], others) if ref else _Place()
        ref_words = ref_place.stems() - phrase_stems - claims([t for g, i in groups.items() if g != label for t in i])
        if any(bank.found(t, hypothesis) for t in ids) or any(place.has(bank, t) for t in other_slang):
            ok = False  # the slang was left in, or other slang took its place
        else:
            ok = (bool((meaning | ref_words) & place.stems())
                  or any(place.says(a) for t in ids for a in _senses(bank.terms[t]["meaning"]))  # short ones: "sí"
                  or (ref is not None and place.says(ref.between_text(spans[label])))  # just what the human wrote there
                  or any(cps.get(t) in bank.terms and place.has(bank, cps[t]) for t in ids)
                  or any(place.has(bank, p) and _stems(bank.terms[p]["meaning"]) & meaning for p in parents_words))
        out.append({"term": label, "expected": bank.terms[ids[0]]["meaning"], "ok": ok})
    return out


def _to_genz(bank, cps, phrase, allowed, hypothesis, hyp: _Places, ref: _Places | None, reference: str | None) -> list[dict]:
    foreign = _slang(bank, countries=bank_countries(bank) - allowed)
    own_slang = _slang(bank, countries=allowed)

    def split(cands: set[str]) -> tuple[set[str], set[str]]:
        genz = {e for e in cands if e in bank.terms and bank.terms[e]["generation"] == "genz"}
        return {e for e in genz if bank.terms[e]["country"] in allowed}, {e for e in genz if bank.terms[e]["country"] not in allowed}

    groups = {label: ids for label, ids in _groups(bank, phrase, bank.ids("parent")).items()
              # the human kept the parents' word: nothing to check there
              if not (reference and any(bank.found(t, reference) for t in ids))}
    spans = {label: _span(bank, ids, phrase) for label, ids in groups.items()}
    items = []  # (label, span, accepted terms, the same meaning in another country's slang)
    for label, ids in groups.items():
        cands = set().union(*(equivalents(cps, cps[t]) for t in ids if cps.get(t)))
        if ref:  # what the human said in that place also counts ("canijo" -> "güey")
            ref_place = ref.of(spans[label], list(spans.values()))
            cands |= set().union(*(equivalents(cps, t) for t in own_slang if ref_place.has(bank, t)))
        accept, elsewhere = split(cands)
        if accept:
            items.append((label, spans[label], accept, elsewhere))
    if not items and reference:  # no parents' term the bank can link: the slang the reference used
        used = bank.found_in(reference, own_slang)
        if used:
            accept, elsewhere = split(set().union(*(equivalents(cps, t) for t in used)))
            items.append((" / ".join(sorted({_label(bank.terms[t]["term"]) for t in used})), None, accept, elsewhere))
    out = []
    for label, span, accept, elsewhere in items:
        place = hyp.of(span, list(spans.values()))
        wrong_country = any(bank.found(e, hypothesis) for e in elsewhere) or any(place.has(bank, t) for t in foreign)
        out.append({
            "term": label,
            "expected": " · ".join(sorted({_label(bank.terms[e]["term"]) for e in accept})),
            "ok": any(bank.found(e, hypothesis) for e in accept) and not wrong_country,
        })
    return out


def bank_countries(bank: TermBank) -> set[str]:
    return {v["country"] for v in bank.terms.values()}
