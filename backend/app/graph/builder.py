"""LangGraph workflow builder — CEO -> department orchestration with a human gate.

    START -> ceo -> guard -(stop)-> END
                       -(go)-> delegate -> approval -(human interrupt)-> ...
                                                    -(approve/retry)-> finalize -> END
                                                    -(reject/rollback)-> END

The graph is compiled WITH a checkpointer so the ``approval`` node can call
LangGraph ``interrupt()`` to suspend mid-run; a human decision resumes it via
``Command(resume=...)`` (see app.services.orchestrator). Nodes that call agents are
closures over a :class:`ProviderRegistry`; ``guard`` is the recursion kill switch.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.kill_switch import check_kill_switch
from app.graph.nodes.approval import make_approval_node
from app.graph.nodes.ceo import make_ceo_node
from app.graph.nodes.delegate import make_delegate_node
from app.graph.nodes.finalize import finalize_node
from app.graph.state import OmnivraState, WorkflowStatus
from app.providers.registry import ProviderRegistry, get_provider_registry

# Process-wide in-memory checkpointer. Enables interrupt/resume within a running
# process. Durable cross-restart resume needs a Postgres checkpointer (Supabase) —
# see docs/SUPABASE_INTEGRATION.md; the WorkflowStore persists run metadata regardless.
_CHECKPOINTER = MemorySaver()


def _after_guard(state: OmnivraState) -> str:
    """Route to END when the kill switch tripped, else continue to delegate."""
    if state.get("status") == WorkflowStatus.STOPPED:
        return "stop"
    return "go"


def _after_approval(state: OmnivraState) -> str:
    """After a resumed decision: reject/rollback end the run, else finalize."""
    if state.get("status") in (WorkflowStatus.FAILED, WorkflowStatus.ROLLED_BACK):
        return "wait"
    return "go"


def build_graph(registry: ProviderRegistry | None = None, *, checkpointer: MemorySaver | None = None):
    """Construct and compile the orchestration graph.

    ``registry`` defaults to the process-wide provider registry. ``checkpointer``
    (required for the approval interrupt/resume) defaults to the shared in-memory saver.
    """
    if registry is None:
        registry = get_provider_registry()
    if checkpointer is None:
        checkpointer = _CHECKPOINTER

    g = StateGraph(OmnivraState)
    g.add_node("ceo", make_ceo_node(registry))
    g.add_node("guard", check_kill_switch)
    g.add_node("delegate", make_delegate_node(registry))
    g.add_node("approval", make_approval_node())
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "ceo")
    g.add_edge("ceo", "guard")
    g.add_conditional_edges("guard", _after_guard, {"stop": END, "go": "delegate"})
    g.add_edge("delegate", "approval")
    g.add_conditional_edges("approval", _after_approval, {"wait": END, "go": "finalize"})
    g.add_edge("finalize", END)

    return g.compile(checkpointer=checkpointer)


@lru_cache(maxsize=1)
def get_compiled_graph():
    """Process-wide compiled graph (default registry + shared checkpointer)."""
    return build_graph()
