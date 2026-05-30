"""Workspace routes: list + read the AI-generated artifacts under ./workspace.

Reads go through the path-jailed FileManager (via ArtifactService), so a crafted
path can never escape the sandbox (returns 400).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import Artifact, ArtifactContent
from app.services.artifacts import get_artifact_service
from app.workspace_fs.file_manager import WorkspaceViolationError

router = APIRouter(tags=["workspace"])


@router.get("/artifacts", response_model=list[Artifact])
def list_artifacts() -> list[Artifact]:
    """List every artifact agents have written under the workspace sandbox (newest first)."""
    return get_artifact_service().list_artifacts()  # type: ignore[return-value]


@router.get("/artifacts/{path:path}", response_model=ArtifactContent)
def read_artifact(path: str) -> ArtifactContent:
    """Read one artifact's text content."""
    try:
        content = get_artifact_service().read_artifact(path)
    except WorkspaceViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"No artifact {path!r}") from exc
    return ArtifactContent(path=path, content=content)
