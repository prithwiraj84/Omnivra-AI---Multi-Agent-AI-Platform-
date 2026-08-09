"""Live in-flight agent registry — who is working RIGHT NOW, across every entry point.

The dashboard used to derive "working" purely from LangGraph workflow runs, which meant an
agent was only ever shown as active if a *workflow* was driving it. But three of the busiest
paths never create a run record at all:

  * Document Studio  (documentation-specialist writing a deck/doc)
  * Social Studio    (reel-automation / social-strategist drafting + rendering)
  * any direct media / one-off agent call

So the user would watch a document generate for thirty seconds while every agent on the
dashboard sat there reading "Idle". This registry closes that gap at the ONE place every LLM
call funnels through (`agents.runner.run_agent`), so a new caller can never reintroduce the bug
by forgetting to report itself.

Process-local and best-effort, like `usage.py`: it resets on restart, which is correct — nothing
is actually running after a restart either.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

from app.services.provider_keys import current_key_owner

# A call that never returns (hard kill mid-flight) would otherwise pin an agent to "working"
# forever. Entries older than this stop counting, so the dashboard self-heals.
STALE_AFTER_SECONDS = 600.0

_lock = threading.Lock()
# (owner, agent_id) -> [depth, first_started_monotonic]. Depth, not a bool: the same agent can be
# invoked concurrently (e.g. per-scene narration), and the last one to finish must clear it.
_inflight: dict[tuple[str, str], list[float]] = {}
# Bumped on every start/stop transition. The dashboard's short-TTL cache carries the revision it
# was built at, so a status change invalidates it immediately instead of being hidden for the
# rest of the TTL — otherwise a fast agent could start AND finish inside one cached window.
_revision = 0


def revision() -> int:
    """A counter that changes whenever any agent starts or stops working."""
    with _lock:
        return _revision


def _key(agent_id: str, owner: str | None) -> tuple[str, str]:
    return (owner or current_key_owner(), agent_id)


def begin(agent_id: str, owner: str | None = None) -> bool:
    """Mark ``agent_id`` as working. Returns True if this STARTED the agent (0 -> 1)."""
    global _revision
    k = _key(agent_id, owner)
    with _lock:
        entry = _inflight.get(k)
        if entry is None or entry[0] <= 0:
            _inflight[k] = [1, time.monotonic()]
            _revision += 1
            return True
        entry[0] += 1
        return False


def end(agent_id: str, owner: str | None = None) -> bool:
    """Mark one call finished. Returns True if this STOPPED the agent (1 -> 0)."""
    global _revision
    k = _key(agent_id, owner)
    with _lock:
        entry = _inflight.get(k)
        if entry is None:
            return False
        entry[0] -= 1
        if entry[0] <= 0:
            _inflight.pop(k, None)
            _revision += 1
            return True
        return False


@contextmanager
def working(agent_id: str, owner: str | None = None) -> Iterator[None]:
    """Scope an agent to 'working' for the duration of the block.

    The owner is captured at ENTRY, not exit: `run_agent` may be awaited across a context switch,
    and reading the ContextVar again on the way out could attribute the release to a different
    user and leak a permanently-'working' agent.
    """
    who = owner or current_key_owner()
    begin(agent_id, who)
    try:
        yield
    finally:
        end(agent_id, who)


def active_agents(owner: str | None = None) -> set[str]:
    """Agent ids currently executing for ``owner`` (defaults to the context owner)."""
    who = owner or current_key_owner()
    cutoff = time.monotonic() - STALE_AFTER_SECONDS
    with _lock:
        return {
            agent_id
            for (o, agent_id), (depth, started) in _inflight.items()
            if o == who and depth > 0 and started >= cutoff
        }


def snapshot() -> dict[str, int]:
    """All in-flight agents across owners, for diagnostics/tests."""
    with _lock:
        return {f"{o}:{a}": int(d) for (o, a), (d, _s) in _inflight.items() if d > 0}


def reset() -> None:
    """Drop all state (tests)."""
    global _revision
    with _lock:
        _inflight.clear()
        _revision += 1
