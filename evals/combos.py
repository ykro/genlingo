"""The combinations niche (evals/niche.md, amendment 2): sentences that pack several slang terms together.

A pair is a "combination" when its Gen Z side (the source in Gen Z -> papás, the reference in papás -> Gen Z)
holds at least MIN_TERMS distinct Gen Z terms of the FROZEN test bank (data/eval/terms_test.jsonl, ambiguous
terms left out) of the pair's country or LATAM. Two terms count once when a form of one sits inside a form of
the other ("chido" inside "bien chido"), or when their matches overlap in the sentence.

Used by scripts/build_combos_set.py (which sentences enter the niche), scripts/real_usage.py (which round-5
sentences are held out for it) and evals/combos_report.py (the cuts).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "duel"))

from genlingo_duel.terms import TermBank, normalize, variants  # noqa: E402

MIN_TERMS = 2


def genz_side(pair: dict) -> str:
    return pair["source"] if pair["direction"] == "genz_to_parent" else pair["target"]


def distinct_terms(bank: TermBank, text: str, country: str) -> list[str]:
    """Distinct Gen Z terms of the country (or LATAM) in `text`, nested or same-span matches counted once."""
    found = bank.found_in(text, bank.ids("genz", [country, "LATAM"]))
    norm = normalize(text)
    spans = {t: [m.span() for p in bank._patterns[t] for m in p.finditer(norm)] for t in found}
    forms = {t: [f" {v} " for v in variants(bank.terms[t]["term"])] for t in found}
    # longest match first, so "bien chido" is kept and "chido" folds into it
    found.sort(key=lambda t: -max((e - s for s, e in spans[t]), default=0))
    kept: list[str] = []
    for t in found:
        nested = any(a in b or b in a for k in kept for a in forms[t] for b in forms[k])
        overlap = any(s1 < e2 and s2 < e1 for k in kept for s1, e1 in spans[t] for s2, e2 in spans[k])
        if not (nested or overlap):
            kept.append(t)
    return kept


def is_combo(bank: TermBank, pair: dict) -> bool:
    return len(distinct_terms(bank, genz_side(pair), pair["country"])) >= MIN_TERMS


def frozen_bank(data_dir: Path) -> TermBank:
    from genlingo_duel.dataset import read_jsonl

    return TermBank(read_jsonl(data_dir / "eval" / "terms_test.jsonl"), ignore_ambiguous=True)
