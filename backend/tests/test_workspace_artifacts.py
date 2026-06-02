"""End-to-end workspace-artifact tests: run a workflow, then list + read the
artifacts it wrote under the (temp) workspace sandbox via the /api/workspace routes.

``conftest`` points WORKSPACE_ROOT at a throwaway temp dir, so these writes never
touch the real workspace and the assertions are isolated per test session.
"""
from __future__ import annotations

import pytest
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
        # Fire-and-poll: the POST returns 'running'; read the terminal run (with its artifacts)
        # back via GET /runs/{id} (the BackgroundTask has finished by then under TestClient).
        body = c.get(f"/api/workflows/runs/{resp.json()['workflowId']}").json()

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

        # The binary media endpoint streams the same artifact (bytes) and 404s on miss.
        media = c.get(f"/api/workspace/media/{one_path}")
        assert media.status_code == 200
        assert media.content
        assert c.get("/api/workspace/media/reports/no-such-media-xyz.mp4").status_code == 404


@pytest.mark.parametrize(
    "payload",
    ["..%2f..%2f..%2fetc%2fpasswd", "%2e%2e%2f%2e%2e%2fsecret.txt", "....//....//x", "docs%2f..%2f..%2f..%2fmain.py"],
)
def test_media_endpoint_blocks_traversal(payload: str) -> None:
    """The binary media route must never serve a file outside the sandbox: any
    traversal payload is rejected (400 jail) or 404 — never a 200 with foreign bytes."""
    with TestClient(app) as c:
        resp = c.get(f"/api/workspace/media/{payload}")
        assert resp.status_code in (400, 404), (payload, resp.status_code)


# --- Guarded in-workspace runner (POST /api/workspace/run) ---
def _write(rel: str, body: str) -> None:
    from app.services.artifacts import get_artifact_service

    get_artifact_service("__default__").fm.write_text(rel, body, agent_id="qa-engineer")


def test_run_executes_a_workspace_python_file() -> None:
    with TestClient(app) as c:
        _write("reports/runtest/hello.py", "print('hello from omnivra')\n")
        r = c.post("/api/workspace/run", json={"path": "reports/runtest/hello.py"})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True, body
        assert body["exitCode"] == 0
        assert "hello from omnivra" in body["stdout"]
        assert body["timedOut"] is False


def test_run_reports_a_nonzero_exit_without_500() -> None:
    with TestClient(app) as c:
        _write("reports/runtest/boom.py", "import sys\nprint('partial')\nsys.exit(3)\n")
        body = c.post("/api/workspace/run", json={"path": "reports/runtest/boom.py"}).json()
        assert body["ok"] is False
        assert body["exitCode"] == 3
        assert "partial" in body["stdout"]


def test_run_refuses_unsupported_file_type() -> None:
    with TestClient(app) as c:
        _write("reports/runtest/notes.md", "# not runnable\n")
        body = c.post("/api/workspace/run", json={"path": "reports/runtest/notes.md"}).json()
        assert body["ok"] is False
        assert "Cannot run" in body["note"]


@pytest.mark.parametrize("path", ["../../../etc/passwd", "..\\..\\secret.py", "reports/../../../escape.py"])
def test_run_blocks_path_traversal(path: str) -> None:
    # An escape attempt must never run anything outside the sandbox — returns ok=False, no 500.
    with TestClient(app) as c:
        r = c.post("/api/workspace/run", json={"path": path})
        assert r.status_code == 200
        assert r.json()["ok"] is False


def test_agent_output_writes_real_code_files() -> None:
    # A builder agent's `name=<path>` fenced blocks are extracted into REAL workspace files
    # (so the codebase is browsable + runnable), alongside the .md summary.
    from app.services.artifacts import extract_code_files, get_artifact_service

    content = (
        "Built the service:\n"
        "```python name=app/main.py\nprint('hello')\n```\n"
        "and a stylesheet:\n"
        "```css name=static/site.css\nbody { margin: 0; }\n```\n"
        "plus a malicious one:\n"
        "```python name=../../../escape.py\nimport os\n```\n"
    )
    files = extract_code_files(content)
    paths = {p for p, _ in files}
    assert "app/main.py" in paths and "static/site.css" in paths
    assert not any(".." in p for p in paths), "traversal paths must be dropped by the extractor"

    svc = get_artifact_service("__default__")
    rels = svc.write_agent_output("wf_codetest", "backend-engineer", content)
    assert any(r.endswith("backend/wf_codetest/app/main.py") for r in rels)
    assert any(r.endswith("backend/wf_codetest/static/site.css") for r in rels)
    assert any(r.endswith("backend/wf_codetest/backend-engineer.md") for r in rels)
    # The extracted .py is a real, readable, runnable file.
    py_rel = next(r for r in rels if r.endswith("app/main.py"))
    assert "print('hello')" in svc.read_artifact(py_rel)


def test_extract_code_files_is_not_redos_prone() -> None:
    # A degenerate backtick-dense blob (no valid fence) must scan in well under a second — the
    # anchored regex can't catastrophically backtrack and stall the (async) persist path.
    import time

    from app.services.artifacts import extract_code_files

    t0 = time.monotonic()
    assert extract_code_files("`" * 50_000) == []
    assert time.monotonic() - t0 < 1.0, "extract_code_files must stay linear on backtick-dense input"


def test_run_enforces_the_timeout(monkeypatch) -> None:
    # A long-running file is killed at the wall-clock cap and reported as timed out (never hangs).
    import app.services.code_runner as cr

    monkeypatch.setattr(cr, "_TIMEOUT_SEC", 1.5)
    with TestClient(app) as c:
        _write("reports/runtest/slow.py", "import time\nprint('start', flush=True)\ntime.sleep(30)\n")
        body = c.post("/api/workspace/run", json={"path": "reports/runtest/slow.py"}).json()
        assert body["timedOut"] is True
        assert body["ok"] is False
        assert "time limit" in body["note"]
