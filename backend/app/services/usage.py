"""In-memory provider / model / media usage counters (cp-0022).

Best-effort, process-local (resets on restart): every agent run records a call,
so the dashboard shows REAL session usage instead of fabricated numbers. Thread-safe.
"""
from __future__ import annotations

import threading
from collections import Counter

_lock = threading.Lock()
_provider_calls: Counter = Counter()
_model_calls: Counter = Counter()
_media_calls: Counter = Counter()


def record_agent_call(provider: str | None, model: str | None) -> None:
    with _lock:
        if provider:
            _provider_calls[provider] += 1
        if model:
            _model_calls[model] += 1


def record_media_call(kind: str) -> None:
    """kind: 'image' | 'tts' | 'stt'."""
    with _lock:
        _media_calls[kind] += 1


def snapshot() -> dict:
    with _lock:
        return {
            "providers": dict(_provider_calls),
            "models": dict(_model_calls),
            "media": dict(_media_calls),
            "total": int(sum(_provider_calls.values())),
        }
