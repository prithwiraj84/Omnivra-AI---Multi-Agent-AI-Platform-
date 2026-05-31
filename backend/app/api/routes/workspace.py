"""Workspace routes: list + read the AI-generated artifacts under ./workspace.

Reads go through the path-jailed FileManager (via ArtifactService), so a crafted
path can never escape the sandbox (returns 400).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import get_project_id
from app.schemas import Artifact, ArtifactContent
from app.services.artifacts import get_artifact_service
from app.workspace_fs.file_manager import WorkspaceViolationError

router = APIRouter(tags=["workspace"])


@router.get("/artifacts", response_model=list[Artifact])
def list_artifacts(project_id: str = Depends(get_project_id)) -> list[Artifact]:
    """List the active project's artifacts under the workspace sandbox (newest first)."""
    return get_artifact_service(project_id).list_artifacts()  # type: ignore[return-value]


@router.get("/artifacts/{path:path}", response_model=ArtifactContent)
def read_artifact(path: str, project_id: str = Depends(get_project_id)) -> ArtifactContent:
    """Read one artifact's text content from the active project."""
    try:
        content = get_artifact_service(project_id).read_artifact(path)
    except WorkspaceViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"No artifact {path!r}") from exc
    return ArtifactContent(path=path, content=content)


@router.get("/media/{path:path}")
def read_media(path: str, project_id: str = Depends(get_project_id)) -> FileResponse:
    """Stream a binary artifact (rendered .mp4 / generated image) for inline playback.

    Project is taken from ?projectId= (native <video>/<img> don't send the X-Project-Id
    header). Path-jailed: a crafted path can never escape the sandbox (400).
    """
    try:
        target = get_artifact_service(project_id).fm.media_file(path)
    except WorkspaceViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"No media {path!r}") from exc
    return FileResponse(target)
