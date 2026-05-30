"""FastAPI application entrypoint for Omnivra AI Company OS.

Run (from backend/):
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import contextlib
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.agents.registry import AGENT_REGISTRY
from app.core.config import get_settings
from app.core.logging import configure_logging, logger
from app.schemas.events import Event
from app.services.realtime import health_snapshot, heartbeat_loop, manager
from app.workspace_fs.file_manager import FileManager

settings = get_settings()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown. Initialise logging, workspace sandbox, and shared clients.

    Phase 1: logging + workspace sandbox only. Provider clients, Supabase, and
    Redis are wired here in later phases (see manifest) and stashed on app.state.
    """
    configure_logging(settings)
    logger.info("Starting {} v{} ({})", settings.app_name, __version__, settings.app_env)

    # Ensure the AI artifact sandbox exists. Agents may ONLY write under here.
    file_manager = FileManager(settings.workspace_root)
    file_manager.ensure_layout()
    app.state.file_manager = file_manager
    app.state.settings = settings
    logger.info("Workspace sandbox ready at {}", file_manager.root)
    logger.info("Agent registry loaded: {} agents", len(AGENT_REGISTRY))

    # Realtime heartbeat: broadcasts live system-health + simulated activity over /ws.
    stop_event = asyncio.Event()
    app.state.realtime_stop = stop_event
    app.state.realtime_task = asyncio.create_task(heartbeat_loop(stop_event))
    logger.info("Realtime heartbeat started")
    yield

    logger.info("Shutting down {}", settings.app_name)
    stop_event.set()
    app.state.realtime_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await app.state.realtime_task


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-client request timestamps for the opt-in rate limiter (in-memory; per process).
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def hardening_middleware(request: Request, call_next):
    """Opt-in per-IP rate limiting + always-on security response headers."""
    if settings.rate_limit_enabled:
        client = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _rate_buckets[client]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again shortly."})
        bucket.append(now)

    response = await call_next(request)

    if settings.security_headers_enabled:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return response


@app.get("/health", tags=["system"])
async def health() -> dict[str, object]:
    """Liveness probe + lightweight system summary for the dashboard header."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
        "agents": len(AGENT_REGISTRY),
    }


# --- API router include ----------------------------------------------------
# Phase 2: from app.api.router import api_router ; app.include_router(api_router, prefix="/api")
try:  # keep the skeleton runnable before routes exist
    from app.api.router import api_router

    app.include_router(api_router, prefix="/api")
except ImportError:  # pragma: no cover - Phase 1 placeholder
    logger.warning("app.api.router not present yet (Phase 2). Serving /health only.")


# --- WebSocket: realtime hub (live activity feed, workflow progress, health) ---
@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    """Realtime channel. The server pushes 'activity', 'system_health', 'workflow',
    and 'approval' events via the ConnectionManager (see app.services.realtime).
    Inbound messages are ignored for now (client->server commands arrive in Phase 7).
    """
    await manager.connect(websocket)
    await websocket.send_json(
        Event(type="hello", payload={"app": settings.app_name, "clients": manager.count}).model_dump(by_alias=True)
    )
    # Push an immediate health snapshot so the client renders live data without waiting a tick.
    await websocket.send_json(Event(type="system_health", payload=health_snapshot()).model_dump(by_alias=True))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
