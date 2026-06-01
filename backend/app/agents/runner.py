"""Agent runner — turns an AgentSpec + a task into an LLM call via its provider.

The LangGraph nodes call :func:`run_agent`. With a configured provider this makes a
real LLM call (tenacity-retried in the provider); without a key the provider returns
a deterministic stub, so the whole graph runs offline.
"""
from __future__ import annotations

from app.agents.registry import AgentSpec, get_agent
from app.core.logging import logger
from app.graph.state import AgentOutput
from app.providers.base import CompletionRequest
from app.providers.registry import ProviderRegistry
from app.services.usage import record_agent_call


def build_system_prompt(spec: AgentSpec) -> str:
    """Role/system prompt that frames an agent for its provider."""
    responsibilities = ", ".join(spec.responsibilities) or "your area of expertise"
    return (
        f"You are the {spec.name}, the {spec.department.value} specialist at Omnivra, "
        f"an autonomous AI software company. Your responsibilities: {responsibilities}. "
        "Produce concrete, professional, well-structured output for the task. Be concise."
    )


async def run_agent(
    agent_id: str,
    task: str,
    *,
    registry: ProviderRegistry,
    context: str = "",
    max_tokens: int = 512,
) -> AgentOutput:
    """Run a single agent against ``task`` and return its normalized output.

    Never raises: provider failures are caught and returned as ``ok=False`` so one
    failed delegation cannot crash the whole workflow.
    """
    spec = get_agent(agent_id)
    provider = registry.get(spec.provider)

    messages: list[dict[str, str]] = [{"role": "system", "content": build_system_prompt(spec)}]
    if context:
        messages.append({"role": "user", "content": f"Context from earlier steps:\n{context}"})
    messages.append({"role": "user", "content": task})

    request = CompletionRequest(model=spec.model, messages=messages, max_tokens=max_tokens)
    try:
        resp = await provider.complete(request)
        record_agent_call(spec.provider, spec.model)  # real session usage for the dashboard
        return AgentOutput(
            agent_id=agent_id,
            content=resp.text,
            artifacts=[],
            tokens=resp.completion_tokens or 0,
            ok=True,
        )
    except Exception as exc:  # noqa: BLE001 - record failure, keep the workflow alive
        logger.error("Agent {} failed: {}", agent_id, exc)
        return AgentOutput(agent_id=agent_id, content=f"[error] {exc}", artifacts=[], tokens=0, ok=False)
