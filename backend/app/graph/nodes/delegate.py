"""Delegate node — run the CEO's plan sequentially, threading context forward.

Each planned agent runs against the original task with a truncated concatenation
of prior agents' outputs as context, so later specialists can build on earlier
work. All outputs accumulate into ``agent_outputs`` via the state reducer.
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from app.agents.registry import AGENT_REGISTRY, AgentKind, get_agent
from app.agents.runner import is_code_agent, run_agent
from app.core.logging import logger
from app.data.seed import DEPARTMENT_ACCENT
from app.graph.state import AgentOutput, OmnivraState, WorkflowStatus
from app.providers.registry import ProviderRegistry
from app.services.memory import get_memory_service
from app.services.realtime import emit
from app.services.workflow_store import update_run_progress
from app.workspace_fs.paths import DEFAULT_PROJECT

DelegateNode = Callable[[OmnivraState], Awaitable[OmnivraState]]

# Cap the rolling context so prompts stay bounded as delegations accumulate.
_CONTEXT_CHAR_LIMIT = 2000


def _build_context(outputs: list[AgentOutput]) -> str:
    """Concatenate prior outputs into a single context block, truncated."""
    parts: list[str] = []
    for out in outputs:
        content = (out.get("content") or "").strip()
        if content:
            parts.append(f"[{out.get('agent_id', 'agent')}]\n{content}")
    joined = "\n\n".join(parts)
    if len(joined) > _CONTEXT_CHAR_LIMIT:
        joined = joined[-_CONTEXT_CHAR_LIMIT:]
    return joined


def make_delegate_node(registry: ProviderRegistry) -> DelegateNode:
    """Build the async delegate node as a closure over ``registry``."""

    async def delegate_node(state: OmnivraState) -> OmnivraState:
        task = state.get("task", "")
        plan = list(state.get("plan", []))
        pid = state.get("project_id") or DEFAULT_PROJECT
        workflow_id = state.get("workflow_id", "")
        logger.debug("[delegate] plan={}", plan)

        outputs: list[AgentOutput] = []
        # Seed context with whatever the CEO already produced.
        prior: list[AgentOutput] = list(state.get("agent_outputs", []))

        # RAG: recall relevant memory from THIS project's earlier work (isolated per project).
        memory_block = get_memory_service(pid).recall_context(task, k=3)

        for agent_id in plan:
            # LIVE status: this specialist is the one working RIGHT NOW (polled dashboard reads it).
            update_run_progress(pid, workflow_id, current_agent=agent_id, delegations=plan)
            # Push a live 'workflow' frame so the dashboard updates the card immediately (which agent
            # is working) instead of waiting for the next poll — the UI invalidates the dashboard on this.
            await emit("workflow", {"workflowId": workflow_id, "projectId": pid, "status": "running",
                                    "currentAgent": get_agent(agent_id).name})
            base = _build_context(prior + outputs)
            context = f"{memory_block}\n\n{base}".strip() if memory_block else base
            # Builder agents need a far bigger budget to emit complete code files (512 is prose-sized).
            max_tokens = 2048 if is_code_agent(agent_id) else 512
            out = await run_agent(agent_id, task, registry=registry, context=context, max_tokens=max_tokens)
            outputs.append(out)

            spec = get_agent(agent_id)
            await emit(
                "activity",
                {
                    "id": f"run-{agent_id}",
                    "agent": spec.name,
                    "action": "responded",
                    "time": "just now",
                    "accent": DEPARTMENT_ACCENT.get(spec.department.value, "cyan"),
                    "icon": "Bot",
                },
            )

        # --- System Ops pass -------------------------------------------------------------------
        # The internal SYSTEM agents (classify / route / recall / notify / analyze) are kind=SYSTEM,
        # so the planner never delegates to them and they'd sit idle forever. Run them here — in
        # PARALLEL, best-effort, with a tiny budget — so they genuinely participate and show 'working'.
        # A system agent failure NEVER breaks the build (it's just skipped).
        sys_ids = [aid for aid, spec in AGENT_REGISTRY.items() if spec.kind == AgentKind.SYSTEM]
        if sys_ids:
            sys_context = _build_context(prior + outputs)

            async def _run_system(agent_id: str) -> AgentOutput | None:
                try:
                    update_run_progress(pid, workflow_id, current_agent=agent_id)
                    spec = get_agent(agent_id)
                    await emit("workflow", {"workflowId": workflow_id, "projectId": pid,
                                            "status": "running", "currentAgent": spec.name})
                    result = await run_agent(agent_id, task, registry=registry, context=sys_context, max_tokens=256)
                    await emit("activity", {"id": f"run-{agent_id}", "agent": spec.name, "action": "responded",
                                            "time": "just now",
                                            "accent": DEPARTMENT_ACCENT.get(spec.department.value, "cyan"),
                                            "icon": "Cpu"})
                    return result
                except Exception as exc:  # noqa: BLE001 - a system agent must never break the build
                    logger.debug("system-ops agent {} skipped: {}", agent_id, exc)
                    return None

            sys_outputs = await asyncio.gather(*[_run_system(a) for a in sys_ids])
            outputs.extend([o for o in sys_outputs if o])

        return OmnivraState(
            status=WorkflowStatus.RUNNING,
            agent_outputs=outputs,
            delegations=list(plan),
        )

    return delegate_node
