"""ArtifactService — persists agent outputs as artifacts under ./workspace.

Every write goes through the path-jailed :class:`FileManager`, so agents can only
ever create files inside the workspace sandbox (the WORKSPACE RULE). Outputs are
filed by agent into the standard subdirs (docs / frontend / backend / presentations
/ reports). The Workspace view lists + reads them via the /api/workspace routes.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.workspace_fs.file_manager import SUBDIRS, FileManager
from app.workspace_fs.paths import DEFAULT_PROJECT, project_root

# Builder agents emit files as fenced blocks whose info line carries `name=<path>`, e.g.
# ```python name=app/main.py  ...  ``` — extract (path, code) so we can write real code files.
# ANCHORED to line starts with NO backticks allowed in the info-line scan, so it is linear and
# can't catastrophically backtrack on backtick-dense input (which would stall the event loop).
# NOTE: a flat fence parse clips a body that itself contains a ``` line — acceptable for now.
_CODE_BLOCK = re.compile(r"(?ms)^```[^\n`]*\bname=([^\s`]+)[^\n]*\n(.*?)\n```\s*$")
_MAX_SCAN = 400_000  # never scan an absurdly large blob (belt-and-suspenders vs pathological input)


def extract_code_files(content: str) -> list[tuple[str, str]]:
    """Pull (relative_path, code) pairs from ``name=``-tagged fenced blocks in agent output."""
    content = (content or "")[:_MAX_SCAN]
    files: list[tuple[str, str]] = []
    for m in _CODE_BLOCK.finditer(content):
        path = m.group(1).strip().strip('"').strip("'")
        code = m.group(2)
        if path and ".." not in path:  # the FileManager also jails; this is belt-and-suspenders
            files.append((path, code.rstrip("\n") + "\n"))
    return files

# agent id -> workspace subdir for its artifacts.
_CATEGORY: dict[str, str] = {
    "ceo-manager": "reports",
    "solution-architect": "docs",
    "documentation-agent": "docs",
    "uiux-designer": "frontend",
    "frontend-engineer": "frontend",
    "backend-engineer": "backend",
    "api-engineer": "backend",
    "database-engineer": "backend",
    "presentation-designer": "presentations",
    "seo-researcher": "reports",
    "social-strategist": "reports",
    "reel-automation": "reports",
    "secops-engineer": "reports",
    "qa-engineer": "reports",
    "recovery-agent": "reports",
}


def _category(agent_id: str) -> str:
    return _CATEGORY.get(agent_id, "reports")


class ArtifactService:
    def __init__(self, workspace_root: str | Path) -> None:
        self.fm = FileManager(workspace_root)
        self.fm.ensure_layout()

    def write_agent_output(self, workflow_id: str, agent_id: str, content: str) -> list[str]:
        """Persist one agent's output: a markdown summary PLUS every real code file it emitted
        (``name=<path>`` fenced blocks) written as ACTUAL files under <category>/<workflow_id>/.

        Returns all workspace-relative paths written (the .md first). So the workspace shows a real
        browsable, runnable codebase — not just a prose description. Path-jailed: a declared path
        that would escape the sandbox is skipped.
        """
        cat = _category(agent_id)
        rels: list[str] = []
        md_rel = f"{cat}/{workflow_id}/{agent_id}.md"
        self.fm.write_text(md_rel, content or "", agent_id=agent_id)
        rels.append(md_rel)
        for decl_path, code in extract_code_files(content or ""):
            rel = f"{cat}/{workflow_id}/{decl_path.lstrip('/').lstrip(chr(92))}"
            try:
                self.fm.write_text(rel, code, agent_id=agent_id)  # jailed; rejects escapes
                rels.append(rel)
            except Exception:  # noqa: BLE001 - skip a file whose declared path escapes the sandbox
                continue
        return rels

    def write_run_report(self, workflow_id: str, task: str, plan: list[str], outputs: list[dict[str, Any]]) -> str:
        """Write a human-readable run report summarizing the workflow."""
        lines = [f"# Workflow {workflow_id}", "", f"**Task:** {task}", "", f"**Plan:** {', '.join(plan) or '(none)'}", ""]
        for o in outputs:
            lines += [f"## {o.get('agent_id', 'agent')}", "", str(o.get("content", "")).strip(), ""]
        rel = f"reports/{workflow_id}/run.md"
        self.fm.write_text(rel, "\n".join(lines), agent_id="ceo-manager")
        return rel

    def persist_run(self, workflow_id: str, task: str, plan: list[str], outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Write artifacts for a whole run; return the outputs enriched with their artifact paths."""
        enriched: list[dict[str, Any]] = []
        for o in outputs:
            arts: list[str] = []
            if o.get("content"):
                try:
                    arts = self.write_agent_output(workflow_id, o.get("agent_id", "agent"), o.get("content", ""))
                except Exception:  # noqa: BLE001 - never let artifact IO break a run
                    arts = []
            enriched.append({**o, "artifacts": arts})
        try:
            self.write_run_report(workflow_id, task, plan, outputs)
        except Exception:  # noqa: BLE001
            pass
        return enriched

    def list_artifacts(self) -> list[dict[str, Any]]:
        """List every artifact under the workspace subdirs (newest first)."""
        items: list[dict[str, Any]] = []
        for sub in SUBDIRS:
            base = self.fm.root / sub
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file() and path.name != ".gitkeep":
                    stat = path.stat()
                    items.append(
                        {
                            "path": path.relative_to(self.fm.root).as_posix(),
                            "category": sub,
                            "size_bytes": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                            "agent_id": path.stem if path.suffix == ".md" else None,
                        }
                    )
        items.sort(key=lambda i: i["modified"], reverse=True)
        return items

    def read_artifact(self, rel_path: str) -> str:
        """Read an artifact's text (path-jailed; raises if it escapes the sandbox)."""
        return self.fm.read_text(rel_path)


@lru_cache(maxsize=None)
def get_artifact_service(project_id: str = DEFAULT_PROJECT) -> ArtifactService:
    """Per-project ArtifactService (jailed to workspace/projects/<project_id>/)."""
    return ArtifactService(project_root(project_id))
