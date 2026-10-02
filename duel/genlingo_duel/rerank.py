"""N-best for David: several answers in parallel, keep the one the term bank likes best.

A small model sometimes knows the right slang but doesn't pick it with greedy decoding. Ollama
answers N requests in parallel (OLLAMA_NUM_PARALLEL) for about the price of one, and a cheap,
deterministic score over our own data chooses:

    +2  per validated counterpart from the glossary that the answer uses (the lexicon's answer)
    +1  the answer has slang of the target generation from this country (papás -> Gen Z)
    −2  per source-side slang term left in the answer (Gen Z -> papás)
    −2  per term of the target generation from ANOTHER country

Ties keep the earliest candidate (the low-temperature one). No model judges another model.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

from duel_core import Completion, clean_translation

from .terms import TermBank

Scorer = Callable[[str], float]


def term_bank_scorer(bank: TermBank, phrase: str, direction: str, country: str, entries: list[dict]) -> Scorer:
    allowed = [country, "LATAM"]
    src_gen, tgt_gen = ("genz", "parent") if direction == "genz_to_parent" else ("parent", "genz")
    expected = [e["counterpart"]["id"] for e in entries if e.get("counterpart")]
    source_terms = bank.found_in(phrase, bank.ids(src_gen))
    foreign = [t for t in bank.ids(tgt_gen) if bank.terms[t]["country"] not in allowed]
    local = bank.ids(tgt_gen, allowed)

    def score(text: str) -> float:
        if not text.strip():
            return -100.0
        s = 2.0 * sum(bank.found(t, text) for t in expected)
        if direction == "parent_to_genz":
            s += 1.0 if bank.found_in(text, local) else 0.0
        else:
            s -= 2.0 * sum(bank.found(t, text) for t in source_terms)
        s -= 2.0 * len(bank.found_in(text, foreign))
        return s

    return score


class NBestClient:
    """Wraps a model client: N requests in parallel (first at the client's own temperature, the rest
    sampled with fixed seeds), returns the best-scoring answer. Latency = the slowest of the N."""

    def __init__(self, inner, n: int, scorer: Scorer, temperature: float = 0.7):
        self.inner, self.n, self.scorer, self.temperature = inner, n, scorer, temperature
        self.last: list[tuple[str, float]] = []

    async def complete(self, messages, *, model: str) -> Completion:
        t0 = time.perf_counter()
        calls = [self.inner.complete(messages, model=model)]
        if hasattr(self.inner, "options"):  # Ollama: sampled variants with fixed seeds
            calls += [self.inner.complete(messages, model=model, options={"temperature": self.temperature, "seed": 1000 + i})
                      for i in range(1, self.n)]
        else:  # mock clients: plain repeats
            calls += [self.inner.complete(messages, model=model) for _ in range(1, self.n)]
        results = await asyncio.gather(*calls, return_exceptions=True)
        ok = [r for r in results if isinstance(r, Completion)]
        if not ok:
            raise next(r for r in results if isinstance(r, BaseException))
        scored = [(c, self.scorer(clean_translation(c.text))) for c in ok]
        self.last = [(clean_translation(c.text), s) for c, s in scored]
        best = max(range(len(scored)), key=lambda i: (scored[i][1], -i))
        c = scored[best][0]
        return Completion(text=c.text, model=c.model, latency_ms=(time.perf_counter() - t0) * 1000,
                          input_tokens=sum(x.input_tokens for x in ok), output_tokens=sum(x.output_tokens for x in ok))
