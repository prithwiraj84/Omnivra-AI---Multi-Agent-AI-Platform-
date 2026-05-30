"""CEO node — the orchestrator that plans the delegation set.

The CEO agent receives the task, produces a high-level plan narrative, and from
that (plus a keyword heuristic) :func:`app.graph.planner.plan_delegations` derives
the ordered list of department agents that the delegate node will run.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from app.agents.runner import run_agent
from app.core.logging import logger
from app.graph.kill_switch import increment_recursion
from app.graph.planner import plan_delegations
from app.graph.state import OmnivraState, WorkflowStatus
from app.providers.registry import ProviderRegistry

CEONode = Callable[[OmnivraState], Awaitable[OmnivraState]]


def _planning_prompt(task: str) -> str:
    return (
        "As the CEO/Manager of Omnivra, an autonomous AI software company, plan the "
        "execution of the following request. Outline the high-level approach and name "
        "which department specialists should be delegated to.\n\n"
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
        )
        plan = plan_delegations(task, ceo_output.get("content", ""))
        logger.info("[ceo] planned delegations: {}", plan)

        return OmnivraState(
            status=WorkflowStatus.RUNNING,
            current_agent="ceo-manager",
            recursion_count=count,
            plan=plan,
            agent_outputs=[ceo_output],
            delegations=["ceo-manager"],
        )

    return ceo_node
