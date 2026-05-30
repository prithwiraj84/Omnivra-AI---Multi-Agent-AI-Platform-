"""End-to-end workspace-artifact tests: run a workflow, then list + read the
artifacts it wrote under the (temp) workspace sandbox via the /api/workspace routes.

``conftest`` points WORKSPACE_ROOT at a throwaway temp dir, so these writes never
touch the real workspace and the assertions are isolated per test session.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_run_writes_and_serves_artifacts() -> None:
    with TestClient(app) as c:
        # A doc-flavoured task routes to the documentation/architect agents, which
        # write markdown artifacts under the workspace sandbox.
        resp = c.post(
            "/api/workflows/run",
            json={"task": "Write the README and architecture documentation"},
        )
        assert resp.status_code == 200
        body = resp.json()

        # At least one agent output carries a workspace-relative .md artifact path.
        md_paths = [
            art
            for output in body["agentOutputs"]
            for art in output.get("artifacts", [])
            if art.endswith(".md")
        ]
        assert md_paths, f"expected .md artifacts, got {body['agentOutputs']!r}"

        # The workspace listing is a non-empty list with the contract fields.
        listing = c.get("/api/workspace/artifacts")
        assert listing.status_code == 200
        items = listing.json()
        assert isinstance(items, list) and items
        first = items[0]
        assert {"path", "category", "sizeBytes", "modified"}.issubset(first.keys())

        # Reading a real artifact returns its content.
        one_path = items[0]["path"]
        read = c.get(f"/api/workspace/artifacts/{one_path}")
        assert read.status_code == 200
        read_body = read.json()
        assert read_body["path"] == one_path
        assert isinstance(read_body["content"], str)

        # An unknown artifact path is a 404.
        missing = c.get("/api/workspace/artifacts/docs/does-not-exist-xyz.md")
        assert missing.status_code == 404
