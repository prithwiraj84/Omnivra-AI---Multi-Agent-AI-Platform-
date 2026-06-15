"""CEO node — the orchestrator that plans the delegation set.

The CEO agent receives the task, produces a high-level plan narrative, and from
that (plus a keyword heuristic) :func:`app.graph.planner.plan_delegations` derives
the ordered list of department agents that the delegate node will run.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from app.agents.registry import get_agent
from app.agents.runner import run_agent
from app.core.logging import logger
from app.graph.kill_switch import increment_recursion
from app.graph.planner import delegatable_agents, plan_delegations
from app.graph.state import OmnivraState, WorkflowStatus
from app.providers.registry import ProviderRegistry
from app.services.workflow_store import update_run_progress
from app.workspace_fs.paths import DEFAULT_PROJECT

CEONode = Callable[[OmnivraState], Awaitable[OmnivraState]]


def _roster() -> str:
    """A compact 'id (department): responsibilities' line per delegatable specialist."""
    lines = []
    for agent_id in delegatable_agents():
        spec = get_agent(agent_id)
        lines.append(f"- {spec.id} ({spec.department.value}): {', '.join(spec.responsibilities)}")
    return "\n".join(lines)


def _planning_prompt(task: str) -> str:
    return (
        "You are the CEO/Manager of Omnivra, an autonomous AI software company. Assemble the team to "
        "deliver the request below by choosing which specialist agents to delegate to. Pick ONLY the "
        "agents genuinely needed (a focused team, usually 3-8) and span the RIGHT departments for the "
        "work (e.g. a software build needs architecture + design + the relevant engineers + QA + "
        "security; a marketing task needs the marketing specialists; a docs task needs documentation). "
        "Order them in a sensible execution sequence.\n\n"
        'Respond with ONLY JSON: {"plan": ["agent-id", ...], "rationale": "one sentence"} using ids '
        "from this roster (use the exact ids):\n"
        f"{_roster()}\n\n"
        f"Request: {task}"
    )


def make_ceo_node(registry: ProviderRegistry) -> CEONode:
    """Build the async CEO node as a closure over ``registry``."""

    async def ceo_node(state: OmnivraState) -> OmnivraState:
        count = increment_recursion(state)
        task = state.get("task", "")
        logger.debug("[ceo] recursion_count={} task={!r}", count, task)

        ceo_output = await run_agent(
            "ceo-manager",
            _planning_prompt(task),
            registry=registry,
            max_tokens=700,  # room for the JSON team list + a one-line rationale
        )
        plan = plan_delegations(task, ceo_output.get("content", ""))
        logger.info("[ceo] planned delegations: {}", plan)

        # LIVE status: record the planned team + mark the CEO as the working agent right now, so the
        # dashboard reflects the run while it is still in flight (the orchestrator finalizes at the end).
        update_run_progress(
            state.get("project_id") or DEFAULT_PROJECT,
            state.get("workflow_id", ""),
            current_agent="ceo-manager",
            delegations=plan,
        )

        return OmnivraState(
            status=WorkflowStatus.RUNNING,
            current_agent="ceo-manager",
            recursion_count=count,
            plan=plan,
            agent_outputs=[ceo_output],
            delegations=["ceo-manager"],
        )

    return ceo_node
