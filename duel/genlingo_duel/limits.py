"""Spending limits for the public page: it is open to anyone with the URL, and each translation costs
money (Gemini bills by token; waking David starts a GPU that bills by the second).

- Per visitor (IP address): at most `translate_per_min` translation calls (each phrase is two: one per
  side) and `wake_per_min` wake/keep-alive calls per minute.
- Per day, for the whole page: at most `gemini_per_day` calls to Gemini and `wakes_per_day` starts of
  David's GPU (a keep-alive ping on a running David doesn't count).

A talk uses a few dozen phrases and one or two starts, so the presenter never gets near these numbers;
they only stop a script or a bot from running up the bill. Limits are kept in memory per page instance
(Cloud Run runs at most 3), so the daily caps are per instance: the real ceiling is 3× each one.
When a limit is reached the API answers 429 with a plain-Spanish message the page shows as is.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import date

from fastapi import HTTPException, Request

MESSAGES = {
    "translate": "Demasiadas traducciones seguidas desde esta conexión. Espera un minuto y vuelve a intentar.",
    "wake": "Demasiadas solicitudes seguidas desde esta conexión. Espera un minuto.",
    "gemini": "La demo llegó a su límite diario de traducciones con Gemini. Vuelve mañana.",
    "wake_day": "La demo llegó a su límite diario de encendidos de David. Vuelve mañana.",
}


@dataclass
class Limits:
    translate_per_min: int = 60
    wake_per_min: int = 12
    gemini_per_day: int = 1500
    wakes_per_day: int = 24
    _hits: dict = field(default_factory=lambda: defaultdict(deque))
    _day: str = ""
    _daily: dict = field(default_factory=lambda: defaultdict(int))

    @classmethod
    def from_settings(cls, s) -> "Limits":
        return cls(s.limit_translate_per_min, s.limit_wake_per_min, s.limit_gemini_per_day, s.limit_wakes_per_day)

    @staticmethod
    def client_ip(request: Request) -> str:
        # Cloud Run puts the visitor's address first in X-Forwarded-For.
        fwd = request.headers.get("x-forwarded-for", "")
        return fwd.split(",")[0].strip() or (request.client.host if request.client else "?")

    def check_ip(self, request: Request, kind: str) -> None:
        limit = self.translate_per_min if kind == "translate" else self.wake_per_min
        q = self._hits[(kind, self.client_ip(request))]
        now = time.monotonic()
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, MESSAGES[kind])
        q.append(now)
        if len(self._hits) > 10_000:  # forget visitors idle for a minute, so memory stays small
            for key in [k for k, v in self._hits.items() if not v or now - v[-1] > 60]:
                del self._hits[key]

    def count_daily(self, kind: str) -> None:
        today = date.today().isoformat()
        if today != self._day:
            self._day, self._daily = today, defaultdict(int)
        cap = self.gemini_per_day if kind == "gemini" else self.wakes_per_day
        if self._daily[kind] >= cap:
            raise HTTPException(429, MESSAGES["gemini" if kind == "gemini" else "wake_day"])
        self._daily[kind] += 1
