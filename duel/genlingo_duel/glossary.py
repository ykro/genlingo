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
import random
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


LEX_K = 6  # entries in a v2+lex glossary


def load_counterparts(path: Path) -> dict[str, str | None]:
    """term_id -> meaning-validated counterpart id (data/counterparts.jsonl, scripts/build_counterparts.py)."""
    if not path.exists():
        return {}
    rows = (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return {r["term_id"]: r["counterpart_id"] for r in rows}


class Glossary:
    def __init__(self, bank: TermBank, embed: Embedder, *, cache: Path | None = None, model: str = "mock", k: int = 4,
                 counterparts: dict[str, str | None] | None = None):
        self.bank, self.embed, self.cache, self.model, self.k = bank, embed, cache, model, k
        self.counterparts = counterparts or {}
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


    def _entry(self, tid: str, **extra) -> dict:
        t = self.bank.terms[tid]
        return {"id": tid, "term": t["term"], "meaning": t["meaning"], "generation": t["generation"], "country": t["country"], **extra}

    async def lex_entries(self, phrase: str, direction: str, country: str, k: int = LEX_K) -> list[dict]:
        """v2+lex: each source-generation term in the phrase with its validated counterpart, then the
        nearest target-generation terms, then one foreign term marked as such; shuffled per phrase."""
        allowed = [country, "LATAM"]
        source_gen, target_gen = ("genz", "parent") if direction == "genz_to_parent" else ("parent", "genz")
        out, shown = [], set()
        for tid in self.bank.found_in(phrase, self.bank.ids(source_gen, allowed))[: k - 2]:
            cp = self.counterparts.get(tid)
            out.append(self._entry(tid, role="link", counterpart=self._entry(cp) if cp else None))
            shown |= {tid, cp}
        if self.vectors:
            [q] = await self.embed([phrase])
            near = sorted((t for t in self.bank.ids(target_gen, allowed) if t in self.vectors and t not in shown),
                          key=lambda t: _cos(q, self.vectors[t]), reverse=True)
            out += [self._entry(t, role="near") for t in near[: max(0, k - 1 - len(out))]]
            foreign = sorted((t for t in self.bank.ids(target_gen) if t in self.vectors
                              and self.bank.terms[t]["country"] not in allowed), key=lambda t: _cos(q, self.vectors[t]), reverse=True)
            out += [self._entry(t, role="foreign") for t in foreign[:1]]
        rng = random.Random(hashlib.sha1(f"{phrase}|{direction}|{country}".encode()).hexdigest())
        rng.shuffle(out)  # position must not give the answer away (training shuffles the same way)
        return out


COUNTRY_NAMES = {"MX": "México", "GT": "Guatemala", "CO": "Colombia", "LATAM": "neutro"}
LABEL = {"genz": "Gen Z", "parent": "papás"}


def render_lex(entries: list[dict], country_name: str) -> str:
    if not entries:
        return ""
    lines = []
    for e in entries:
        if e.get("role") == "foreign":
            lines.append(f"- «{e['term']}» ({LABEL[e['generation']]} de {COUNTRY_NAMES[e['country']]}, NO de {country_name}): {e['meaning']}")
        elif e.get("counterpart"):
            cp = e["counterpart"]
            lines.append(f"- «{e['term']}» ({LABEL[e['generation']]}) = «{cp['term']}» ({LABEL[cp['generation']]}): {e['meaning']}")
        else:
            lines.append(f"- «{e['term']}» ({LABEL[e['generation']]}): {e['meaning']}")
    return f"\n\nGlosario de {country_name} (úsalo si aplica; no uses términos de otros países):\n" + "\n".join(lines)


def render(entries: list[dict], country_name: str) -> str:
    if entries and any("role" in e for e in entries):
        return render_lex(entries, country_name)
    if not entries:
        return ""
    label = {"genz": "Gen Z", "parent": "papás"}
    lines = [f"- «{e['term']}» ({label[e['generation']]}): {e['meaning']}" for e in entries]
    return f"\n\nGlosario de {country_name} (úsalo si aplica):\n" + "\n".join(lines)
