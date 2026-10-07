"""All configuration comes from env vars (see `.env.example`). No model names in code:
models age, and swapping them must not require a code change."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from duel_core import Price, PriceSchedule

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _flag(name: str) -> bool:
    return _env(name, "0").lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float) -> float:
    raw = _env(name)
    return float(raw) if raw else default


@dataclass
class Settings:
    project: str = field(default_factory=lambda: _env("GOOGLE_CLOUD_PROJECT", "ai-experiments-487722"))
    location: str = field(default_factory=lambda: _env("GOOGLE_CLOUD_LOCATION", "global"))
    gemini_model: str = field(default_factory=lambda: _env("GEMINI_MODEL"))
    gemini_thinking_level: str = field(default_factory=lambda: _env("GEMINI_THINKING_LEVEL", "low"))
    # Dated USD-per-million prices: "2026-01-01:0.75/3.75,2027-01-01:1.50/7.50".
    gemini_price_schedule: str = field(default_factory=lambda: _env("GEMINI_PRICE_SCHEDULE"))
    # Single-price fallback when no schedule is configured.
    gemini_input_usd_per_m: float = field(default_factory=lambda: _float("GEMINI_INPUT_USD_PER_M", 0.0))
    gemini_output_usd_per_m: float = field(default_factory=lambda: _float("GEMINI_OUTPUT_USD_PER_M", 0.0))
    # The Ollama tag of David (the fine-tuned Gemma the page uses), served by the David service.
    david_tag: str = field(default_factory=lambda: _env("DAVID_MODEL_TAG"))
    # Prompt styles (plain | country | glossary | lexicon; see prompts.py). David's comes from his run file when it has one;
    # Goliath gets no glossary by default (the term bank is David's data), set it to compare.
    david_prompt_style: str = field(default_factory=lambda: _env("DAVID_PROMPT_STYLE", "plain"))
    goliath_prompt_style: str = field(default_factory=lambda: _env("GOLIATH_PROMPT_STYLE", "country"))
    # David's Ollama: the private Cloud Run GPU service (infra/04-david.sh), called with an ID token
    # when it is https. The eval job runs its own Ollama inside the job (OLLAMA_URL).
    david_url: str = field(default_factory=lambda: _env("DAVID_URL", _env("OLLAMA_URL", "http://127.0.0.1:11434")))
    ollama_url: str = field(default_factory=lambda: _env("OLLAMA_URL", "http://127.0.0.1:11434"))
    # Sentence-embedding model (served by the same Ollama) for the term-bank glossary retrieval.
    embedding_model: str = field(default_factory=lambda: _env("EMBEDDING_MODEL"))
    mock_ai: bool = field(default_factory=lambda: _flag("MOCK_AI"))
    data_dir: Path = field(default_factory=lambda: REPO_ROOT / "data")
    runs_dir: Path = field(default_factory=lambda: REPO_ROOT / "train" / "runs")
    # The page translates with this country's slang (the examples are Guatemalan).
    country: str = field(default_factory=lambda: _env("EVENT_COUNTRY", "GT"))
    # David's N-best: candidates generated in parallel and reranked with the term bank (1 = off).
    david_nbest: int = field(default_factory=lambda: int(_env("DAVID_NBEST", "1")))
    # Spending limits of the public page (limits.py): per visitor per minute, and per day for the whole page.
    limit_translate_per_min: int = field(default_factory=lambda: int(_env("LIMIT_TRANSLATE_PER_MIN", "60")))
    limit_wake_per_min: int = field(default_factory=lambda: int(_env("LIMIT_WAKE_PER_MIN", "12")))
    limit_gemini_per_day: int = field(default_factory=lambda: int(_env("LIMIT_GEMINI_PER_DAY", "1500")))
    limit_wakes_per_day: int = field(default_factory=lambda: int(_env("LIMIT_WAKES_PER_DAY", "24")))
    # What David's GPU service costs per second while it runs (Cloud Run: L4 + vCPU + memory, billed by the
    # second; infra/04-david.sh sizes it). The page shows David's cost as these seconds × this rate.
    david_usd_per_s: float = field(default_factory=lambda: (
        _float("CLOUD_RUN_L4_USD_PER_S", 0.0) + _float("DAVID_CPU", 4) * _float("CLOUD_RUN_VCPU_USD_PER_S", 0.0)
        + _float("DAVID_MEMORY_GIB", 16) * _float("CLOUD_RUN_GIB_USD_PER_S", 0.0)))


def goliath_prices(s: "Settings") -> PriceSchedule:
    """The price list for Goliath; the duel and the eval pick the price in force on their date."""
    if s.gemini_price_schedule:
        return PriceSchedule.parse(s.gemini_price_schedule)
    return PriceSchedule.single(Price(s.gemini_input_usd_per_m, s.gemini_output_usd_per_m))


def get_settings() -> Settings:
    return Settings()
