"""Workspace artifact schemas. camelCase on the wire."""
from __future__ import annotations

from app.schemas.dashboard import CamelModel


class Artifact(CamelModel):
    path: str
    category: str
    size_bytes: int
    modified: str
    agent_id: str | None = None


class ArtifactContent(CamelModel):
    path: str
    content: str
