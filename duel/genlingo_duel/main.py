"""Duel service (runs on the presenter's laptop).

    uv run uvicorn genlingo_duel.main:create_app --factory --port 8787

The presenter view calls this API; it never talks to Gemini or Ollama directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .arena import Arena
from .audience_feed import AudienceFeed
from .dataset import test_pairs
from .prompts import COUNTRIES, Direction
from .scoreboard import Scoreboard
from .settings import Settings, get_settings

log = logging.getLogger("genlingo.duel")


class DuelRequest(BaseModel):
    phrase: str = Field(min_length=1, max_length=400)
    direction: Direction
    country: str = "LATAM"
    david_tag: str | None = None
    reference: str | None = None
    round_type: Literal["evaluation", "audience"] | None = None
    pair_id: str | None = None
    phrase_id: str | None = None


class EvaluationRequest(BaseModel):
    direction: Direction | None = None
    country: str | None = None
    david_tag: str | None = None


class VotesRequest(BaseModel):
    david: int = Field(ge=0)
    goliath: int = Field(ge=0)


def training_run(settings: Settings, tag: str) -> dict | None:
    """Training cost/duration for a David tag, written by `make train` (train/runs/<tag>.json).
    David's inference is free; his cost is the training run, amortized over the rounds."""
    path = settings.runs_dir / f"{tag}.json"
    if not path.exists():
        return None
    run = json.loads(path.read_text())
    return {k: run.get(k) for k in ("tag", "estimated_cost_usd", "duration_s", "machine", "base_model", "data_date")}


def create_app(settings: Settings | None = None, arena: Arena | None = None, feed: AudienceFeed | None = None) -> FastAPI:
    s = settings or get_settings()
    board = Scoreboard(s.db_path)
    arena = arena or Arena.from_settings(s)
    if feed is None and s.audience_feed:  # also in MOCK_AI rehearsals: models mocked, audience real
        feed = AudienceFeed(board, project=s.project, database=s.firestore_database, event_id=s.event_id)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if feed is not None and feed.scoreboard is board:
            feed.start()
        yield
        if feed is not None:
            feed.stop()

    app = FastAPI(title="Genlingo · duelo", lifespan=lifespan)
    # The presenter view runs on another localhost port.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.state.board, app.state.arena, app.state.feed = board, arena, feed

    def check_country(country: str) -> None:
        if country not in COUNTRIES:
            raise HTTPException(422, f"País no soportado: {country}. Usa uno de {', '.join(COUNTRIES)}.")

    async def run_round(req: DuelRequest) -> dict:
        check_country(req.country)
        round_type = req.round_type or ("evaluation" if req.reference else "audience")
        results = await arena.duel(req.phrase, req.direction, req.country, david_tag=req.david_tag, reference=req.reference)
        rnd = board.record_round(
            round_type=round_type,
            phrase=req.phrase,
            direction=req.direction,
            country=req.country,
            results=results,
            reference=req.reference,
            pair_id=req.pair_id,
            phrase_id=req.phrase_id,
            david_tag=req.david_tag or s.david_tag,
        )
        if feed is not None:
            feed.publish_round(rnd)
            if req.phrase_id:
                feed.mark_shown(req.phrase_id)
        return rnd

    @app.get("/health")
    async def health() -> dict:
        ollama_up = True if s.mock_ai else await arena.david_client.is_up()  # type: ignore[attr-defined]
        return {
            "ok": True,
            "mock": s.mock_ai,
            "online": await arena.is_online(),
            "ollama": ollama_up,
            "david_tag": s.david_tag,
            "david_tags": [t for t in (s.david_tag, s.david_previous_tag) if t],
            "goliath_model": s.gemini_model,
            "event": s.event_id,
            "audience_feed": feed is not None,
            "feed_last_sync": feed.last_sync if feed else None,
        }

    @app.post("/duel")
    async def duel(req: DuelRequest) -> dict:
        return await run_round(req)

    @app.post("/rounds/evaluation")
    async def evaluation_round(req: EvaluationRequest) -> dict:
        """Next unused test-set phrase, with its reference, so chrF++ can be shown live."""
        pool = [
            p
            for p in test_pairs(s.data_dir, include_pending=s.allow_unreviewed_test)
            if p.id not in board.used_pair_ids()
            and (req.direction is None or p.direction == req.direction)
            and (req.country is None or p.country == req.country)
        ]
        if not pool:
            raise HTTPException(404, "No quedan frases de prueba para esa combinación.")
        pair = random.choice(pool)
        return await run_round(
            DuelRequest(
                phrase=pair.source,
                direction=pair.direction,
                country=pair.country,
                reference=pair.target,
                round_type="evaluation",
                pair_id=pair.id,
                david_tag=req.david_tag,
            )
        )

    @app.get("/rounds")
    async def rounds(limit: int = 20) -> list[dict]:
        return board.list_rounds(limit)

    @app.get("/rounds/{round_id}")
    async def get_round(round_id: str) -> dict:
        rnd = board.get_round(round_id)
        if rnd is None:
            raise HTTPException(404, "Ronda no encontrada.")
        return rnd

    @app.post("/rounds/{round_id}/votes")
    async def set_votes(round_id: str, req: VotesRequest) -> dict:
        rnd = board.set_votes(round_id, req.david, req.goliath)
        if rnd is None:
            raise HTTPException(404, "Ronda no encontrada.")
        return rnd

    @app.get("/rounds/{round_id}/votes")
    async def live_votes(round_id: str) -> dict:
        """Live tally while phones vote (read from Firestore); stored tally when offline."""
        rnd = board.get_round(round_id)
        if rnd is None:
            raise HTTPException(404, "Ronda no encontrada.")
        if feed is not None:
            try:
                d, g = await asyncio.to_thread(feed.tally, round_id)
                return {"david": d, "goliath": g, "live": True}
            except Exception:
                pass
        return {"david": rnd["votes_david"], "goliath": rnd["votes_goliath"], "live": False}

    @app.post("/rounds/{round_id}/close")
    async def close_round(round_id: str) -> dict:
        """Close voting: read the tally from Firestore (if connected) and decide the round."""
        if board.get_round(round_id) is None:
            raise HTTPException(404, "Ronda no encontrada.")
        if feed is None:
            return board.get_round(round_id)  # type: ignore[return-value]
        try:
            d, g = feed.tally(round_id)
        except Exception as exc:
            raise HTTPException(503, f"No se pudieron leer los votos: {exc}") from exc
        feed.close_round(round_id)
        return board.set_votes(round_id, d, g)  # type: ignore[return-value]

    @app.get("/scoreboard")
    async def scoreboard(david_tag: str | None = None) -> dict:
        out = board.summary()
        out["david_tag"] = david_tag or s.david_tag
        out["david_training"] = training_run(s, out["david_tag"])
        return out

    @app.get("/queue")
    async def queue() -> list[dict]:
        return board.pending_phrases()

    @app.post("/reset")
    async def reset() -> dict:
        board.reset()
        return {"ok": True}

    return app

