"""
CYBER ZONE — Server  (Python L3)

The ONLY place with side-effects: network I/O, async timer, static files.
Business logic lives in core.py and stays 100 % pure.

Run:
    pip install fastapi uvicorn
    python -m club.server
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import core


# ─────────────────────────────────────────────────────────────────
# Mutable "world state" and speed — intentionally kept here, at L3.
# Core only sees these values as inputs to pure functions.
# ─────────────────────────────────────────────────────────────────
STATE: core.World = core.initial_state(seed=42)
SPEED: int        = 1         # simulation minutes per real second
SPEED_OPTIONS     = (1, 2, 5, 10, 20, 60)
CLIENTS: Set[WebSocket] = set()

ROOT = Path(__file__).resolve().parent
WEB  = ROOT


# ─────────────────────────────────────────────────────────────────
# App wiring — simulation loop runs as a background task for the app's lifetime
# ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_simulation_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(lifespan=lifespan)

# Serve CSS and other assets at root level (e.g. /style.css, not /static/style.css)
if WEB.exists():
    app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/")
async def index():
    return FileResponse(WEB / "index.html")


@app.get("/style.css")
async def stylesheet():
    return FileResponse(WEB / "style.css", media_type="text/css")


# ─────────────────────────────────────────────────────────────────
# WebSocket endpoint
# ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    CLIENTS.add(ws)
    # Push initial snapshot immediately so the UI isn't blank
    await _safe_send(ws, _snapshot_payload())
    try:
        while True:
            text = await ws.receive_text()
            try:
                msg = json.loads(text)
            except ValueError:
                continue
            _handle_command(msg)
            # Immediately echo new snapshot so the UI reflects the change
            # without waiting for the next tick.
            await _broadcast(_snapshot_payload())
    except WebSocketDisconnect:
        pass
    finally:
        CLIENTS.discard(ws)


# ─────────────────────────────────────────────────────────────────
# Command handling (L3 -> L2 bridge)
# ─────────────────────────────────────────────────────────────────
def _handle_command(msg: dict) -> None:
    """Apply a user intent. L3 mutates the single STATE reference here."""
    global STATE, SPEED
    action = msg.get("action")

    if action == "speed":
        s = int(msg.get("value", 1))
        if s in SPEED_OPTIONS:
            SPEED = s
        return

    # All other actions are pure reductions over the current state.
    STATE = core.apply_command(STATE, msg)


# ─────────────────────────────────────────────────────────────────
# Simulation loop — advances state 1 sim-minute per iteration.
# Interval = 1 / SPEED real seconds.
# ─────────────────────────────────────────────────────────────────
async def _simulation_loop() -> None:
    global STATE
    while True:
        interval = max(0.016, 1.0 / SPEED)
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return

        if STATE.running and not STATE.paused:
            # Pure transition — no side-effects in core.tick
            STATE = core.tick(STATE)
            await _broadcast(_snapshot_payload())


# ─────────────────────────────────────────────────────────────────
# Broadcast helpers
# ─────────────────────────────────────────────────────────────────
def _snapshot_payload() -> str:
    d = core.world_to_dict(STATE, log_tail=80, chat_tail=80)
    d["speed"]          = SPEED
    d["speed_options"]  = list(SPEED_OPTIONS)
    return json.dumps(d, ensure_ascii=False)


async def _safe_send(ws: WebSocket, data: str) -> None:
    try:
        await ws.send_text(data)
    except Exception:
        CLIENTS.discard(ws)


async def _broadcast(data: str) -> None:
    if not CLIENTS:
        return
    await asyncio.gather(
        *(_safe_send(ws, data) for ws in list(CLIENTS)),
        return_exceptions=True,
    )


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")