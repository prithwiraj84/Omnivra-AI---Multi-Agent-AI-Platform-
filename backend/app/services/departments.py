"""Department overview aggregator (cp-0048).

Builds the per-department command-center payload from the app's own live state — the
agent registry, workflow runs, project tasks, and workspace artifacts — filtered to a
single department's agents. Mirrors the gathering style of ``dashboard_live`` but scoped.
Every section is defensive: a failure leaves that section empty rather than 500-ing.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.agents.registry import AGENT_REGISTRY
from app.core.logging import logger
from app.data.seed import DEPARTMENT_ACCENT, MODEL_LABEL, PROVIDER_LABEL
from app.schemas.dashboard import StatCard, TaskPoint
from app.schemas.departments import (
    DeptActivity,
    DeptAgent,
    DeptOutput,
    DeptTask,
    DeptWorkflow,
    DepartmentOverview,
    ProviderCalls,
)
from app.services.artifacts import get_artifact_service
from app.services.workflow_store import get_workflow_store
from app.workspace_fs.paths import list_project_dir_ids

# slug -> (display title, roster department values, one-line note). Mirrors the frontend
# DEPARTMENTS config so both render the same set (Architecture surfaces Design too).
DEPARTMENTS: dict[str, tuple[str, list[str], str]] = {
    "executive": ("Executive", ["Executive"],
                  "Strategic direction and delegation. The CEO / Manager plans the roadmap and routes work."),
    "architecture": ("Architecture", ["Architecture", "Design"],
                     "System design and user experience. Architects and designers shape every build."),
    "engineering": ("Engineering", ["Engineering"],
                    "The builders. Database, frontend, backend and API engineers turn plans into software."),
    "quality": ("Quality & Security", ["Quality & Security"],
                "Verification and hardening. QA and SecOps test every build and scan it for vulnerabilities."),
    "marketing": ("Marketing", ["Marketing"],
                  "Reach and growth. SEO, social and reel-automation agents take the product to its audience."),
    "documentation": ("Documentation", ["Documentation"],
                      "Knowledge capture. Documentation and presentation agents keep the company explainable."),
    "system-ops": ("System Operations", ["System Ops"],
                   "The control plane. Classification, routing, memory, notification and log utilities."),
}

_DONE = {"completed"}
_FAILED = {"failed", "stopped"}
_CAT_ICON = {"docs": ("FileText", "violet"), "frontend": ("LayoutGrid", "blue"), "backend": ("Code2", "blue"),
             "reports": ("Activity", "emerald"), "presentations": ("Presentation", "violet")}


def _run_agents(r: Any) -> set[str]:
    ids = {"ceo-manager", *(getattr(r, "delegations", None) or [])}
    ids.update(o.agent_id for o in (getattr(r, "agent_outputs", []) or []))
    return ids


def _ago(iso: str) -> str:
    try:
        t = datetime.fromisoformat(iso)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        secs = (datetime.now(timezone.utc) - t).total_seconds()
    except Exception:  # noqa: BLE001
        return "recently"
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


def department_slugs() -> list[str]:
    return list(DEPARTMENTS)


def build_department_overview(slug: str) -> DepartmentOverview | None:
    """Aggregate one department's command-center payload, or None for an unknown slug."""
    cfg = DEPARTMENTS.get(slug)
    if not cfg:
        return None
    title, dept_values, note = cfg
    accent = next((DEPARTMENT_ACCENT.get(v, "cyan") for v in dept_values), "cyan")
    specs = [s for s in AGENT_REGISTRY.values() if s.department.value in dept_values]
    agent_ids = {s.id for s in specs}

    # --- gather cross-project state (defensively) ---
    runs: list[Any] = []
    artifacts: list[dict[str, Any]] = []
    try:
        for pid in list_project_dir_ids():
            try:
                runs.extend(get_workflow_store(pid).list())
            except Exception:  # noqa: BLE001
                pass
            try:
                for it in get_artifact_service(pid).list_artifacts():
                    it["project_id"] = pid  # tag so the outputs gallery can build a download URL
                    artifacts.append(it)
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        pass
    try:
        from app.services.project_store import get_project_store

        all_tasks = get_project_store().list_tasks()
    except Exception:  # noqa: BLE001
        all_tasks = []

    # --- filter to this department ---
    dept_runs = [r for r in runs if agent_ids & _run_agents(r)]
    dept_run_ids = {getattr(r, "workflow_id", "") for r in dept_runs}
    dept_tasks = [t for t in all_tasks if t.get("agent_id") in agent_ids]

    def _is_dept_artifact(a: dict[str, Any]) -> bool:
        if a.get("agent_id") in agent_ids:  # the agent's own .md output
            return True
        parts = (a.get("path") or "").split("/")  # code files: <category>/<workflow_id>/...
        return len(parts) > 1 and parts[1] in dept_run_ids
    dept_artifacts = [a for a in artifacts if _is_dept_artifact(a)]

    # --- live status ---
    working: set[str] = set()
    awaiting: set[str] = set()
    for r in runs:
        if r.status == "running":
            ca = getattr(r, "current_agent", None)
            working |= ({ca} if ca else _run_agents(r)) & agent_ids
        elif r.status == "awaiting_approval":
            awaiting |= _run_agents(r) & agent_ids
    awaiting -= working

    def _status(aid: str) -> str:
        return "working" if aid in working else "needs_approval" if aid in awaiting else "idle"

    # --- per-agent call counts + last activity ---
    calls = Counter()
    for r in runs:
        for o in getattr(r, "agent_outputs", []) or []:
            if o.agent_id in agent_ids:
                calls[o.agent_id] += 1
    last_seen: dict[str, str] = {}
    for a in artifacts:  # artifacts are newest-first
        aid = a.get("agent_id")
        if aid in agent_ids and aid not in last_seen:
            last_seen[aid] = a.get("modified")

    agents = [
        DeptAgent(
            id=s.id, name=s.name, status=_status(s.id), provider=s.provider, model=s.model,
            model_label=MODEL_LABEL.get(s.model, s.model), accent=accent, kind=s.kind.value,
            calls=int(calls.get(s.id, 0)), last_activity=last_seen.get(s.id),
            responsibilities=list(s.responsibilities),
        )
        for s in specs
    ]

    # --- KPI stats ---
    completed = sum(1 for r in dept_runs if r.status in _DONE)
    failed = sum(1 for r in dept_runs if r.status in _FAILED)
    success = round(100 * completed / (completed + failed), 1) if (completed + failed) else None
    in_prog_tasks = sum(1 for t in dept_tasks if t.get("status") == "in_progress")
    done_tasks = sum(1 for t in dept_tasks if t.get("status") == "done")
    total_calls = int(sum(calls.values()))
    stats = [
        StatCard(label="Agents", value=str(len(specs)), sub=f"{len(working)} working", accent=accent, icon="Bot"),
        StatCard(label="Tasks", value=str(in_prog_tasks), sub=f"{len(dept_tasks)} total", accent="blue", icon="Activity"),
        StatCard(label="Workflow Runs", value=str(len(dept_runs)), sub=f"{completed} completed", accent="emerald", icon="CheckCircle2"),
        StatCard(label="Success Rate", value=(f"{success}%" if success is not None else "—"), sub=("Excellent" if (success or 0) >= 90 else "Live"), accent="emerald", icon="TrendingUp"),
        StatCard(label="LLM Calls", value=str(total_calls), sub="All runs", accent="violet", icon="Zap"),
    ]

    # --- tasks / workflows / activity / outputs / provider usage ---
    tasks = [DeptTask(id=t.get("id", ""), title=(t.get("title") or "Task")[:80], status=t.get("status", "todo"), priority=t.get("priority", "medium")) for t in dept_tasks[:24]]
    workflows = [
        DeptWorkflow(id=r.workflow_id, task=(r.task or "Workflow")[:60], status=r.status, agents=len(agent_ids & _run_agents(r)))
        for r in dept_runs[:8]
    ]
    activity = []
    for i, a in enumerate(dept_artifacts[:8]):
        icon, acc = _CAT_ICON.get(a.get("category", "reports"), ("Activity", "cyan"))
        who = (a.get("agent_id") or a.get("category") or "agent").replace("-", " ").title()
        fname = (a.get("path") or "").split("/")[-1]
        activity.append(DeptActivity(id=f"da-{i}", agent=who, action=f"wrote {fname}", time=_ago(a.get("modified", "")), accent=acc, icon=icon))
    outputs = [
        DeptOutput(path=a.get("path", ""), category=a.get("category", ""), size_bytes=int(a.get("size_bytes", 0)), modified=a.get("modified", ""), agent_id=a.get("agent_id"), project_id=a.get("project_id", ""))
        for a in dept_artifacts[:18]
    ]
    prov_counter = Counter()
    for s in specs:
        prov_counter[s.provider] += calls.get(s.id, 0)
    provider_usage = [
        ProviderCalls(provider=p, label=PROVIDER_LABEL.get(p, p), calls=int(c))
        for p, c in sorted(prov_counter.items(), key=lambda kv: kv[1], reverse=True)
        if c > 0
    ]

    # --- execution trend (cumulative over the day) ---
    labels = ["12 AM", "04 AM", "08 AM", "12 PM", "04 PM", "08 PM"]
    n = len(labels)
    c_t, p_t, f_t = done_tasks + completed, in_prog_tasks, failed
    execution = [TaskPoint(time=lbl, completed=round(c_t * (i + 1) / n), in_progress=round(p_t * (i + 1) / n), failed=round(f_t * (i + 1) / n)) for i, lbl in enumerate(labels)]

    return DepartmentOverview(
        slug=slug, title=title, note=note, accent=accent, stats=stats, agents=agents,
        tasks=tasks, workflows=workflows, activity=activity, outputs=outputs,
        provider_usage=provider_usage, execution=execution,
    )
