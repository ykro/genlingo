"""David vs. Goliath: builds both contenders from settings and runs one duel.

David = a small Gemma fine-tuned on our pairs, served by Ollama on the laptop (free, offline).
Goliath = Gemini on Vertex AI (paid per token, needs internet).
"""

from __future__ import annotations

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

from .prompts import Direction, translation_messages
from .settings import Settings, goliath_prices

# Mock answers: David "knows" the slang, Goliath answers almost literally, so rehearsals show
# a plausible duel without network or GPU.
_MOCK_DAVID = {"genz_to_parent": "estuvo regular y me dio pena ajena", "parent_to_genz": "estuvo bien mid, me dio cringe"}
_MOCK_GOLIATH = {"genz_to_parent": "estuvo mediocre y me dio vergüenza", "parent_to_genz": "estuvo mid y me dio cringe total"}


def _mock_responder(table: dict[str, str]):
    def respond(messages) -> str:
        system = messages[0]["content"]
        return table["genz_to_parent" if "al habla de sus papás" in system else "parent_to_genz"]

    return respond


@dataclass
class Arena:
    settings: Settings
    david_client: ModelClient
    goliath_client: ModelClient
    connectivity: Connectivity

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
        messages = translation_messages(phrase, direction, country)
        online = await self.is_online()
        return await run_duel(self.contenders(david_tag), messages, reference=reference, online=online)
