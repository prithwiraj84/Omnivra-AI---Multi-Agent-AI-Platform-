"""Error log — every failure the user actually hits, in one queryable place.

Errors were already being reported honestly, but each in its own silo: provider failures in the
server console, TTS misses in a render note, rate limits in a toast that's gone in seconds. The
user's view of "why did this fail?" shouldn't require reading uvicorn output — so this module
captures WARNING+ records from the ONE funnel everything already flows through (loguru) into a
ring buffer the UI can browse, filter and clear.

Capture is a loguru SINK, not calls sprinkled through the codebase: any `logger.warning` or
`logger.error` anywhere in the app (providers, agents, media, render, publishers, middleware)
lands here automatically, and new code can't forget to report itself. Records are classified
into user-meaningful categories (rate limit vs LLM vs media vs system…) by module + message,
coalesced so a retry storm reads as one row ×N, and scoped to the owner whose request/run
produced them.

Process-local, like usage.py: it resets on restart, which is the correct semantic for
operational telemetry (nothing that happened before a restart is still in flight).
"""
from __future__ import annotations

import asyncio
import itertools
import re
import threading
import time
from collections import Counter, deque
from datetime import datetime, timezone
from typing import Any

from app.services.provider_keys import current_key_owner

_MAX_RECORDS = 500
# Same (owner, category, source, message) arriving within this window bumps a counter instead of
# appending — a provider retry storm or a per-scene TTS fan-out reads as ONE row ×N, not spam.
_COALESCE_SECONDS = 90.0

_lock = threading.Lock()
_records: deque[dict[str, Any]] = deque(maxlen=_MAX_RECORDS)
_ids = itertools.count(1)
_handler_id: int | None = None

# --- classification ------------------------------------------------------------------------
# Category is decided by WHERE the record came from (module) first, then WHAT it says. Message
# checks come second because module names are stable while wording changes.
_RATE_RE = re.compile(r"\b429\b|rate.?limit|quota|too many requests|resource.?exhausted", re.IGNORECASE)
_AUTH_RE = re.compile(r"\b401\b|\b403\b|unauthorized|forbidden|invalid.*(key|token)|expired.*token|paid_plan_required|payment_required|paid plan|\b402\b", re.IGNORECASE)
_NETWORK_RE = re.compile(r"timeout|timed out|connection|unreachable|dns|refused|reset by peer|ssl", re.IGNORECASE)

_MODULE_CATEGORY: tuple[tuple[str, str], ...] = (
    ("app.providers", "llm"),
    ("app.agents", "llm"),
    ("app.services.elevenlabs_tts", "media"),
    ("app.services.google_tts", "media"),
    ("app.services.media", "media"),
    ("app.services.pexels", "media"),
    ("app.services.reel_render", "render"),
    ("app.services.app_runner", "render"),
    ("app.services.code_runner", "render"),
    ("app.services.publishers", "publish"),
    ("app.services.social", "publish"),
    ("app.services.documents", "documents"),
    ("app.services.doc_render", "documents"),
    ("app.api.deps", "auth"),
    ("app.core.security", "auth"),
    ("app.db", "database"),
    ("app.services.secrets_store", "database"),
)

CATEGORIES = ("rate_limit", "llm", "media", "render", "publish", "documents", "auth", "database", "network", "system")


def _classify(module: str, message: str) -> str:
    """One user-meaningful category per record. Rate limits win — they're the most actionable
    (wait / add a key to the pool), whatever subsystem surfaced them."""
    if _RATE_RE.search(message):
        return "rate_limit"
    base = next((cat for prefix, cat in _MODULE_CATEGORY if module.startswith(prefix)), None)
    if base in ("auth",):
        return "auth"
    if _AUTH_RE.search(message):
        return "auth"
    if base:
        return base
    if _NETWORK_RE.search(message):
        return "network"
    return "system"


# --- recording -----------------------------------------------------------------------------


def record(
    level: str,
    message: str,
    *,
    module: str = "",
    source: str = "",
    detail: str = "",
    owner: str | None = None,
) -> dict[str, Any]:
    """Append one error/warning record (coalescing repeats). Returns the stored record."""
    who = owner or _safe_owner()
    category = _classify(module, message)
    now = time.time()
    ts = datetime.now(timezone.utc).isoformat()
    with _lock:
        # Coalesce with the most recent matching record so bursts read as one row ×N.
        for existing in itertools.islice(reversed(_records), 20):
            if (
                existing["owner"] == who
                and existing["category"] == category
                and existing["message"] == message
                and existing["source"] == source
                and now - existing["_mono"] <= _COALESCE_SECONDS
            ):
                existing["count"] += 1
                existing["lastTs"] = ts
                existing["_mono"] = now
                if detail and not existing["detail"]:
                    existing["detail"] = detail
                return existing
        rec = {
            "id": next(_ids),
            "ts": ts,
            "lastTs": ts,
            "level": "error" if level.upper() in ("ERROR", "CRITICAL") else "warning",
            "category": category,
            "source": source or module,
            "message": message[:600],
            "detail": detail[:2000],
            "owner": who,
            "count": 1,
            "_mono": now,
        }
        _records.append(rec)
        return rec


def _safe_owner() -> str:
    try:
        return current_key_owner()
    except Exception:  # noqa: BLE001 - never let telemetry raise
        return "system"


def _emit_async(rec: dict[str, Any]) -> None:
    """Best-effort realtime push. Only possible from a thread that runs an event loop; records
    made from worker threads are picked up by the next poll instead."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    try:
        from app.services.realtime import emit

        loop.create_task(emit("error_log", {"id": rec["id"], "category": rec["category"], "level": rec["level"]}))
    except Exception:  # noqa: BLE001
        pass


# --- the loguru sink -----------------------------------------------------------------------


def _sink(message: Any) -> None:
    """Loguru sink: fold WARNING+ records into the buffer. Must never raise (it runs inside
    logging, so an exception here would swallow the very message being logged)."""
    try:
        r = message.record
        module = r["name"] or ""
        if module.startswith("app.services.error_log"):
            return  # never capture our own diagnostics — that's a feedback loop
        detail = ""
        if r["exception"] is not None:
            exc = r["exception"]
            detail = f"{getattr(exc.type, '__name__', exc.type)}: {exc.value}"
        rec = record(
            r["level"].name,
            str(r["message"]),
            module=module,
            source=f"{module}:{r['function']}:{r['line']}",
            detail=detail,
        )
        _emit_async(rec)
    except Exception:  # noqa: BLE001
        pass


def install() -> None:
    """(Re)attach the capture sink to loguru.

    RE-ENTRANT, not merely idempotent: `configure_logging` starts with `logger.remove()`, which
    silently wipes this sink — a once-only guard would then believe it's installed while
    capturing nothing (exactly the bug the first version had). So install always drops its own
    previous handler (if any survives) and adds a fresh one; called from configure_logging
    itself, the sink survives every logging reconfiguration.
    """
    global _handler_id
    from app.core.logging import logger

    if _handler_id is not None:
        try:
            logger.remove(_handler_id)
        except ValueError:
            pass  # already gone (a logger.remove() beat us to it)
    _handler_id = logger.add(_sink, level="WARNING", enqueue=False)


# --- querying ------------------------------------------------------------------------------


def list_errors(owner: str | None = None, *, limit: int = 200, all_owners: bool = False) -> dict[str, Any]:
    """The newest records (newest first) + per-category counts, scoped to ``owner``.

    ``all_owners`` is the single-admin/open mode: there is only one human, so show everything
    (including records attributed to background/system contexts).
    """
    who = owner or _safe_owner()
    with _lock:
        mine = [r for r in _records if all_owners or r["owner"] == who]
    mine.reverse()  # newest first
    counts = Counter(r["category"] for r in mine)
    items = [{k: v for k, v in r.items() if not k.startswith("_") and k != "owner"} for r in mine[:limit]]
    return {"items": items, "counts": dict(counts), "total": len(mine)}


def clear(owner: str | None = None, *, all_owners: bool = False) -> int:
    """Drop this owner's records (or everything in open mode). Returns how many were removed."""
    who = owner or _safe_owner()
    with _lock:
        if all_owners:
            n = len(_records)
            _records.clear()
            return n
        keep = [r for r in _records if r["owner"] != who]
        n = len(_records) - len(keep)
        _records.clear()
        _records.extend(keep)
        return n


def reset() -> None:
    """Tests only: drop all records (keeps the sink installed)."""
    with _lock:
        _records.clear()
