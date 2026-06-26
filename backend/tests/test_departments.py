"""Department command-center API tests (cp-0048)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.departments import DEPARTMENTS


def test_list_departments() -> None:
    with TestClient(app) as c:
        body = c.get("/api/departments").json()
        slugs = {d["slug"] for d in body}
        assert slugs == set(DEPARTMENTS)
        assert all(d["title"] for d in body)


@pytest.mark.parametrize("slug", list(DEPARTMENTS))
def test_department_overview_shape(slug: str) -> None:
    with TestClient(app) as c:
        res = c.get(f"/api/departments/{slug}/overview")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["slug"] == slug
        assert body["title"] and body["note"] and body["accent"]
        assert len(body["stats"]) == 5  # KPI strip
        # camelCase keys present on the wire
        for a in body["agents"]:
            assert {"id", "name", "status", "modelLabel", "calls", "responsibilities"}.issubset(a)
            assert a["status"] in ("working", "needs_approval", "idle")
        for key in ("tasks", "workflows", "activity", "outputs", "providerUsage", "execution"):
            assert isinstance(body[key], list)


def test_engineering_lists_its_agents() -> None:
    with TestClient(app) as c:
        body = c.get("/api/departments/engineering/overview").json()
        ids = {a["id"] for a in body["agents"]}
        assert {"database-engineer", "frontend-engineer", "backend-engineer", "api-engineer"}.issubset(ids)
        assert "ceo-manager" not in ids  # executive, not engineering


def test_architecture_includes_design() -> None:
    with TestClient(app) as c:
        body = c.get("/api/departments/architecture/overview").json()
        ids = {a["id"] for a in body["agents"]}
        assert "solution-architect" in ids and "uiux-designer" in ids  # Architecture + Design


def test_unknown_department_404() -> None:
    with TestClient(app) as c:
        assert c.get("/api/departments/nope/overview").status_code == 404
