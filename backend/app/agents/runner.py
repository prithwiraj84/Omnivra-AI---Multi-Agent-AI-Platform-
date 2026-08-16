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
from app.services import agent_activity
from app.services.provider_keys import current_key_owner
from app.services.usage import record_agent_call


# Cross-provider fallback chain for TEXT agents: if an agent's own provider is exhausted (all its
# keys rate-limited) or returns empty, retry the SAME prompt on the first CONFIGURED provider here
# (skipping the agent's own). Ordered most-reliable first: an OpenRouter agent fails over to Groq
# then Gemini; a Groq/Gemini agent can in turn spill to OpenRouter as a last resort.
_TEXT_FALLBACKS: tuple[tuple[str, str], ...] = (
    ("groq", "llama-3.3-70b-versatile"),
    ("google_ai", "gemini-3.1-flash-lite"),
    ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"),
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

# Agents that own the thing the user actually LOOKS AT.
_WEB_AGENTS = {"uiux-designer", "frontend-engineer"}

# The delivery contract that makes a generated app OPEN AND RUN, everywhere.
#
# Why this is mandatory rather than a preference: the app is browsed from a hosted deployment
# that cannot launch processes (no Node, no dev server, no npm install — a shared host can't
# expose a localhost port and running generated code there is an AUP risk). A Vite/CRA project
# is SOURCE: it needs a build before a browser can render it, so it previews as a broken page
# or not at all. A no-build page needs nothing but the browser already open in front of the
# user — and it runs identically on their laptop.
_WEB_APP_INSTRUCTION = (
    "\n\nCRITICAL DELIVERY CONTRACT — the app MUST run by opening index.html in a browser, with "
    "NO build step, NO bundler, NO npm install, NO dev server and NO backend required:\n"
    "1. ALWAYS produce `index.html` at the app root. It is the entry point and must be complete "
    "and self-contained enough to render on its own.\n"
    "2. Plain `<script type=\"module\">` + a linked `styles.css`. NEVER emit package.json, vite/"
    "webpack config, JSX/TSX that needs compiling, or bare imports like `import React from "
    "'react'`. If you want React, import it from a CDN URL "
    "(`import React from 'https://esm.sh/react@18.3.1'`) — but vanilla JS is usually better here.\n"
    "3. Persist data with localStorage. Do NOT assume an API exists.\n"
    "4. If the project also has a backend, the page must STILL work standalone: ship realistic "
    "seed data in the JS and only call the API when it is actually reachable, degrading quietly.\n"
    "5. Make it genuinely usable and good-looking: real interactivity, responsive layout, sensible "
    "empty states. It is a product someone will open and use, not a demo skeleton."
)

# The architect frames the build, so it must not plan an architecture the deployment can't run.
_ARCHITECT_WEB_INSTRUCTION = (
    "\n\nDeployment constraint that shapes the design: the frontend MUST be a static, no-build "
    "web app (index.html + styles.css + ES-module JS, opened directly in a browser, state in "
    "localStorage). Plan for that. A backend is optional and must never be REQUIRED for the UI "
    "to run — design the client so it works standalone and enriches itself if an API is present."
)


def is_code_agent(agent_id: str) -> bool:
    """True for builder agents expected to emit real code files (drives token budget + persistence)."""
    return agent_id in _CODE_AGENTS


def build_system_prompt(spec: AgentSpec) -> str:
    """Role/system prompt that frames an agent for its provider."""
    responsibilities = ", ".join(spec.responsibilities) or "your area of expertise"
    prompt = (
        f"You are the {spec.name}, the {spec.department.value} specialist at Omnivra, "
        f"an autonomous AI software company. Your responsibilities: {responsibilities}. "
        "Produce concrete, professional, well-structured output for the task. Be concise."
    )
    if spec.id in _CODE_AGENTS:
        prompt += _CODE_FILE_INSTRUCTION
    if spec.id in _WEB_AGENTS:
        prompt += _WEB_APP_INSTRUCTION
    elif spec.id == "solution-architect":
        prompt += _ARCHITECT_WEB_INSTRUCTION
    return prompt


async def _emit_agent_status(agent_id: str, status: str) -> None:
    """Push a live agent working/idle transition to connected dashboards. Best-effort."""
    try:
        from app.services.realtime import emit

        await emit("agent_activity", {"agentId": agent_id, "status": status})
    except Exception as exc:  # noqa: BLE001 - telemetry must never break an agent call
        logger.debug("agent_activity emit failed: {}", exc)


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

    This is also where an agent is marked LIVE-WORKING for the dashboard. It has to happen
    here rather than in the workflow graph: Document Studio and Social Studio call agents
    directly, without a workflow run, so a run-derived status leaves them showing "Idle" for
    the entire generation. Registering at the single funnel means a future caller cannot
    forget to. Events fire only on 0->1 / 1->0 transitions, so a fan-out of concurrent calls
    to the same agent doesn't spam the socket.
    """
    owner = current_key_owner()
    if agent_activity.begin(agent_id, owner):
        await _emit_agent_status(agent_id, "working")
    try:
        return await _complete_agent(agent_id, task, registry=registry, context=context, max_tokens=max_tokens)
    finally:
        # finally, not a trailing call: a cancelled or crashing agent must still be released,
        # or it stays "working" on the dashboard until the staleness cutoff.
        if agent_activity.end(agent_id, owner):
            await _emit_agent_status(agent_id, "idle")


async def _complete_agent(
    agent_id: str,
    task: str,
    *,
    registry: ProviderRegistry,
    context: str = "",
    max_tokens: int = 512,
) -> AgentOutput:
    """The actual provider call + cross-provider fallback (see run_agent)."""
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
