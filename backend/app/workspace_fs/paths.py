"""Per-project workspace paths, migration, and cache eviction.

Each project owns an isolated subtree under ``workspace/projects/<project_id>/``:
artifacts (docs/frontend/backend/presentations/reports), its RAG memory + knowledge
vector stores (``.state/vectors``), its workflow run records (``.state/workflows``),
and agent-run checkpoints (``.checkpoints``). The project catalog itself
(``workspace/.state/projects.json`` + ``tasks.json``) and the build checkpoint
lineage (``workspace/.state/checkpoints``) stay GLOBAL.

This module is the single source of truth for resolving a project's root (and for
rejecting any ``project_id`` that could escape the ``projects/`` directory — the
per-project arm of the WORKSPACE RULE). It also performs a one-time migration of
the original flat layout into the ``__default__`` project.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import logger

# The fallback project that holds runs with no explicit project_id and the
# migrated legacy (pre-partition) artifacts. Always present in the catalog.
DEFAULT_PROJECT = "__default__"

_PROJECTS_DIRNAME = "projects"
_MIGRATION_MARKER = ".migrated_v2_projects"
# Legacy flat locations migrated into projects/__default__/ on first startup.
_LEGACY_TOP = ("frontend", "backend", "docs", "presentations", "reports")
_LEGACY_STATE = ("vectors", "workflows", "artifacts")


def safe_project_id(project_id: str | None) -> str:
    """Validate a project_id for use as a directory name; map blank/None to default.

    Rejects anything that could traverse out of ``workspace/projects/`` (separators,
    NUL, ``..``). This is the per-project path jail.
    """
    pid = (project_id or "").strip()
    if not pid:
        return DEFAULT_PROJECT
    if any(c in pid for c in ("/", "\\", "\x00")) or ".." in pid:
        raise ValueError(f"Invalid project_id: {project_id!r}")
    return pid


def projects_dir() -> Path:
    return get_settings().workspace_path / _PROJECTS_DIRNAME


def project_root(project_id: str | None = None) -> Path:
    """Absolute root for one project's isolated workspace subtree (jailed)."""
    return projects_dir() / safe_project_id(project_id)


def list_project_dir_ids() -> list[str]:
    """Project ids that actually have a workspace dir on disk (+ the default)."""
    base = projects_dir()
    ids = [p.name for p in base.iterdir() if p.is_dir()] if base.exists() else []
    if DEFAULT_PROJECT not in ids:
        ids.append(DEFAULT_PROJECT)
    return ids


def reset_caches() -> None:
    """Drop cached per-project store instances (after delete/migrate so no stale state)."""
    # Lazy imports avoid an import cycle (these modules import this one).
    from app.services.artifacts import get_artifact_service
    from app.services.knowledge import get_knowledge_service
    from app.services.memory import get_memory_service
    from app.services.workflow_store import get_workflow_store

    for factory in (get_artifact_service, get_memory_service, get_knowledge_service, get_workflow_store):
        factory.cache_clear()


def purge_project_workspace(project_id: str) -> bool:
    """Hard-delete a project's entire workspace subtree. Returns True if anything was removed.

    Jailed: refuses to remove anything that is not a direct child of ``workspace/projects/``.
    """
    root = project_root(project_id)  # validates project_id
    base = projects_dir()
    if root.parent != base or root == base:
        raise ValueError(f"Refusing to purge path outside projects dir: {root}")
    if root.exists() and root.is_dir():
        shutil.rmtree(root)
        logger.info("Purged workspace for project {}", project_id)
        reset_caches()
        return True
    return False


def _merge_move(src: Path, dst: Path) -> bool:
    """Move every child of ``src`` into ``dst`` (merging existing dirs); remove empty ``src``."""
    dst.mkdir(parents=True, exist_ok=True)
    moved = False
    for child in list(src.iterdir()):
        target = dst / child.name
        if target.exists():
            if child.is_dir():
                moved = _merge_move(child, target) or moved
            # an existing file means it was already migrated — leave it
        else:
            shutil.move(str(child), str(target))
            moved = True
    try:
        if not any(src.iterdir()):
            src.rmdir()
    except OSError:  # pragma: no cover - non-empty after a merge skip
        pass
    return moved


def migrate_flat_workspace(ws: Path | None = None) -> bool:
    """One-time migration of the original flat layout into projects/__default__/.

    Moves the legacy artifact subdirs + per-run state into the default project,
    leaving the global catalog (projects.json/tasks.json), the build checkpoint
    lineage (.state/checkpoints), and the workspace READMEs in place. Idempotent
    via a marker file. No-op (returns False) once migrated or on a fresh install.

    ``ws`` defaults to the configured workspace root; it is parameterised so the
    migration can be unit-tested against a synthetic flat layout in a temp dir.
    """
    ws = ws or get_settings().workspace_path
    state = ws / ".state"
    marker = state / _MIGRATION_MARKER
    if marker.exists():
        return False

    dest = ws / _PROJECTS_DIRNAME / DEFAULT_PROJECT
    moved_any = False
    for sub in _LEGACY_TOP:
        src = ws / sub
        if src.is_dir() and any(src.iterdir()):
            moved_any = _merge_move(src, dest / sub) or moved_any
    for sub in _LEGACY_STATE:
        src = state / sub
        if src.is_dir() and any(src.iterdir()):
            moved_any = _merge_move(src, dest / ".state" / sub) or moved_any
    src_ckpt = ws / ".checkpoints"
    if src_ckpt.is_dir() and any(src_ckpt.iterdir()):
        moved_any = _merge_move(src_ckpt, dest / ".checkpoints") or moved_any

    state.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps({"migratedAt": datetime.now(timezone.utc).isoformat(), "into": DEFAULT_PROJECT, "movedData": moved_any}),
        encoding="utf-8",
    )
    if moved_any:
        reset_caches()
        logger.info("Migrated legacy flat workspace into project '{}'", DEFAULT_PROJECT)
    return moved_any
