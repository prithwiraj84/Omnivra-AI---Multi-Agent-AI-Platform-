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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_SEED_PROJECTS = [
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

    # --- Projects ---
    def list_projects(self) -> list[dict[str, Any]]:
        out = []
        for p in self._projects:
            out.append({**p, "task_count": sum(1 for t in self._tasks if t.get("project_id") == p["id"])})
        return out

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        for p in self.list_projects():
            if p["id"] == project_id:
                return p
        return None

    def create_project(self, name: str, description: str = "") -> dict[str, Any]:
        proj = {"id": "proj-" + uuid4().hex[:8], "name": name, "description": description, "status": "active", "created_at": _now()}
        with self._lock:
            self._projects.append(proj)
            self._save_projects()
        return {**proj, "task_count": 0}

    def delete_project(self, project_id: str) -> bool:
        with self._lock:
            before = len(self._projects)
            self._projects = [p for p in self._projects if p["id"] != project_id]
            self._tasks = [t for t in self._tasks if t.get("project_id") != project_id]
            if len(self._projects) != before:
                self._save_projects()
                self._save_tasks()
                return True
            return False

    # --- Tasks ---
    def list_tasks(self, *, project_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        return [
            t for t in self._tasks
            if (project_id is None or t.get("project_id") == project_id) and (status is None or t.get("status") == status)
        ]

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return next((t for t in self._tasks if t["id"] == task_id), None)

    def create_task(self, title: str, *, project_id: str | None = None, priority: str = "medium", agent_id: str | None = None) -> dict[str, Any]:
        task = {"id": "task-" + uuid4().hex[:8], "title": title, "project_id": project_id, "status": "todo", "priority": priority, "agent_id": agent_id, "created_at": _now()}
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
