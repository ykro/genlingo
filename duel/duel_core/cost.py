"""Cost from per-million-token prices, with a dated price schedule.

Prices live in the app config (env vars), never here: they change over time, and showing
that a frontier model's price moves while the local model's inference stays at zero is
part of the story. A schedule says which price applies on which date, so a duel in March 2027
is billed at March 2027 prices, and every cost says which price it used.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Price:
    input_per_million: float = 0.0
    output_per_million: float = 0.0
    effective_from: str | None = None  # ISO date the price started to apply (None = always)

    @classmethod
    def free(cls) -> "Price":
        """Local inference: the laptop is already paid for."""
        return cls(0.0, 0.0)


def cost_usd(price: Price, input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * price.input_per_million + output_tokens * price.output_per_million) / 1_000_000


@dataclass(frozen=True)
class PriceSchedule:
    """Prices by start date. `parse("2026-01-01:0.75/3.75,2027-01-01:1.50/7.50")`."""

    prices: tuple[Price, ...] = field(default_factory=tuple)

    @classmethod
    def parse(cls, spec: str) -> "PriceSchedule":
        prices = []
        for item in filter(None, (p.strip() for p in spec.split(","))):
            start, _, pair = item.partition(":")
            inp, _, out = pair.partition("/")
            date.fromisoformat(start)  # validate
            prices.append(Price(float(inp), float(out), start))
        return cls(tuple(sorted(prices, key=lambda p: p.effective_from or "")))

    @classmethod
    def single(cls, price: Price) -> "PriceSchedule":
        return cls((price,))

    def at(self, day: date | None = None) -> Price:
        """The price in force on `day` (today by default); free if nothing applies yet."""
        iso = (day or date.today()).isoformat()
        current = [p for p in self.prices if (p.effective_from or "") <= iso]
        return current[-1] if current else Price.free()

    def next_after(self, day: date | None = None) -> Price | None:
        iso = (day or date.today()).isoformat()
        upcoming = [p for p in self.prices if (p.effective_from or "") > iso]
        return upcoming[0] if upcoming else None
