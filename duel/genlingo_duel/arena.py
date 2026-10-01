"""David vs. Goliath: builds both contenders from settings and runs one duel.

David = a small Gemma fine-tuned on our pairs, served by Ollama on the laptop (free, offline).
Goliath = Gemini on Vertex AI (paid per token, needs internet).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from duel_core import (
    Connectivity,
    Contender,
    ContenderResult,
    GeminiClient,
    MockClient,
    ModelClient,
    OllamaClient,
    Price,
    run_duel,
)

from .dataset import read_jsonl
from .glossary import Glossary, hashing_embedder
from .glossary import render as render_glossary
from .prompts import COUNTRIES, STYLES, Direction, prompt_version, translation_messages
from .runs import load_run
from .settings import Settings, goliath_prices
from .terms import TermBank

# Mock answers: David "knows" the slang, Goliath answers almost literally, so rehearsals show
# a plausible duel without network or GPU.
_MOCK_DAVID = {"genz_to_parent": "estuvo regular y me dio pena ajena", "parent_to_genz": "estuvo bien mid, me dio cringe"}
_MOCK_GOLIATH = {"genz_to_parent": "estuvo mediocre y me dio vergüenza", "parent_to_genz": "estuvo mid y me dio cringe total"}


def _mock_responder(table: dict[str, str]):
    def respond(messages) -> str:
        system = messages[0]["content"]
        return table["genz_to_parent" if "al habla de sus papás" in system else "parent_to_genz"]

    return respond


def prompt_style_for(settings: Settings, david_tag: str) -> str:
    """Each David is prompted the way its training data was rendered (recorded in its run file)."""
    run = load_run(settings.runs_dir, david_tag)  # exports (-f16, -q5_k_m…) share their run's prompt
    if run and run.get("prompt_style") in STYLES:
        return run["prompt_style"]
    return settings.david_prompt_style


@dataclass
class Arena:
    settings: Settings
    david_client: ModelClient
    goliath_client: ModelClient
    connectivity: Connectivity
    glossary: Glossary | None = None

    async def get_glossary(self) -> Glossary:
        """The term-bank glossary (embeddings computed once and cached on disk; works offline)."""
        if self.glossary is None:
            s = self.settings
            bank = TermBank(read_jsonl(s.data_dir / "terms.jsonl"))
            if s.mock_ai or not s.embedding_model:
                self.glossary = await Glossary(bank, hashing_embedder()).load()
            else:
                client = self.david_client  # Ollama: the same local server David runs on
                self.glossary = await Glossary(
                    bank,
                    lambda texts: client.embed(texts, model=s.embedding_model),  # type: ignore[attr-defined]
                    cache=s.data_dir / ".cache" / "term_embeddings.json",
                    model=s.embedding_model,
                ).load()
        return self.glossary

    @classmethod
    def from_settings(cls, s: Settings) -> "Arena":
        if s.mock_ai:
            return cls(
                s,
                MockClient(_mock_responder(_MOCK_DAVID), latency_ms=320),
                MockClient(_mock_responder(_MOCK_GOLIATH), latency_ms=1450, offline=s.force_offline),
                Connectivity(force_offline=s.force_offline, host="127.0.0.1", port=1),
            )
        return cls(
            s,
            OllamaClient(s.ollama_url),
            GeminiClient(s.project, s.location, thinking_level=s.gemini_thinking_level or None),
            Connectivity(force_offline=s.force_offline),
        )

    def contenders(self, david_tag: str | None = None) -> list[Contender]:
        s = self.settings
        return [
            Contender("david", self.david_client, david_tag or s.david_tag, Price.free()),
            Contender(
                "goliath",
                self.goliath_client,
                s.gemini_model,
                goliath_prices(s).at(),  # the price in force today
                requires_network=True,
            ),
        ]

    async def is_online(self) -> bool:
        if self.settings.mock_ai:
            return not self.settings.force_offline
        return await self.connectivity.is_online()

    async def duel(
        self,
        phrase: str,
        direction: Direction,
        country: str,
        *,
        david_tag: str | None = None,
        reference: str | None = None,
    ) -> dict[str, ContenderResult]:
        s = self.settings
        tag = david_tag or s.david_tag
        styles = {"david": prompt_style_for(s, tag), "goliath": s.goliath_prompt_style}
        entries: list[dict] = []
        retrieval_ms = 0.0
        if "v2+glossary" in styles.values():
            t0 = time.perf_counter()
            entries = await (await self.get_glossary()).entries(phrase, direction, country)
            retrieval_ms = (time.perf_counter() - t0) * 1000
        block = render_glossary(entries, COUNTRIES[country])
        messages = {name: translation_messages(phrase, direction, country, style, block) for name, style in styles.items()}
        online = await self.is_online()
        results = await run_duel(self.contenders(tag), messages, reference=reference, online=online)
        for name, res in results.items():
            used = styles[name] == "v2+glossary"
            # Retrieval is part of the answer: its time counts in the latency the audience sees.
            if used and res.latency_ms is not None:
                res.latency_ms = round(res.latency_ms + retrieval_ms, 1)
            res.extra = {
                "prompt": prompt_version(styles[name]),
                "glossary": [e["term"] for e in entries] if used else [],
                "retrieval_ms": round(retrieval_ms, 1) if used else 0.0,
            }
        return results
