"""The comparison page on Cloud Run: David and Goliath translate Gen Z ↔ papás side by side.

    uv run uvicorn genlingo_duel.main:create_app --factory --port 8080

The browser only talks to this service. It calls David (a private Cloud Run GPU service, with an ID
token) and Goliath (Gemini on Vertex AI) and returns each answer as soon as it arrives. David scales
to zero between talks: opening the page wakes him (`/api/david/wake`), and the page keeps him warm
while it stays open.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .arena import Arena
from .prompts import Direction
from .settings import Settings, get_settings
from .translate_page import FONTS, PAGE, check_terms, find_example, load_examples

log = logging.getLogger("genlingo.page")

# Cloud Run stops an idle instance after about 15 minutes; past this we assume David is cold again.
IDLE_COLD_S = 10 * 60
# Right after a model load the first few generations on the GPU are slow (seconds, not half a second):
# one throwaway translation per direction during the wake-up absorbs that before anyone is watching.
WARM_PHRASES = {"genz_to_parent": "qué onda, ese plan estuvo bien chilero", "parent_to_genz": "qué pena con los vecinos"}


class TranslateRequest(BaseModel):
    phrase: str = Field(min_length=1, max_length=400)
    direction: Direction
    # An example button: the answer also carries the ✓/✗ per slang term (translate_page.py).
    example_id: str | None = Field(default=None, max_length=40)


class DavidState:
    """Whether David's GPU instance is up with his models loaded, as far as this instance knows."""

    def __init__(self) -> None:
        self.phase: Literal["idle", "waking", "ready", "error"] = "idle"
        self.since = time.time()
        self.last_seen = 0.0  # last time David answered anything
        self.error: str | None = None
        self.task: asyncio.Task | None = None

    def set(self, phase, error: str | None = None) -> None:
        self.phase, self.since, self.error = phase, time.time(), error

    def seen(self) -> None:
        self.last_seen = time.time()

    def view(self) -> dict:
        if self.phase == "ready" and time.time() - self.last_seen > IDLE_COLD_S:
            self.set("idle")
        return {"phase": self.phase, "seconds": round(time.time() - self.since, 1), "error": self.error}


def create_app(settings: Settings | None = None, arena: Arena | None = None) -> FastAPI:
    s = settings or get_settings()
    arena = arena or Arena.from_settings(s)
    david = DavidState()
    if s.mock_ai:
        david.set("ready")
        david.seen()

    app = FastAPI(title="Genlingo · David contra Goliath", docs_url=None, redoc_url=None)
    app.state.arena, app.state.david = arena, david

    async def wake() -> None:
        """Start David's instance (the first request waits for it) and load both models."""
        client = arena.david_client
        try:
            loaded = await client.loaded_models(timeout_s=600)  # type: ignore[attr-defined]
            if s.david_tag not in loaded:
                await client.warm_up(s.david_tag)  # type: ignore[attr-defined]
            if s.embedding_model and s.embedding_model not in loaded:
                await client.warm_up_embedding(s.embedding_model)  # type: ignore[attr-defined]
            await arena.get_glossary()
            if s.david_tag not in loaded:  # a fresh load: run the throwaway translations
                for direction, phrase in WARM_PHRASES.items():
                    await arena.translate_one("david", phrase, direction, s.country)
            david.seen()
            david.set("ready")
        except Exception as exc:
            log.warning("David did not wake: %s", exc)
            david.set("error", f"{type(exc).__name__}: {str(exc)[:160]}")

    async def keep_warm() -> None:
        try:
            loaded = await arena.david_client.loaded_models(timeout_s=30)  # type: ignore[attr-defined]
            if s.david_tag in loaded:
                david.seen()
            else:
                david.set("waking")
                await wake()
        except Exception as exc:
            log.warning("keep-warm ping failed: %s", exc)

    @app.get("/", response_class=HTMLResponse)
    async def page() -> str:
        return PAGE.read_text(encoding="utf-8")

    @app.get("/fonts/{name}")
    async def font(name: str) -> FileResponse:
        if name not in FONTS or not FONTS[name].exists():
            raise HTTPException(404, "No existe.")
        return FileResponse(FONTS[name], media_type="font/woff2", headers={"Cache-Control": "max-age=86400"})

    @app.get("/api/examples")
    async def examples() -> list[dict]:
        return load_examples(s.data_dir)

    @app.get("/api/status")
    async def status() -> dict:
        return {"david": david.view(), "david_model": s.david_tag, "goliath_model": s.gemini_model}

    @app.post("/api/david/wake")
    async def david_wake() -> dict:
        """Called by the page when it opens and every minute while it is open: wakes David if he is
        cold (the request stays open until he is ready, so this instance keeps its CPU meanwhile),
        otherwise a cheap ping that keeps his instance alive. Concurrent calls share one wake-up."""
        if s.mock_ai:
            return david.view()
        if not (david.task and not david.task.done()):
            if david.view()["phase"] in ("idle", "error"):
                david.set("waking")
                david.task = asyncio.create_task(wake())
            else:
                david.task = asyncio.create_task(keep_warm())
        await asyncio.shield(david.task)
        return david.view()

    @app.post("/api/translate/{side}")
    async def translate(req: TranslateRequest, side: Literal["david", "goliath"]) -> dict:
        """One side's translation (the page asks both at once): no score, nothing recorded."""
        res = await arena.translate_one(side, req.phrase.strip(), req.direction, s.country)
        if side == "david" and res.status == "ok":
            david.seen()
            if david.phase != "ready":
                david.set("ready")
        if res.status != "ok":
            log.warning("%s did not answer: %s", side, res.error)
        out = {"status": res.status, "text": res.text, "latency_ms": res.latency_ms, "cost_usd": res.cost_usd, "model": res.model,
               "error": res.error}
        example = find_example(s.data_dir, req.example_id)
        if example and example["text"] == req.phrase.strip() and res.status == "ok":
            out["terms"] = check_terms(s.data_dir, example, s.country, res.text)
        return out

    @app.get("/api/health")
    async def health() -> dict:
        return {"ok": True}

    return app
