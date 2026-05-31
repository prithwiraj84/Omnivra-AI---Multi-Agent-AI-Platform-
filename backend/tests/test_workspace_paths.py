"""Unit tests for per-project path resolution, the path jail, and the migration
merge helper (cp-0015). These are pure-function tests (no HTTP / no app state)."""
from __future__ import annotations

import pytest

from app.workspace_fs.paths import (
    DEFAULT_PROJECT,
    _merge_move,
    migrate_flat_workspace,
    project_root,
    purge_project_workspace,
    safe_project_id,
)


@pytest.mark.parametrize("blank", [None, "", "   "])
def test_blank_project_id_maps_to_default(blank: str | None) -> None:
    assert safe_project_id(blank) == DEFAULT_PROJECT


@pytest.mark.parametrize("bad", ["../escape", "..", "a/b", "a\\b", "a/../b", "x\x00y", "../../etc"])
def test_traversal_project_ids_are_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        safe_project_id(bad)


def test_valid_project_ids_pass_through() -> None:
    for ok in ("proj-dashboard", "proj-1a2b3c", "__default__", "My_Project.v2"):
        assert safe_project_id(ok) == ok


def test_project_root_is_under_projects_dir() -> None:
    root = project_root("proj-xyz")
    assert root.name == "proj-xyz"
    assert root.parent.name == "projects"


def test_purge_rejects_traversal_id() -> None:
    # purge validates via safe_project_id, so a traversal id never reaches rmtree.
    with pytest.raises(ValueError):
        purge_project_workspace("../../etc")


def test_purge_missing_project_is_noop() -> None:
    assert purge_project_workspace("proj-never-existed-xyz") is False


def test_merge_move_moves_and_preserves_existing(tmp_path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "sub").mkdir(parents=True)
    (src / "new.txt").write_text("new", encoding="utf-8")
    (src / "sub" / "deep.txt").write_text("deep", encoding="utf-8")
    # dst already has a colliding file that must be preserved (already-migrated).
    dst.mkdir()
    (dst / "new.txt").write_text("existing", encoding="utf-8")

    moved = _merge_move(src, dst)

    assert moved is True
    assert (dst / "sub" / "deep.txt").read_text(encoding="utf-8") == "deep"  # nested moved
    assert (dst / "new.txt").read_text(encoding="utf-8") == "existing"  # collision preserved in dst
    assert not (src / "sub").exists(), "a fully-moved subdir is removed from src"
    # A colliding file is left in src (migration never deletes data; the dst copy wins).
    assert (src / "new.txt").exists()


def _make_flat_workspace(ws):
    """Build a realistic pre-partition flat workspace under ``ws``."""
    (ws / ".state").mkdir(parents=True)
    # legacy artifacts + per-run state that SHOULD migrate
    (ws / "docs" / "wf_old").mkdir(parents=True)
    (ws / "docs" / "wf_old" / "architect.md").write_text("arch", encoding="utf-8")
    (ws / "reports").mkdir()
    (ws / "reports" / "run.md").write_text("report", encoding="utf-8")
    (ws / ".state" / "vectors").mkdir()
    (ws / ".state" / "vectors" / "memory.json").write_text("[]", encoding="utf-8")
    (ws / ".state" / "workflows").mkdir()
    (ws / ".state" / "workflows" / "wf_old.json").write_text("{}", encoding="utf-8")
    # GLOBAL state that must STAY put
    (ws / ".state" / "projects.json").write_text("[]", encoding="utf-8")
    (ws / ".state" / "tasks.json").write_text("[]", encoding="utf-8")
    (ws / ".state" / "checkpoints").mkdir()
    (ws / ".state" / "checkpoints" / "cp-0001.json").write_text("{}", encoding="utf-8")
    (ws / "README.md").write_text("ws", encoding="utf-8")


def test_migration_moves_legacy_data_and_preserves_global(tmp_path) -> None:
    ws = tmp_path / "workspace"
    _make_flat_workspace(ws)

    moved = migrate_flat_workspace(ws)
    assert moved is True

    dest = ws / "projects" / DEFAULT_PROJECT
    # legacy artifacts + per-run state migrated into the default project
    assert (dest / "docs" / "wf_old" / "architect.md").read_text(encoding="utf-8") == "arch"
    assert (dest / "reports" / "run.md").exists()
    assert (dest / ".state" / "vectors" / "memory.json").exists()
    assert (dest / ".state" / "workflows" / "wf_old.json").exists()
    # GLOBAL state stays at the top level — never moved into a project
    assert (ws / ".state" / "projects.json").exists()
    assert (ws / ".state" / "tasks.json").exists()
    assert (ws / ".state" / "checkpoints" / "cp-0001.json").exists()
    assert not (dest / ".state" / "checkpoints").exists()
    assert (ws / "README.md").exists()
    # marker written
    assert (ws / ".state" / ".migrated_v2_projects").exists()


def test_migration_is_idempotent(tmp_path) -> None:
    ws = tmp_path / "workspace"
    _make_flat_workspace(ws)
    assert migrate_flat_workspace(ws) is True
    # Second run is a no-op (marker present) and never moves data twice.
    assert migrate_flat_workspace(ws) is False


def test_migration_on_fresh_install_is_noop(tmp_path) -> None:
    ws = tmp_path / "workspace"
    (ws / ".state").mkdir(parents=True)
    assert migrate_flat_workspace(ws) is False
    assert (ws / ".state" / ".migrated_v2_projects").exists()
