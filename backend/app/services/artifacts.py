"""ArtifactService — persists agent outputs as artifacts under ./workspace.

Every write goes through the path-jailed :class:`FileManager`, so agents can only
ever create files inside the workspace sandbox (the WORKSPACE RULE). Outputs are
filed by agent into the standard subdirs (docs / frontend / backend / presentations
/ reports). The Workspace view lists + reads them via the /api/workspace routes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.workspace_fs.file_manager import SUBDIRS, FileManager
from app.workspace_fs.paths import DEFAULT_PROJECT, project_root

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

    def write_agent_output(self, workflow_id: str, agent_id: str, content: str) -> str:
        """Write one agent's output as a markdown artifact; return its workspace-relative path."""
        rel = f"{_category(agent_id)}/{workflow_id}/{agent_id}.md"
        self.fm.write_text(rel, content or "", agent_id=agent_id)
        return rel

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
                    arts = [self.write_agent_output(workflow_id, o.get("agent_id", "agent"), o.get("content", ""))]
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
