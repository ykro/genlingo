"""Measure what the README's projections need: David's throughput on his cloud GPU and both sides'
latency and cost per translation, with the page's exact code path (Arena.translate_one).

    cd duel && uv run python ../scripts/bench_capacity.py [--n 48] [--levels 1,4,8,16]

David must be awake (open the page, or the first request waits for his cold start). For each
concurrency level it sends the same phrases to David, at most that many at a time, and records the
wall time and every latency; Goliath gets the same phrases one at a time (his price is per token, so
concurrency doesn't change his cost) with his token counts. Writes docs/data/capacity.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "duel"))

from genlingo_duel.arena import Arena  # noqa: E402
from genlingo_duel.dataset import read_jsonl  # noqa: E402
from genlingo_duel.settings import get_settings, goliath_prices  # noqa: E402


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(p / 100 * (len(xs) - 1)))]


async def run_level(arena: Arena, phrases: list[dict], level: int, country: str) -> dict:
    sem = asyncio.Semaphore(level)
    lat, errors = [], 0

    async def one(p: dict) -> None:
        nonlocal errors
        async with sem:
            res = await arena.translate_one("david", p["source"], p["direction"], country)
            if res.status == "ok" and res.latency_ms is not None:
                lat.append(res.latency_ms)
            else:
                errors += 1

    t0 = time.perf_counter()
    await asyncio.gather(*(one(p) for p in phrases))
    wall = time.perf_counter() - t0
    return {"concurrency": level, "n": len(phrases), "errors": errors, "wall_s": round(wall, 2),
            "per_hour": round(len(lat) / wall * 3600), "median_ms": round(statistics.median(lat)),
            "p95_ms": round(pct(lat, 95))}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--levels", default="1,4,8,16")
    args = ap.parse_args()
    s = get_settings()
    arena = Arena.from_settings(s)
    rows = [r for r in read_jsonl(ROOT / "data" / "pairs" / "test_web.jsonl") if r["status"] == "auto_validated"]
    phrases = rows[:: max(1, len(rows) // args.n)][: args.n]  # a fixed, evenly spread sample

    # Warm-up (not measured): both models loaded and every code path paid once.
    for p in phrases[:4]:
        await arena.translate_one("david", p["source"], p["direction"], s.country)

    david = [await run_level(arena, phrases, int(c), s.country) for c in args.levels.split(",")]

    price = goliath_prices(s)
    g_lat, g_in, g_out, g_err = [], [], [], 0
    for p in phrases:
        res = await arena.translate_one("goliath", p["source"], p["direction"], s.country)
        if res.status == "ok":
            g_lat.append(res.latency_ms)
            g_in.append(res.input_tokens or 0)
            g_out.append(res.output_tokens or 0)
        else:
            g_err += 1
    tin, tout = statistics.mean(g_in), statistics.mean(g_out)
    goliath = {
        "n": len(phrases), "errors": g_err, "median_ms": round(statistics.median(g_lat)), "p95_ms": round(pct(g_lat, 95)),
        "mean_input_tokens": round(tin, 1), "mean_output_tokens": round(tout, 1),
        "usd_per_translation": {p.effective_from: round((tin * p.input_per_million + tout * p.output_per_million) / 1e6, 7)
                                for p in price.prices},
    }
    out = {
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "david_model": s.david_tag, "goliath_model": s.gemini_model,
        "david_usd_per_hour": round(s.david_usd_per_s * 3600, 4),
        "david": david, "goliath": goliath,
    }
    dest = ROOT / "docs" / "data" / "capacity.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
