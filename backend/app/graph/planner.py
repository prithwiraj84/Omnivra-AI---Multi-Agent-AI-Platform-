"""Delegation planner — turn a task + CEO narrative into an ordered agent list.

The CEO node calls :func:`plan_delegations` to decide which department agents to
delegate to. It first looks for known agent ids mentioned verbatim in the CEO's
own text; if none are found it falls back to a keyword heuristic over the task.
``solution-architect`` is always delegated first.
"""
from __future__ import annotations

import re

from app.agents.registry import AGENT_REGISTRY

# Ordered (keyword -> agent ids) heuristic. Order matters: earlier matches are
# appended first, which (after de-dup) gives a sensible delegation order.
_KEYWORD_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("design", "ui", "ux", "wireframe", "landing page"), ("uiux-designer", "frontend-engineer")),
    (("api", "endpoint", "contract", "rest"), ("api-engineer", "backend-engineer")),
    (("backend", "service", "business logic"), ("backend-engineer",)),
    (("database", "schema", "sql", "migration", "pgvector"), ("database-engineer",)),
    (("security", "audit", "threat", "hardening"), ("secops-engineer",)),
    (("test", "qa", "validation"), ("qa-engineer",)),
    (("doc", "readme", "guide"), ("documentation-agent",)),
    (("present", "deck", "pitch", "slide"), ("presentation-designer",)),
    (("market", "seo", "social", "campaign"), ("seo-researcher", "social-strategist")),
    (("frontend", "react", "component"), ("frontend-engineer",)),
]

_FALLBACK = ("solution-architect", "backend-engineer", "frontend-engineer")
_MAX = 5


def _extract_mentioned_agents(text: str) -> list[str]:
    """Return known agent ids that appear verbatim in ``text`` (registration order)."""
    if not text:
        return []
    lowered = text.lower()
    found: list[str] = []
    for agent_id in AGENT_REGISTRY:
        # Match the id as a whole token (kebab-case id treated as a literal).
        if re.search(rf"(?<![\w-]){re.escape(agent_id)}(?![\w-])", lowered):
            found.append(agent_id)
    return found


def _matches(keyword: str, text: str) -> bool:
    """Whole-word (boundary-aware) keyword match to avoid substring false positives.

    e.g. 'ui' must not match inside 'build'; 'design' still matches 'designing'
    because the boundary is on word edges, so we treat the keyword as a prefix at
    a word start.
    """
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}", text) is not None


def _keyword_agents(task: str) -> list[str]:
    """Derive agent ids from keyword rules applied to ``task``."""
    lowered = (task or "").lower()
    picked: list[str] = []
    for keywords, agents in _KEYWORD_RULES:
        if any(_matches(kw, lowered) for kw in keywords):
            picked.extend(agents)
    return picked


def _dedup_known_capped(ids: list[str]) -> list[str]:
    """De-duplicate (preserving order), drop unknown ids, and cap at ``_MAX``."""
    seen: set[str] = set()
    out: list[str] = []
    for agent_id in ids:
        if agent_id in AGENT_REGISTRY and agent_id not in seen:
            seen.add(agent_id)
            out.append(agent_id)
        if len(out) >= _MAX:
            break
    return out


def plan_delegations(task: str, ceo_text: str) -> list[str]:
    """Derive an ORDERED list (length 2-5) of agent ids to delegate to.

    Strategy:
      1. Use any known agent ids mentioned in ``ceo_text``.
      2. Otherwise apply a keyword heuristic to ``task``.
      3. Always prepend ``solution-architect``; de-dup; cap at 5.
      4. Fall back to a sane default trio if the result would be empty.
    """
    derived = _extract_mentioned_agents(ceo_text) or _keyword_agents(task)

    candidates = ["solution-architect", *derived]
    plan = _dedup_known_capped(candidates)

    if not plan:
        plan = _dedup_known_capped(list(_FALLBACK))

    # Guarantee a minimum useful breadth (length 2-5).
    if len(plan) < 2:
        for agent_id in _FALLBACK:
            if agent_id not in plan:
                plan.append(agent_id)
            if len(plan) >= 2:
                break

    return plan[:_MAX]
