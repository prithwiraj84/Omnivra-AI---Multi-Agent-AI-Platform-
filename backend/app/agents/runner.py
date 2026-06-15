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


# Cross-provider fallback chain for TEXT agents: if an agent's own provider is exhausted (all its
# keys rate-limited) or returns empty, retry the SAME prompt on the first CONFIGURED provider here
# (skipping the agent's own). Ordered most-reliable first: an OpenRouter agent fails over to Groq
# then Gemini; a Groq/Gemini agent can in turn spill to OpenRouter as a last resort.
_TEXT_FALLBACKS: tuple[tuple[str, str], ...] = (
    ("groq", "llama-3.3-70b-versatile"),
    ("google_ai", "gemini-3.1-flash-lite"),
    ("openrouter", "z-ai/glm-4.5-air:free"),
)


# Builder agents that should emit real, runnable code FILES (not prose descriptions).
_CODE_AGENTS = {
    "solution-architect", "uiux-designer", "frontend-engineer",
    "backend-engineer", "api-engineer", "database-engineer",
}

_CODE_FILE_INSTRUCTION = (
    " You BUILD real software, so DELIVER actual files — not descriptions. For EVERY file you create, "
    "output a fenced code block whose info line carries the relative path as `name=<path>`, e.g.\n"
    "```python name=app/main.py\n<the complete file contents>\n```\n"
    "Write complete, runnable code with real filenames + extensions (.py/.js/.ts/.tsx/.html/.css/.sql/.json). "
    "No placeholders, no '...'. A short note is fine, but the code files ARE the deliverable."
)


def is_code_agent(agent_id: str) -> bool:
    """True for builder agents expected to emit real code files (drives token budget + persistence)."""
    return agent_id in _CODE_AGENTS


def build_system_prompt(spec: AgentSpec) -> str:
    """Role/system prompt that frames an agent for its provider."""
    responsibilities = ", ".join(spec.responsibilities) or "your area of expertise"
    base = (
        f"You are the {spec.name}, the {spec.department.value} specialist at Omnivra, "
        f"an autonomous AI software company. Your responsibilities: {responsibilities}. "
        "Produce concrete, professional, well-structured output for the task. Be concise."
    )
    return base + _CODE_FILE_INSTRUCTION if spec.id in _CODE_AGENTS else base


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
    primary = registry.get(spec.provider)

    messages: list[dict[str, str]] = [{"role": "system", "content": build_system_prompt(spec)}]
    if context:
        messages.append({"role": "user", "content": f"Context from earlier steps:\n{context}"})
    messages.append({"role": "user", "content": task})

    def _ok(provider_name: str, model: str, resp) -> AgentOutput:
        record_agent_call(provider_name, model)  # real session usage for the dashboard
        return AgentOutput(agent_id=agent_id, content=resp.text, artifacts=[], tokens=resp.completion_tokens or 0, ok=True)

    last_err = "no provider produced content"

    # 1) The agent's own provider/model. Its key pool already rotates across keys internally; here
    #    we add a CROSS-PROVIDER fallback so one provider being exhausted doesn't fail the agent.
    try:
        resp = await primary.complete(CompletionRequest(model=spec.model, messages=messages, max_tokens=max_tokens))
        # Offline/unconfigured -> the deterministic stub (non-empty) is the intended behavior; accept it.
        if (resp.text or "").strip() or not primary.is_configured:
            return _ok(spec.provider, spec.model, resp)
        last_err = "empty response"
        logger.warning("Agent {}: primary {} returned empty content; trying a fallback provider", agent_id, spec.provider)
    except Exception as exc:  # noqa: BLE001
        last_err = repr(exc)
        logger.warning("Agent {}: primary {} failed ({}); trying a fallback provider", agent_id, spec.provider, exc)

    # 2) Cross-provider fallback — only when the primary is actually configured (offline stays stubbed).
    if primary.is_configured:
        for fb_provider, fb_model in _TEXT_FALLBACKS:
            if fb_provider == spec.provider:
                continue
            try:
                fb = registry.get(fb_provider)
            except Exception:  # noqa: BLE001 - unknown provider name
                continue
            if not fb.is_configured:
                continue
            try:
                resp = await fb.complete(CompletionRequest(model=fb_model, messages=messages, max_tokens=max_tokens))
                if (resp.text or "").strip():
                    logger.warning("Agent {}: fell back {} -> {} ({})", agent_id, spec.provider, fb_provider, fb_model)
                    return _ok(fb_provider, fb_model, resp)
            except Exception as exc:  # noqa: BLE001
                last_err = repr(exc)
                continue

    logger.error("Agent {} failed: {}", agent_id, last_err)
    return AgentOutput(agent_id=agent_id, content=f"[error] {last_err}", artifacts=[], tokens=0, ok=False)
