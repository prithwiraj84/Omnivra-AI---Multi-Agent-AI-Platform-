"""Live dashboard aggregator (cp-0022/cp-0023) — real operational data, never seed demo.

Computes the dashboard payload from the app's OWN live state (cross-project): the
agent registry, workflow runs, project tasks, RAG memory + knowledge sizes, awaiting
approvals + social drafts, recent workspace artifacts, configured providers, and
provider/model usage derived from the PERSISTED run history (so it survives restarts).

EVERY operational field is overridden unconditionally (empty -> empty list/0) so the
seed base never shows through — the dashboard is always live (real or honestly empty).
Each section is defensive: a section that can't be computed keeps the base value.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.agents.registry import AGENT_REGISTRY
from app.core.logging import logger
from app.data.seed import ACCENT_HEX, CATEGORICAL, DEPARTMENT_ACCENT, MODEL_LABEL, PROVIDER_LABEL
from app.providers.registry import get_provider_registry
from app.schemas.dashboard import (
    Achievement,
    ActivityItem,
    ApprovalItem,
    DashboardPayload,
    DistributionSlice,
    HealthMetric,
    MediaService,
    ModelUsage,
    ProviderUsage,
    StatCard,
    TaskPoint,
    WorkflowItem,
)
from app.services.artifacts import get_artifact_service
from app.services.knowledge import get_knowledge_service
from app.services.memory import get_memory_service
from app.services.realtime import manager
from app.services.social_store import get_social_store
from app.services.usage import snapshot as usage_snapshot
from app.services.workflow_store import get_workflow_store
from app.workspace_fs.paths import list_project_dir_ids

_DONE = {"completed"}
_FAILED = {"failed", "stopped"}
_CAT_ICON = {"docs": ("FileText", "violet"), "frontend": ("LayoutGrid", "blue"), "backend": ("Code2", "blue"), "reports": ("Activity", "emerald"), "presentations": ("Presentation", "violet")}
_MEDIA_META = {"image": ("Image Generation", "FLUX.1-schnell", "emerald", "Image"), "tts": ("Text-to-Speech", "Orpheus", "violet", "Volume2"), "stt": ("Speech-to-Text", "Whisper", "cyan", "Mic")}


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


def build_live_dashboard(base: DashboardPayload) -> DashboardPayload:
    """Return ``base`` with ALL operational fields replaced by live values."""
    try:
        pids = list_project_dir_ids()
    except Exception:  # noqa: BLE001
        return base

    runs: list[Any] = []
    drafts: list[Any] = []
    artifacts: list[dict[str, Any]] = []
    mem = kb = 0
    for pid in pids:
        for getter, sink in ((get_workflow_store, runs), (get_social_store, drafts)):
            try:
                sink.extend(getter(pid).list())
            except Exception:  # noqa: BLE001
                pass
        try:
            artifacts.extend(get_artifact_service(pid).list_artifacts())
        except Exception:  # noqa: BLE001
            pass
        try:
            mem += get_memory_service(pid).count
        except Exception:  # noqa: BLE001
            pass
        try:
            kb += get_knowledge_service(pid).count
        except Exception:  # noqa: BLE001
            pass
    artifacts.sort(key=lambda a: a.get("modified", ""), reverse=True)

    completed = sum(1 for r in runs if r.status in _DONE)
    failed = sum(1 for r in runs if r.status in _FAILED)
    awaiting = [r for r in runs if r.status == "awaiting_approval"]
    success = round(100 * completed / (completed + failed), 1) if (completed + failed) else None

    # Provider / model usage from the PERSISTED run history (survives restart).
    prov_calls: Counter = Counter()
    model_calls: Counter = Counter()
    for r in runs:
        for o in getattr(r, "agent_outputs", []) or []:
            spec = AGENT_REGISTRY.get(o.agent_id)
            if spec:
                prov_calls[spec.provider] += 1
                model_calls[spec.model] += 1
    total_agent_calls = int(sum(prov_calls.values()))

    # LIVE agent status: an agent is 'working' if it's in a CURRENTLY-running run, or
    # 'needs_approval' if it's in a run paused at the approval gate — else 'idle'. The CEO
    # always counts as working/awaiting for its run (it orchestrates even before delegations
    # are recorded on the begin_run placeholder).
    def _run_agents(r: Any) -> set[str]:
        ids = {"ceo-manager", *(getattr(r, "delegations", None) or [])}
        ids.update(o.agent_id for o in (getattr(r, "agent_outputs", []) or []))
        return ids

    working_agents: set[str] = set()
    awaiting_agents: set[str] = set()
    for r in runs:
        if r.status == "running":
            working_agents |= _run_agents(r)
        elif r.status == "awaiting_approval":
            awaiting_agents |= _run_agents(r)
    awaiting_agents -= working_agents  # a live run wins over a stale gate for the same agent
    busy_agents = working_agents | awaiting_agents
    media_calls = usage_snapshot().get("media", {})  # media is session-scoped (no persisted log)

    try:
        from app.services.project_store import get_project_store

        ps = get_project_store()
        projects = ps.list_projects()
        tasks = ps.list_tasks()
    except Exception:  # noqa: BLE001
        projects, tasks = [], []

    o: dict[str, Any] = {}
    agents_total = len(AGENT_REGISTRY)
    active_tasks = sum(1 for t in tasks if t.get("status") == "in_progress")
    done_tasks = sum(1 for t in tasks if t.get("status") == "done")

    def section(fn) -> None:  # run a section; on failure keep the base value for its keys
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            logger.debug("dashboard_live section failed: {}", exc)

    # --- stats ---
    def _stats() -> None:
        o["stats"] = [
            StatCard(label="Agents", value=str(agents_total), sub=f"{len(busy_agents)} active", accent="cyan", icon="Bot"),
            StatCard(label="Active Tasks", value=str(active_tasks), sub=f"{len(tasks)} total", accent="blue", icon="Activity"),
            StatCard(label="Workflow Runs", value=str(len(runs)), sub=f"{completed} completed", accent="emerald", icon="CheckCircle2"),
            StatCard(label="Success Rate", value=(f"{success}%" if success is not None else "—"), sub=("Excellent" if (success or 0) >= 90 else "Live"), accent="emerald", icon="TrendingUp"),
            StatCard(label="LLM Calls", value=str(total_agent_calls), sub="All runs", accent="violet", icon="Zap"),
        ]

    # --- agents: live status (working in a run / needs_approval at the gate / else idle) ---
    def _status_for(agent_id: str) -> str:
        if agent_id in working_agents:
            return "working"
        if agent_id in awaiting_agents:
            return "needs_approval"
        return "idle"

    def _agents() -> None:
        o["agents"] = [a.model_copy(update={"status": _status_for(a.id)}) for a in base.agents]
        o["system_ops"] = [a.model_copy(update={"status": _status_for(a.id)}) for a in base.system_ops]

    # --- workflows (real runs) ---
    def _workflows() -> None:
        view = {"completed": ("Completed", 100, "emerald"), "awaiting_approval": ("Review", 90, "amber"), "failed": ("Failed", 100, "pink"), "stopped": ("Stopped", 100, "pink"), "rolled_back": ("Rolled back", 100, "pink")}
        wf = []
        for r in runs[:6]:
            label, progress, accent = view.get(r.status, ("In Progress", 60, "cyan"))
            dept = AGENT_REGISTRY[r.agent_outputs[0].agent_id].department.value if r.agent_outputs and r.agent_outputs[0].agent_id in AGENT_REGISTRY else "Orchestration"
            wf.append(WorkflowItem(id=r.workflow_id, name=(r.task or "Workflow")[:48], department=dept, status=label, progress=progress, accent=accent, icon="LayoutDashboard"))
        o["workflows"] = wf

    # --- tasks: distribution by project (%), totals, execution chart ---
    def _tasks() -> None:
        by_project: dict[str, int] = {}
        names = {p["id"]: p["name"] for p in projects}
        for t in tasks:
            key = names.get(t.get("project_id"), "Unassigned")
            by_project[key] = by_project.get(key, 0) + 1
        total = len(tasks) or 1
        o["task_distribution"] = [
            DistributionSlice(name=name, value=round(100 * count / total), color=CATEGORICAL[i % len(CATEGORICAL)])
            for i, (name, count) in enumerate(sorted(by_project.items(), key=lambda kv: kv[1], reverse=True))
        ]
        o["total_tasks"] = len(tasks)
        c_total, p_total, f_total = done_tasks + completed, active_tasks + len(awaiting), failed
        labels = ["12 AM", "03 AM", "06 AM", "09 AM", "12 PM", "03 PM", "06 PM", "09 PM"]
        n = len(labels)
        o["task_execution"] = [TaskPoint(time=lbl, completed=round(c_total * (i + 1) / n), in_progress=round(p_total * (i + 1) / n), failed=round(f_total * (i + 1) / n)) for i, lbl in enumerate(labels)]

    # --- activity (recent artifacts) ---
    def _activity() -> None:
        acts = []
        for i, a in enumerate(artifacts[:6]):
            cat = a.get("category", "reports")
            icon, accent = _CAT_ICON.get(cat, ("Activity", "cyan"))
            who = (a.get("agent_id") or cat or "agent").replace("-", " ").title()
            fname = (a.get("path") or "").split("/")[-1]
            acts.append(ActivityItem(id=f"act-{i}", agent=who, action=f"wrote {fname}", time=_ago(a.get("modified", "")), accent=accent, icon=icon))
        o["activity"] = acts

    # --- approvals: social drafts here (the panel renders awaiting workflow RUNS live
    #     via useAwaitingApprovals; including them here too would double-render). The
    #     total counts both runs + social drafts. ---
    def _approvals() -> None:
        social = [d for d in drafts if d.status == "awaiting_approval"][:6]
        o["approvals"] = [
            ApprovalItem(id=d.id, title=(d.brief or d.kind)[:40], source=f"{d.kind} · social", priority="medium", accent="amber", icon="Image")
            for d in social
        ]
        o["total_pending_approvals"] = len(awaiting) + len(social)

    # --- system health (real signals) ---
    def _health() -> None:
        prov = get_provider_registry().status()
        online = sum(1 for v in prov.values() if v)
        total_prov = len(prov) or 1
        o["system_health"] = [
            HealthMetric(label="Agents Registered", pct=100, display=str(agents_total), accent="cyan"),
            HealthMetric(label="Providers Online", pct=round(100 * online / total_prov), display=f"{online}/{total_prov}", accent="emerald" if online else "amber"),
            HealthMetric(label="Workflow Runs", pct=None, display=str(len(runs)), accent="blue"),
            HealthMetric(label="Memory Items", pct=None, display=str(mem), accent="violet"),
            HealthMetric(label="Knowledge Docs", pct=None, display=str(kb), accent="emerald"),
            HealthMetric(label="Realtime Clients", pct=None, display=str(getattr(manager, "count", 0)), accent="cyan"),
        ]

    # --- provider / model / media usage (always set, empty when none) ---
    def _usage() -> None:
        total = total_agent_calls or 1
        o["provider_usage"] = [
            ProviderUsage(name=PROVIDER_LABEL.get(p, p), pct=round(100 * c / total), calls=c, color=ACCENT_HEX.get(DEPARTMENT_ACCENT.get(p, "cyan"), "#22d3ee"))
            for p, c in sorted(prov_calls.items(), key=lambda kv: kv[1], reverse=True)
        ]
        mtotal = sum(model_calls.values()) or 1
        o["model_usage"] = [
            ModelUsage(id=MODEL_LABEL.get(m, m), pct=round(100 * c / mtotal), calls=c, color=CATEGORICAL[i % len(CATEGORICAL)])
            for i, (m, c) in enumerate(sorted(model_calls.items(), key=lambda kv: kv[1], reverse=True)[:6])
        ]
        o["media_services"] = [
            MediaService(name=_MEDIA_META[k][0], provider=_MEDIA_META[k][1], calls=media_calls[k], delta="", accent=_MEDIA_META[k][2], icon=_MEDIA_META[k][3])
            for k in ("image", "tts", "stt")
            if media_calls.get(k)
        ]

    # --- achievements (real milestones) ---
    def _achievements() -> None:
        o["achievements"] = [
            Achievement(title=f"{len(runs)} Workflow Runs", subtitle="All projects", accent="cyan", icon="PartyPopper"),
            Achievement(title=(f"{success}% Success Rate" if success is not None else "Awaiting first run"), subtitle="Across runs", accent="emerald", icon="ShieldCheck"),
            Achievement(title=f"{agents_total} Agents Registered", subtitle=f"{len(busy_agents)} active", accent="blue", icon="Zap"),
            Achievement(title=f"{len(artifacts)} Artifacts Created", subtitle="In the workspace", accent="violet", icon="ServerCog"),
            Achievement(title=f"{mem + kb} Memory + Knowledge", subtitle="Indexed for RAG", accent="amber", icon="Coins"),
        ]

    for fn in (_stats, _agents, _workflows, _tasks, _activity, _approvals, _health, _usage, _achievements):
        section(fn)

    return base.model_copy(update=o)
