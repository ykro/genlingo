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
    david_tag: str = field(default_factory=lambda: _env("LOCAL_MODEL_TAG"))
    ollama_url: str = field(default_factory=lambda: _env("OLLAMA_URL", "http://127.0.0.1:11434"))
    mock_ai: bool = field(default_factory=lambda: _flag("MOCK_AI"))
    force_offline: bool = field(default_factory=lambda: _flag("FORCE_OFFLINE"))
    db_path: Path = field(default_factory=lambda: REPO_ROOT / _env("DUEL_DB_PATH", "duel/state/genlingo.sqlite"))
    data_dir: Path = field(default_factory=lambda: REPO_ROOT / "data")
    runs_dir: Path = field(default_factory=lambda: REPO_ROOT / "train" / "runs")
    firestore_database: str = field(default_factory=lambda: _env("FIRESTORE_DATABASE", "genlingo"))
    audience_feed: bool = field(default_factory=lambda: _flag("AUDIENCE_FEED"))
    event_id: str = field(default_factory=lambda: _env("EVENT_ID", "ensayo"))
    # Evaluation rounds may use test pairs still pending review (useful before the presenter
    # has reviewed them); on stage set it to 0 so only approved references are shown.
    allow_unreviewed_test: bool = field(default_factory=lambda: _flag("ALLOW_UNREVIEWED_TEST"))


def goliath_prices(s: "Settings") -> PriceSchedule:
    """The price list for Goliath; the duel and the eval pick the price in force on their date."""
    if s.gemini_price_schedule:
        return PriceSchedule.parse(s.gemini_price_schedule)
    return PriceSchedule.single(Price(s.gemini_input_usd_per_m, s.gemini_output_usd_per_m))


def get_settings() -> Settings:
    return Settings()
