"""Delegate node — run the CEO's plan sequentially, threading context forward.

Each planned agent runs against the original task with a truncated concatenation
of prior agents' outputs as context, so later specialists can build on earlier
work. All outputs accumulate into ``agent_outputs`` via the state reducer.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from app.agents.registry import get_agent
from app.agents.runner import run_agent
from app.core.logging import logger
from app.data.seed import DEPARTMENT_ACCENT
from app.graph.state import AgentOutput, OmnivraState, WorkflowStatus
from app.providers.registry import ProviderRegistry
from app.services.memory import get_memory_service
from app.services.realtime import emit
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
        logger.debug("[delegate] plan={}", plan)

        outputs: list[AgentOutput] = []
        # Seed context with whatever the CEO already produced.
        prior: list[AgentOutput] = list(state.get("agent_outputs", []))

        # RAG: recall relevant memory from THIS project's earlier work (isolated per project).
        memory_block = get_memory_service(state.get("project_id") or DEFAULT_PROJECT).recall_context(task, k=3)

        for agent_id in plan:
            base = _build_context(prior + outputs)
            context = f"{memory_block}\n\n{base}".strip() if memory_block else base
            out = await run_agent(agent_id, task, registry=registry, context=context)
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

        return OmnivraState(
            status=WorkflowStatus.RUNNING,
            agent_outputs=outputs,
            delegations=list(plan),
        )

    return delegate_node
