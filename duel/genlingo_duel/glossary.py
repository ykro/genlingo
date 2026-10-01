"""A tiny per-phrase glossary retrieved from our own term bank: David's home advantage.

Before translating, we look up the few term-bank entries that matter for this phrase and this
country: exact matches of slang in the phrase, plus the closest entries by meaning (EmbeddingGemma,
running locally in Ollama, so it works with Wi-Fi off). The glossary goes into the prompt.

It's legitimate because the term bank is our data (researched, sourced, dated) and Goliath doesn't
have it. It's visible because the eval also runs Goliath *with* the same glossary, so the room can
see how much of David's result is the model and how much is the data.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

from .terms import TermBank

Embedder = Callable[[list[str]], Awaitable[list[list[float]]]]


def hashing_embedder(dim: int = 256) -> Embedder:
    """Deterministic bag-of-words vectors for MOCK_AI and tests (no model needed)."""

    async def embed(texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            v = [0.0] * dim
            for w in re.findall(r"\w+", t.lower()):
                v[int(hashlib.md5(w.encode()).hexdigest(), 16) % dim] += 1.0
            out.append(v)
        return out

    return embed


def _cos(a: list[float], b: list[float]) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


class Glossary:
    def __init__(self, bank: TermBank, embed: Embedder, *, cache: Path | None = None, model: str = "mock", k: int = 4):
        self.bank, self.embed, self.cache, self.model, self.k = bank, embed, cache, model, k
        self.vectors: dict[str, list[float]] = {}

    @staticmethod
    def entry_text(t: dict) -> str:
        return f"{t['term']}: {t['meaning']}"

    async def load(self) -> "Glossary":
        """Embed every term once (cached on disk, keyed by model and term-bank content)."""
        texts = {tid: self.entry_text(t) for tid, t in self.bank.terms.items()}
        key = hashlib.sha1((self.model + json.dumps(texts, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()
        if self.cache and self.cache.exists():
            data = json.loads(self.cache.read_text())
            if data.get("key") == key:
                self.vectors = data["vectors"]
                return self
        ids = list(texts)
        vecs = await self.embed([texts[i] for i in ids])
        self.vectors = dict(zip(ids, vecs))
        if self.cache:
            self.cache.parent.mkdir(parents=True, exist_ok=True)
            self.cache.write_text(json.dumps({"key": key, "vectors": self.vectors}))
        return self

    async def entries(self, phrase: str, direction: str, country: str) -> list[dict]:
        allowed = [country, "LATAM"]
        # What the phrase already says (slang of the source generation), then what it could become.
        source_gen, target_gen = ("genz", "parent") if direction == "genz_to_parent" else ("parent", "genz")
        exact = self.bank.found_in(phrase, self.bank.ids(source_gen, allowed))
        picked = exact[: self.k]
        if len(picked) < self.k and self.vectors:
            [q] = await self.embed([phrase])
            candidates = [t for t in self.bank.ids(target_gen, allowed) if t in self.vectors]
            ranked = sorted(candidates, key=lambda t: _cos(q, self.vectors[t]), reverse=True)
            picked += [t for t in ranked if t not in picked][: self.k - len(picked)]
        return [{"id": t, **{k: self.bank.terms[t][k] for k in ("term", "meaning", "generation")}} for t in picked]


def render(entries: list[dict], country_name: str) -> str:
    if not entries:
        return ""
    label = {"genz": "Gen Z", "parent": "papás"}
    lines = [f"- «{e['term']}» ({label[e['generation']]}): {e['meaning']}" for e in entries]
    return f"\n\nGlosario de {country_name} (úsalo si aplica):\n" + "\n".join(lines)
