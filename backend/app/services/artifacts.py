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

# Builder agents are INSTRUCTED to emit files as ```lang name=<path> fenced blocks — but
# free-tier models ignore instructions often enough that whole runs materialized as one prose
# .md and NOTHING runnable ("No runnable backend/frontend detected"). So extraction now also
# recognizes the shapes models actually produce, in order of trustworthiness:
#   1. the info line:      ```python name=app/main.py   (also file= / path= / title=)
#   2. the info line IS a path:            ```app/main.py
#   3. a heading just above the fence:     **app/main.py** / ### `src/App.jsx` / File: main.py
#   4. a comment on the body's first line: # app/main.py   // src/App.jsx   <!-- index.html -->
#   5. last resort, html only: one unnamed full html page becomes index.html — a page is
#      self-evidently a file, and it makes the run instantly previewable. Other languages are
#      NEVER synthesized: an unnamed python block may be a snippet, and inventing main.py for
#      it would create confidently broken "runnable" targets.
# ANCHORED to line starts with NO backticks in the info-line scan, so parsing stays linear on
# backtick-dense input. NOTE: a flat fence parse clips a body containing a ``` line — accepted.
_ANY_BLOCK = re.compile(r"(?ms)^```([^\n`]*)\n(.*?)\n```[ \t]*$")
_INFO_NAME = re.compile(r"\b(?:name|file|path|title)=([^\s`]+)")
# A plausible relative file path with a real code/asset extension. No spaces, no URLs.
_PATHY = re.compile(
    r"^[\w./\\-]+\.(?:py|js|jsx|ts|tsx|mjs|html?|css|json|sql|ya?ml|toml|md|txt|sh|env|svg|cfg|ini)$",
    re.IGNORECASE,
)
_HEADING_PATH = re.compile(r"(?:^|\s|`|\*)((?:[\w-]+[/\\])*[\w-]+\.[A-Za-z0-9]{1,6})(?:`|\*|\s|:|$)")
_COMMENT_PATH = re.compile(r"^\s*(?:#|//|<!--|/\*|--)\s*(?:file:|filename:)?\s*([\w./\\-]+\.[A-Za-z0-9]{1,6})\s*(?:-->|\*/)?\s*$")
_MAX_SCAN = 400_000  # never scan an absurdly large blob (belt-and-suspenders vs pathological input)


def _clean_path(raw: str | None) -> str | None:
    """A usable relative path from a candidate string, or None."""
    if not raw:
        return None
    path = raw.strip().strip('"').strip("'").strip("`").replace("\\", "/").lstrip("/")
    if not path or ".." in path or not _PATHY.match(path):
        return None
    return path


def _heading_path(content: str, fence_start: int) -> str | None:
    """A file path named in the last non-empty line just above the fence (bold/heading/File:)."""
    lines = content[:fence_start].rstrip("\n").rsplit("\n", 2)[-2:]
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        m = _HEADING_PATH.search(line)
        return _clean_path(m.group(1)) if m else None
    return None


def extract_code_files(content: str) -> list[tuple[str, str]]:
    """Pull (relative_path, code) pairs from the fenced code blocks in agent output."""
    content = (content or "")[:_MAX_SCAN]
    files: list[tuple[str, str]] = []
    seen: set[str] = set()
    html_synthesized = False
    for m in _ANY_BLOCK.finditer(content):
        info, code = m.group(1).strip(), m.group(2)
        lang = (info.split() or [""])[0].lower()

        named = _INFO_NAME.search(info)
        path = _clean_path(named.group(1)) if named else None
        if path is None:
            path = _clean_path(info)  # the whole info line is the path (```app/main.py)
        if path is None:
            path = _heading_path(content, m.start())
        if path is None:
            first = code.split("\n", 1)[0]
            cm = _COMMENT_PATH.match(first)
            path = _clean_path(cm.group(1)) if cm else None
        if path is None and not html_synthesized and (lang in ("html", "") and "<html" in code.lower()):
            path, html_synthesized = "index.html", True  # a full page IS a file; make it previewable

        if path and path not in seen:
            seen.add(path)
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
