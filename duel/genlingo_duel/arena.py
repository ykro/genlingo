"""David vs. Goliath: builds both sides from settings and translates one phrase with either.

David = a small Gemma fine-tuned on our pairs, served by Ollama on a Cloud Run GPU (private service).
Goliath = Gemini on Vertex AI, used as anyone would (paid per token).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from duel_core import Contender, ContenderResult, GeminiClient, MockClient, ModelClient, OllamaClient, Price, run_duel

from .cloud_auth import IdTokenAuth
from .dataset import read_jsonl
from .glossary import Glossary, hashing_embedder, load_counterparts
from .glossary import render as render_glossary
from .rerank import NBestClient, term_bank_scorer
from .prompts import COUNTRIES, GLOSSARY_STYLES, STYLES, canonical_style, Direction, translation_messages
from .runs import load_run
from .settings import Settings, goliath_prices
from .terms import TermBank

log = logging.getLogger("genlingo.arena")

# Mock answers (MOCK_AI=1, tests): David "knows" the slang, Goliath answers almost literally.
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
    style = canonical_style(run.get("prompt_style")) if run else None
    if style in STYLES:
        return style
    return canonical_style(settings.david_prompt_style)


def david_client_for(url: str, **kwargs) -> OllamaClient:
    """Ollama client for David: an https URL is the private Cloud Run service (ID token)."""
    auth = IdTokenAuth(url) if url.startswith("https://") else None
    return OllamaClient(url, auth=auth, **kwargs)


@dataclass
class Arena:
    settings: Settings
    david_client: ModelClient
    goliath_client: ModelClient
    glossary: Glossary | None = None

    async def get_glossary(self) -> Glossary:
        """The term-bank glossary (term embeddings cached in data/.cache, so only the phrase is embedded)."""
        if self.glossary is None:
            s = self.settings
            bank = TermBank(read_jsonl(s.data_dir / "terms.jsonl"))
            counterparts = load_counterparts(s.data_dir / "counterparts.jsonl")
            if s.mock_ai or not s.embedding_model:
                self.glossary = await Glossary(bank, hashing_embedder(), counterparts=counterparts).load()
            else:
                client = self.david_client  # the same Ollama David runs on
                self.glossary = await Glossary(
                    bank,
                    lambda texts: client.embed(texts, model=s.embedding_model),  # type: ignore[attr-defined]
                    cache=s.data_dir / ".cache" / "term_embeddings.json",
                    model=s.embedding_model,
                    counterparts=counterparts,
                ).load()
        return self.glossary

    @classmethod
    def from_settings(cls, s: Settings) -> "Arena":
        if s.mock_ai:
            return cls(s, MockClient(_mock_responder(_MOCK_DAVID), latency_ms=320),
                       MockClient(_mock_responder(_MOCK_GOLIATH), latency_ms=1450))
        # Temperature 0 on both sides, as in `make eval`: the page shows what the eval measured, and the
        # same phrase gets the same answer every time it is shown.
        return cls(s, david_client_for(s.david_url, timeout_s=120.0, temperature=0.0),
                   GeminiClient(s.project, s.location, temperature=0.0, thinking_level=s.gemini_thinking_level or None,
                                timeout_s=30.0))  # Gemini sometimes takes 15–20 s; let it answer

    def contenders(self, david_client: ModelClient | None = None) -> list[Contender]:
        s = self.settings
        return [
            Contender("david", david_client or self.david_client, s.david_tag, Price.free()),
            Contender("goliath", self.goliath_client, s.gemini_model, goliath_prices(s).at()),  # today's price
        ]

    async def translate_one(self, side: str, phrase: str, direction: Direction, country: str) -> ContenderResult:
        """One side of the page, so each column shows its answer as soon as it arrives. For David the
        latency includes the glossary lookup (part of his answer). Nothing is recorded."""
        s = self.settings
        style = prompt_style_for(s, s.david_tag) if side == "david" else canonical_style(s.goliath_prompt_style)
        entries, retrieval_ms = [], 0.0
        if style in GLOSSARY_STYLES:
            entries, retrieval_ms, _ = await self.glossary_entries(style, phrase, direction, country)
        glossary = render_glossary(entries, COUNTRIES[country]) if style in GLOSSARY_STYLES else ""
        messages = translation_messages(phrase, direction, country, style, glossary)
        david_client = None
        if side == "david" and s.david_nbest > 1 and style in GLOSSARY_STYLES:
            g = await self.get_glossary()
            david_client = NBestClient(self.david_client, s.david_nbest, term_bank_scorer(g.bank, phrase, direction, country, entries))
        contender = [c for c in self.contenders(david_client) if c.name == side]
        res = (await run_duel(contender, messages))[side]
        if res.latency_ms is not None:
            res.latency_ms = round(res.latency_ms + retrieval_ms, 1)
        return res

    async def glossary_entries(self, style: str, phrase: str, direction: Direction, country: str) -> tuple[list[dict], float, str | None]:
        """(entries, retrieval ms, error) for a glossary prompt style. A failure means no glossary, never a 500."""
        t0 = time.perf_counter()
        try:
            g = await self.get_glossary()
            if GLOSSARY_STYLES[style] == "lex":
                entries = await g.lex_entries(phrase, direction, country)
            else:
                entries = await g.entries(phrase, direction, country)
            return entries, (time.perf_counter() - t0) * 1000, None
        except Exception as exc:  # embedding model not loaded yet or a hiccup
            log.warning("glossary unavailable, continuing without it: %s", exc)
            return [], (time.perf_counter() - t0) * 1000, f"{type(exc).__name__}: {exc}"[:200]
