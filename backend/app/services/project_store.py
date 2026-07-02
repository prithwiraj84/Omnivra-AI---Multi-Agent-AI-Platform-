"""ProjectStore — projects + tasks, persisted under workspace/.state (offline-first).

Seeds a few demo projects/tasks on first run so the Projects/Tasks views look alive.
JSON-backed (no DB needed); swappable for Supabase tables when configured.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import get_settings
from app.core.logging import logger
from app.workspace_fs.paths import DEFAULT_PROJECT, purge_project_workspace


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# The default bucket: holds unfiled runs + migrated legacy artifacts. Never deletable.
_DEFAULT_PROJECT_SEED = {
    "id": DEFAULT_PROJECT,
    "name": "Default Workspace",
    "description": "Unfiled workflow runs and migrated (pre-partition) artifacts.",
    "status": "active",
    "created_at": _now(),
}

_SEED_PROJECTS = [
    dict(_DEFAULT_PROJECT_SEED),
    {"id": "proj-dashboard", "name": "AI Company OS Dashboard", "description": "The Omnivra command center.", "status": "active", "created_at": _now()},
    {"id": "proj-instagram", "name": "Instagram Campaign", "description": "Launch social campaign across reels + posts.", "status": "active", "created_at": _now()},
    {"id": "proj-pitch", "name": "Investor Pitch Deck", "description": "Seed-round investor presentation.", "status": "active", "created_at": _now()},
]

_SEED_TASKS = [
    {"id": "task-1", "title": "Build the dashboard layout shell", "project_id": "proj-dashboard", "status": "done", "priority": "high", "agent_id": "frontend-engineer", "created_at": _now()},
    {"id": "task-2", "title": "Wire the REST API + repositories", "project_id": "proj-dashboard", "status": "in_progress", "priority": "high", "agent_id": "backend-engineer", "created_at": _now()},
    {"id": "task-3", "title": "Design the agent hierarchy view", "project_id": "proj-dashboard", "status": "review", "priority": "medium", "agent_id": "uiux-designer", "created_at": _now()},
    {"id": "task-4", "title": "Draft 8 reel scripts", "project_id": "proj-instagram", "status": "in_progress", "priority": "medium", "agent_id": "reel-automation", "created_at": _now()},
    {"id": "task-5", "title": "Keyword + competitor research", "project_id": "proj-instagram", "status": "done", "priority": "medium", "agent_id": "seo-researcher", "created_at": _now()},
    {"id": "task-6", "title": "Write the 12-slide investor deck", "project_id": "proj-pitch", "status": "todo", "priority": "high", "agent_id": "presentation-designer", "created_at": _now()},
    {"id": "task-7", "title": "Security audit before launch", "project_id": "proj-dashboard", "status": "todo", "priority": "high", "agent_id": "secops-engineer", "created_at": _now()},
]


class ProjectStore:
    def __init__(self, root: str | Path) -> None:
        base = Path(root) / ".state"
        base.mkdir(parents=True, exist_ok=True)
        self._projects_path = base / "projects.json"
        self._tasks_path = base / "tasks.json"
        self._lock = threading.RLock()  # guard read-modify-write (sync routes run in a threadpool)
        self._projects: list[dict[str, Any]] = self._load(self._projects_path, _SEED_PROJECTS)
        self._tasks: list[dict[str, Any]] = self._load(self._tasks_path, _SEED_TASKS)
        self._ensure_default()

    def _ensure_default(self) -> None:
        """Guarantee the Default Workspace project always exists (even for older catalogs)."""
        if not any(p.get("id") == DEFAULT_PROJECT for p in self._projects):
            self._projects.insert(0, dict(_DEFAULT_PROJECT_SEED))
            self._save_projects()

    @staticmethod
    def _load(path: Path, seed: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if path.exists():
            try:
                return __import__("json").loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                return list(seed)
        data = list(seed)
        path.write_text(__import__("json").dumps(data, indent=2), encoding="utf-8")
        return data

    def _save_projects(self) -> None:
        self._projects_path.write_text(__import__("json").dumps(self._projects, indent=2), encoding="utf-8")

    def _save_tasks(self) -> None:
        self._tasks_path.write_text(__import__("json").dumps(self._tasks, indent=2), encoding="utf-8")

    # --- Ownership (per-user isolation) ---
    @staticmethod
    def _admin_id() -> str:
        return get_settings().admin_username

    def _owner_of(self, proj: dict[str, Any]) -> str:
        """A project's owner. Legacy projects (no owner_id) belong to the admin, so in open
        mode the admin sees everything and in per-user mode they're hidden from real users."""
        return proj.get("owner_id") or self._admin_id()

    def owns(self, project_id: str, owner_id: str) -> bool:
        proj = next((p for p in self._projects if p["id"] == project_id), None)
        return proj is not None and self._owner_of(proj) == owner_id

    # --- Projects ---
    def list_projects(self, *, owner_id: str | None = None) -> list[dict[str, Any]]:
        """All projects (owner_id=None) or only those owned by `owner_id`, with task counts."""
        out = []
        for p in self._projects:
            if owner_id is not None and self._owner_of(p) != owner_id:
                continue
            out.append({**p, "task_count": sum(1 for t in self._tasks if t.get("project_id") == p["id"])})
        return out

    def get_project(self, project_id: str, *, owner_id: str | None = None) -> dict[str, Any] | None:
        for p in self._projects:
            if p["id"] == project_id:
                if owner_id is not None and self._owner_of(p) != owner_id:
                    return None
                return {**p, "task_count": sum(1 for t in self._tasks if t.get("project_id") == p["id"])}
        return None

    def create_project(self, name: str, description: str = "", *, owner_id: str | None = None) -> dict[str, Any]:
        proj: dict[str, Any] = {"id": "proj-" + uuid4().hex[:8], "name": name, "description": description, "status": "active", "created_at": _now()}
        if owner_id is not None:
            proj["owner_id"] = owner_id
        with self._lock:
            self._projects.append(proj)
            self._save_projects()
        return {**proj, "task_count": 0}

    def ensure_user_default(self, owner_id: str) -> str:
        """The id of `owner_id`'s Default Workspace, creating it on first use.

        The admin's default is the legacy shared DEFAULT_PROJECT (so open mode is unchanged);
        every other user gets their own private default bucket."""
        if owner_id == self._admin_id():
            return DEFAULT_PROJECT
        with self._lock:
            for p in self._projects:
                if p.get("owner_id") == owner_id and p.get("is_default"):
                    return str(p["id"])
            pid = "default-" + uuid4().hex[:8]
            self._projects.append({
                "id": pid, "name": "Default Workspace", "description": "Your unfiled workflow runs.",
                "status": "active", "created_at": _now(), "owner_id": owner_id, "is_default": True,
            })
            self._save_projects()
            return pid

    def delete_project(self, project_id: str, *, owner_id: str | None = None) -> bool:
        """Remove a project from the catalog AND hard-delete its workspace subtree.

        The Default Workspace is never deletable, and a non-owner can't delete another user's
        project. The filesystem cascade runs after the catalog write so a purge failure can't
        leave a half-deleted catalog.
        """
        if project_id == DEFAULT_PROJECT:
            return False
        with self._lock:
            proj = next((p for p in self._projects if p["id"] == project_id), None)
            if proj is None:
                return False
            if proj.get("is_default"):
                return False  # a user's own Default Workspace isn't deletable either
            if owner_id is not None and self._owner_of(proj) != owner_id:
                return False
            self._projects = [p for p in self._projects if p["id"] != project_id]
            self._tasks = [t for t in self._tasks if t.get("project_id") != project_id]
            self._save_projects()
            self._save_tasks()
        try:  # cascade: wipe the project's entire workspace subtree + evict caches
            purge_project_workspace(project_id)
        except Exception as exc:  # noqa: BLE001 - never let FS cleanup break the catalog delete
            logger.warning("Workspace purge failed for project {}: {}", project_id, exc)
        return True

    # --- Tasks ---
    def list_tasks(
        self, *, project_id: str | None = None, status: str | None = None, owner_id: str | None = None
    ) -> list[dict[str, Any]]:
        owned: set[str] | None = None
        if owner_id is not None:
            owned = {p["id"] for p in self.list_projects(owner_id=owner_id)}
        return [
            t for t in self._tasks
            if (project_id is None or t.get("project_id") == project_id)
            and (status is None or t.get("status") == status)
            and (owned is None or t.get("project_id") in owned)
        ]

    def task_owned_by(self, task_id: str, owner_id: str) -> bool:
        """True when `task_id` exists and belongs to a project `owner_id` owns."""
        task = self.get_task(task_id)
        if task is None:
            return False
        pid = task.get("project_id")
        return pid is not None and self.owns(pid, owner_id)

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return next((t for t in self._tasks if t["id"] == task_id), None)

    def find_task_by_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """The task auto-created for a CEO run (linked by workflow_id), if any."""
        return next((t for t in self._tasks if t.get("workflow_id") == workflow_id), None)

    def create_task(
        self, title: str, *, project_id: str | None = None, priority: str = "medium",
        agent_id: str | None = None, status: str = "todo", workflow_id: str | None = None,
    ) -> dict[str, Any]:
        task: dict[str, Any] = {
            "id": "task-" + uuid4().hex[:8], "title": title, "project_id": project_id,
            "status": status, "priority": priority, "agent_id": agent_id, "created_at": _now(),
        }
        if workflow_id:  # link to a CEO workflow run so its status can track the run
            task["workflow_id"] = workflow_id
        with self._lock:
            self._tasks.append(task)
            self._save_tasks()
        return task

    def update_task(self, task_id: str, **fields: Any) -> dict[str, Any] | None:
        with self._lock:
            task = self.get_task(task_id)
            if task is None:
                return None
            for k, v in fields.items():
                if v is not None:
                    task[k] = v
            self._save_tasks()
            return task

    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            before = len(self._tasks)
            self._tasks = [t for t in self._tasks if t["id"] != task_id]
            if len(self._tasks) != before:
                self._save_tasks()
                return True
            return False


@lru_cache(maxsize=1)
def get_project_store() -> ProjectStore:
    return ProjectStore(get_settings().workspace_path)
