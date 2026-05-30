"""Realtime event envelope broadcast over the /ws WebSocket. camelCase on the wire."""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field

from app.schemas.dashboard import CamelModel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Event(CamelModel):
    """A server -> client realtime event.

    type: 'hello' | 'activity' | 'system_health' | 'workflow' | 'approval'
    payload: type-specific body (e.g. an ActivityItem, a list of HealthMetric, a workflow update).
    """

    type: str
    payload: dict = Field(default_factory=dict)
    ts: str = Field(default_factory=_now_iso)
