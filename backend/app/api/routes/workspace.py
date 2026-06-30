"""Workspace routes: list + read the AI-generated artifacts under ./workspace.

Reads go through the path-jailed FileManager (via ArtifactService), so a crafted
path can never escape the sandbox (returns 400).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response

from app.api.deps import get_project_id, require_user
from app.schemas import (
    AppInfo,
    AppRunRequest,
    AppRunStatus,
    AppStopRequest,
    Artifact,
    ArtifactContent,
    RunProgramRequest,
    RunProgramResult,
)
from app.services import app_runner
from app.services.artifacts import get_artifact_service
from app.services.code_runner import run_workspace_file
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


@router.post("/run", response_model=RunProgramResult)
def run_program(req: RunProgramRequest, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> RunProgramResult:
    """Run one generated workspace file in a guarded local subprocess (see services.code_runner).

    Path-jailed + allowlisted interpreter (.py/.js) + hard timeout + captured output + minimal env.
    Never 500s: an escape / unsupported type / timeout returns a result with ok=False and a note.
    """
    return RunProgramResult(**run_workspace_file(req.path, project_id))


# --- Universal app runner (cp-0054): run a WHOLE generated project ----------
@router.get("/app/list", response_model=list[AppInfo])
def list_apps(project_id: str = Depends(get_project_id)) -> list[AppInfo]:
    """One entry per generated app (workflow), de-duplicated across category dirs to its best root —
    so the UI shows a single card per app instead of one per category fragment."""
    return [AppInfo(**a) for a in app_runner.list_apps(project_id)]


@router.post("/app/run", response_model=AppRunStatus)
def run_app(req: AppRunRequest, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> AppRunStatus:
    """Set up (per-app venv + pip install / npm install) and launch a generated project's backend +
    frontend on local ports. Returns immediately; setup/serving run in the background — poll /app/status.
    No Docker, workspace-jailed, localhost-only, never raises.

    Disabled when APP_RUNNER_ENABLED=false (e.g. on a shared host like a Hugging Face Space, where the
    launched app's localhost port isn't reachable and running generated code is a security/AUP risk) —
    you can still browse and Download-as-ZIP; run the app locally instead."""
    from app.core.config import get_settings

    if not get_settings().app_runner_enabled:
        return AppRunStatus(dir=req.dir, targets=[],
                            note="The app runner is disabled in this deployment. Download the ZIP and run it locally.")
    return AppRunStatus(**app_runner.start_app(project_id, req.dir))


@router.get("/app/status", response_model=AppRunStatus)
def app_status(dir: str, project_id: str = Depends(get_project_id)) -> AppRunStatus:
    """Live status + log tail for a generated project's targets (idle when nothing is running yet)."""
    return AppRunStatus(**app_runner.app_status(project_id, dir))


@router.post("/app/stop", response_model=AppRunStatus)
def stop_app(req: AppStopRequest, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> AppRunStatus:
    """Stop a whole project (by dir) or a single target (by runKey) — process-tree kill."""
    if req.run_key:
        app_runner.stop_app(project_id, req.run_key)
        # return the parent dir's aggregate (dir derived from the rel encoded in the key)
        rel = req.run_key.split("::", 1)[-1]
        parent = "/".join(rel.split("/")[:-1]) or rel
        return AppRunStatus(**app_runner.app_status(project_id, req.dir or parent))
    return AppRunStatus(**app_runner.stop_dir(project_id, req.dir or ""))


@router.get("/app/download")
def download_app(dir: str, project_id: str = Depends(get_project_id)) -> Response:
    """Download the generated project as a .zip — only real app files (no .venv/node_modules/caches/
    agent transcripts). Path-jailed. Served like /media (project via ?projectId=) so an <a href>
    download works without an auth header."""
    try:
        filename, data = app_runner.zip_app(project_id, dir)
    except (ValueError, WorkspaceViolationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"No such project dir {dir!r}") from exc
    return Response(
        content=data, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
