"""The workspace sandbox must let agents write inside it and refuse to escape it."""
from __future__ import annotations

import pytest

from app.workspace_fs.file_manager import (
    SUBDIRS,
    FileManager,
    WorkspaceViolationError,
)


def test_ensure_layout_creates_subdirs(tmp_path) -> None:
    fm = FileManager(tmp_path)
    fm.ensure_layout()
    for sub in SUBDIRS:
        assert (tmp_path / sub).is_dir()


def test_write_and_read_inside_sandbox(tmp_path) -> None:
    fm = FileManager(tmp_path)
    fm.ensure_layout()
    entry = fm.write_text("docs/notes.md", "# hello", agent_id="documentation-agent")
    assert entry.agent_id == "documentation-agent"
    assert entry.size_bytes == len("# hello".encode("utf-8"))
    assert fm.exists("docs/notes.md")
    assert fm.read_text("docs/notes.md") == "# hello"


@pytest.mark.parametrize("escape", ["../escape.txt", "../../etc/passwd", "docs/../../outside.txt"])
def test_path_traversal_is_rejected(tmp_path, escape) -> None:
    fm = FileManager(tmp_path)
    fm.ensure_layout()
    with pytest.raises(WorkspaceViolationError):
        fm.write_text(escape, "should never be written")
