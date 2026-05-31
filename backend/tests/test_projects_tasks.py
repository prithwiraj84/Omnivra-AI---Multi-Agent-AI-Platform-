"""Projects + Tasks API contract tests.

Exercises the full CRUD surface for ``/api/projects`` and ``/api/tasks`` against
the conftest ``client`` fixture (its temp ``WORKSPACE_ROOT`` isolates the JSON
store from the real sandbox). Assertions lean on the *seeded ids* plus the ids
this module creates itself, rather than assuming a pristine global count, so the
suite stays robust even if other modules mutate the store.
"""
from __future__ import annotations

from typing import Any

SEEDED_PROJECT_IDS = {"proj-dashboard", "proj-instagram", "proj-pitch"}
# The always-present Default Workspace (holds unfiled runs + migrated artifacts).
DEFAULT_PROJECT_ID = "__default__"


def test_list_projects_returns_seed_with_camelcase_task_count(client: Any) -> None:
    res = client.get("/api/projects")
    assert res.status_code == 200
    projects = res.json()
    assert isinstance(projects, list)
    # 3 demo projects + the Default Workspace bucket (>= because other tests in the
    # session may create projects against the shared store).
    assert len(projects) >= 4

    by_id = {p["id"]: p for p in projects}
    assert SEEDED_PROJECT_IDS.issubset(by_id)
    assert DEFAULT_PROJECT_ID in by_id, "the Default Workspace must always exist"
    for proj in projects:
        # camelCase on the wire (not snake_case task_count)
        assert "taskCount" in proj
        assert "task_count" not in proj
    assert by_id["proj-dashboard"]["taskCount"] == 4


def test_list_tasks_filtered_by_project_uses_camelcase(client: Any) -> None:
    res = client.get("/api/tasks", params={"projectId": "proj-dashboard"})
    assert res.status_code == 200
    tasks = res.json()
    assert isinstance(tasks, list)
    assert len(tasks) == 4
    for task in tasks:
        assert task["projectId"] == "proj-dashboard"
        # camelCase keys present, snake_case absent
        assert "agentId" in task and "agent_id" not in task
        assert "createdAt" in task and "created_at" not in task
        assert "project_id" not in task


def test_project_and_task_lifecycle(client: Any) -> None:
    # --- create a project ---
    created = client.post("/api/projects", json={"name": "QA Project"})
    assert created.status_code == 200
    project = created.json()
    project_id = project["id"]
    assert project_id
    assert project["name"] == "QA Project"
    assert project["taskCount"] == 0

    # --- create a task in that project ---
    made = client.post(
        "/api/tasks",
        json={"title": "t1", "projectId": project_id, "priority": "high"},
    )
    assert made.status_code == 200
    task = made.json()
    task_id = task["id"]
    assert task_id
    assert task["title"] == "t1"
    assert task["projectId"] == project_id
    assert task["priority"] == "high"
    assert task["status"] == "todo"

    # --- patch the task to done ---
    patched = client.patch(f"/api/tasks/{task_id}", json={"status": "done"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "done"

    # --- delete the task ---
    del_task = client.delete(f"/api/tasks/{task_id}")
    assert del_task.status_code == 200
    assert del_task.json() == {"ok": True}

    # --- delete the project ---
    del_proj = client.delete(f"/api/projects/{project_id}")
    assert del_proj.status_code == 200
    assert del_proj.json() == {"ok": True}

    # project is gone
    assert client.get(f"/api/projects/{project_id}").status_code == 404


def test_get_unknown_project_is_404(client: Any) -> None:
    res = client.get("/api/projects/nope")
    assert res.status_code == 404


def test_patch_unknown_task_is_404(client: Any) -> None:
    res = client.patch("/api/tasks/nope", json={"status": "done"})
    assert res.status_code == 404
