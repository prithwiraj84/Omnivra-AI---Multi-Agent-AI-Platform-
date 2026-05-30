"""Realtime hub: a WebSocket ConnectionManager + a heartbeat producer.

`manager` is the process-wide broadcast hub. Any code can push an event with
`await emit(type, payload)`. The heartbeat loop (started in the app lifespan)
periodically broadcasts jittered system-health metrics and the occasional
simulated activity item so the dashboard feels alive even with no workflow running.
Real workflow runs also emit activity/workflow/approval events (see orchestrator/nodes).
"""
from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING, Any

from app.core.logging import logger
from app.schemas.events import Event

if TYPE_CHECKING:
    from fastapi import WebSocket


class ConnectionManager:
    """Tracks connected WebSocket clients and fans out events to all of them."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)
        logger.info("WS client connected ({} total)", len(self._clients))

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)
        logger.info("WS client disconnected ({} total)", len(self._clients))

    @property
    def count(self) -> int:
        return len(self._clients)

    async def broadcast(self, event: Event) -> None:
        if not self._clients:
            return
        data = event.model_dump(by_alias=True)
        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_json(data)
            except Exception:  # noqa: BLE001 - drop clients that errored
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)


# Process-wide hub.
manager = ConnectionManager()


async def emit(event_type: str, payload: dict[str, Any]) -> None:
    """Broadcast an event to all connected clients (no-op if none)."""
    await manager.broadcast(Event(type=event_type, payload=payload))


# --- Heartbeat producer ----------------------------------------------------
_HEALTH_BASE = [
    ("CPU Usage", 32, "cyan"),
    ("Memory Usage", 58, "blue"),
    ("Storage Usage", 68, "emerald"),
    ("API Quota (OpenRouter)", 89, "amber"),
    ("API Quota (Groq)", 76, "emerald"),
]

_SIM_ACTIVITY = [
    ("Backend Engineer", "Committed service changes", "blue", "Code2"),
    ("Frontend Engineer", "Rebuilt the dashboard", "blue", "LayoutGrid"),
    ("QA Engineer", "Ran the test suite", "emerald", "CheckCircle2"),
    ("SecOps Engineer", "Completed a security scan", "emerald", "ShieldCheck"),
    ("Database Engineer", "Optimized a query", "blue", "Database"),
    ("Documentation Agent", "Updated the docs", "violet", "FileText"),
]


def health_snapshot() -> dict[str, Any]:
    metrics = []
    for label, base, accent in _HEALTH_BASE:
        pct = max(3, min(99, base + random.randint(-6, 6)))
        metrics.append({"label": label, "pct": pct, "display": f"{pct}%", "accent": accent})
    metrics.insert(3, {"label": "Network", "pct": None, "display": "Good", "accent": "emerald"})
    return {"metrics": metrics}


def _sim_activity(seq: int) -> dict[str, Any]:
    agent, action, accent, icon = random.choice(_SIM_ACTIVITY)
    return {"id": f"live-{seq}", "agent": agent, "action": action, "time": "just now", "accent": accent, "icon": icon}


async def heartbeat_loop(stop: asyncio.Event, *, interval: float = 4.0) -> None:
    """Broadcast system-health every tick + a simulated activity every ~3rd tick."""
    seq = 0
    try:
        while not stop.is_set():
            await emit("system_health", health_snapshot())
            seq += 1
            if seq % 3 == 0:
                await emit("activity", _sim_activity(seq))
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:  # pragma: no cover - shutdown path
        pass
