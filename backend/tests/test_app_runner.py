"""Universal app runner (cp-0054): discovery, packaging, jail, status, stop — all hermetic.

These never spawn a real venv/uvicorn/npm (that's covered by a live smoke, not the unit suite); they
exercise the pure logic: which targets a generated project exposes, what the downloadable zip includes
and excludes, the path jail, idle status, and stopping an unknown target.
"""
from __future__ import annotations

import io
import zipfile

import pytest

from app.services import app_runner
from app.services.artifacts import get_artifact_service

PID = "apprunner_test"
ROOT = "apps/wf_test"

_MAIN = (
    "from fastapi import FastAPI\n"
    "from sqlmodel import SQLModel, create_engine\n"
    "import os\n"
    "app = FastAPI()\n"
    "@app.get('/')\n"
    "def root():\n"
    "    return {'ok': True}\n"
)


@pytest.fixture
def project():
    """Write a synthetic generated project (python backend + node frontend) + junk to exclude."""
    fm = get_artifact_service(PID).fm
    fm.write_text(f"{ROOT}/backend/main.py", _MAIN, agent_id="backend-engineer")
    fm.write_text(f"{ROOT}/backend/requirements.txt", "fastapi\nuvicorn[standard]\nsqlmodel\npydantic\n", agent_id="backend-engineer")
    fm.write_text(f"{ROOT}/frontend/package.json", '{"name":"x","scripts":{"dev":"vite"}}', agent_id="frontend-engineer")
    fm.write_text(f"{ROOT}/frontend/src/App.tsx", "export default function App(){return null}", agent_id="frontend-engineer")
    fm.write_text(f"{ROOT}/README.md", "# My App", agent_id="documentation-agent")
    # junk that must NOT appear in the zip:
    fm.write_text(f"{ROOT}/solution-architect.md", "agent transcript", agent_id="solution-architect")
    fm.write_text(f"{ROOT}/backend/.venv/pyvenv.cfg", "home = x", agent_id="backend-engineer")
    fm.write_text(f"{ROOT}/backend/__pycache__/main.cpython-311.pyc", "bytecode", agent_id="backend-engineer")
    fm.write_text(f"{ROOT}/frontend/node_modules/left-pad/index.js", "module.exports=1", agent_id="frontend-engineer")
    return PID, ROOT


def test_discover_finds_backend_and_frontend(project) -> None:
    pid, root = project
    targets = app_runner.discover_targets(pid, root)
    by_kind = {t["kind"]: t for t in targets}
    assert set(by_kind) == {"python", "node"}
    assert by_kind["python"]["framework"] == "fastapi"
    assert by_kind["python"]["rel"].endswith("/backend")
    assert by_kind["python"]["entry"] == "main.py"
    assert by_kind["node"]["framework"] == "vite"
    assert by_kind["node"]["rel"].endswith("/frontend")


def test_detect_python_fastapi_app_var(tmp_path) -> None:
    f = tmp_path / "main.py"
    f.write_text("from fastapi import FastAPI\napi = FastAPI()\n", encoding="utf-8")
    fw, var = app_runner._detect_python(f)
    assert fw == "fastapi" and var == "api"


def test_third_party_imports_excludes_stdlib_and_local(project) -> None:
    pid, root = project
    backend = app_runner._jail_dir(pid, f"{root}/backend")
    mods = app_runner._third_party_imports(backend)
    assert "fastapi" in mods and "sqlmodel" in mods  # third-party
    assert "os" not in mods  # stdlib excluded
    assert "main" not in mods  # local module excluded


def test_zip_includes_app_files_excludes_junk(project) -> None:
    pid, root = project
    name, data = app_runner.zip_app(pid, root)
    assert name == "wf_test.zip"
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    rels = {n.split("/", 1)[1] for n in names}  # strip the "wf_test/" arc prefix
    assert "backend/main.py" in rels
    assert "backend/requirements.txt" in rels
    assert "frontend/package.json" in rels
    assert "README.md" in rels  # README is kept
    # junk excluded:
    assert not any(".venv" in r for r in rels)
    assert not any("node_modules" in r for r in rels)
    assert not any("__pycache__" in r or r.endswith(".pyc") for r in rels)
    assert "solution-architect.md" not in rels  # agent transcript excluded


def test_jail_rejects_traversal(project) -> None:
    pid, _ = project
    with pytest.raises(ValueError):
        app_runner._jail_dir(pid, "../../../etc")


def test_status_idle_lists_targets(project) -> None:
    pid, root = project
    st = app_runner.app_status(pid, root)
    assert st["dir"] == root
    statuses = {t["kind"]: t["status"] for t in st["targets"]}
    assert statuses == {"python": "idle", "node": "idle"}
    assert all(t["url"] is None for t in st["targets"])


def test_stop_unknown_key_is_safe(project) -> None:
    pid, _ = project
    res = app_runner.stop_app(pid, "nope::does/not/exist")
    assert res["status"] == "idle" and "No such" in res["note"]


def test_zip_bad_dir_raises(project) -> None:
    pid, _ = project
    with pytest.raises((ValueError, FileNotFoundError)):
        app_runner.zip_app(pid, "../escape")


@pytest.mark.parametrize(
    "pkg,expected",
    [
        ('{"dependencies":{"vite":"^5"},"scripts":{"dev":"vite"}}', "vite"),
        ('{"dependencies":{"next":"14"},"scripts":{"dev":"next dev"}}', "next"),
        ('{"dependencies":{"react-scripts":"5"}}', "cra"),
        ('{"dependencies":{"express":"4"},"scripts":{"start":"node server.js"}}', "node"),
        ('{"main":"server.js"}', "node"),
    ],
)
def test_detect_node_classifies_framework(tmp_path, pkg, expected) -> None:
    (tmp_path / "package.json").write_text(pkg, encoding="utf-8")
    assert app_runner._detect_node(tmp_path) == expected


def test_list_apps_groups_one_card_per_workflow() -> None:
    """The same wf_* scattered across docs/backend/frontend collapses to ONE app at its best root."""
    pid = "grouping_test"
    fm = get_artifact_service(pid).fm
    # the full project under docs/ (2 targets) + a stray fragment under backend/ (1 target)
    fm.write_text("docs/wf_a/backend/main.py", _MAIN, agent_id="solution-architect")
    fm.write_text("docs/wf_a/backend/requirements.txt", "fastapi\n", agent_id="solution-architect")
    fm.write_text("docs/wf_a/frontend/package.json", '{"scripts":{"dev":"vite"},"dependencies":{"vite":"5"}}', agent_id="solution-architect")
    fm.write_text("backend/wf_a/frontend/package.json", '{"dependencies":{"vite":"5"}}', agent_id="backend-engineer")
    fm.write_text("reports/wf_a/run.md", "report", agent_id="ceo-manager")
    apps = app_runner.list_apps(pid)
    assert len(apps) == 1, apps
    assert apps[0]["wf_id"] == "wf_a"
    assert apps[0]["dir"] == "docs/wf_a"  # most complete root wins (2 targets, docs preferred)
