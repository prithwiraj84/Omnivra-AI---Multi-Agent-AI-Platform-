"""Orchestrator service — run the CEO->department graph and drive the approval gate.

``run_workflow`` runs the graph until it completes or interrupts at the human approval
gate (LangGraph ``interrupt``). ``resume_workflow`` re-enters a paused run with a human
decision (approve/reject/retry/rollback) via ``Command(resume=...)``. Every run is mapped
to the wire schema :class:`RunResult` and persisted via the WorkflowStore.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from langgraph.types import Command

from app.core.logging import logger
from app.graph.builder import get_compiled_graph
from app.graph.state import OmnivraState, WorkflowStatus, new_state
from app.schemas import AgentRunOutput, PendingApproval, RunResult
from app.services.artifacts import get_artifact_service
from app.services.memory import get_memory_service
from app.services.realtime import emit
from app.services.workflow_store import find_run, get_workflow_store
from app.workspace_fs.paths import safe_project_id


def _persist_artifacts_and_memory(workflow_id: str, task: str, state: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
    """Write each agent output to the project's workspace + store it as recallable memory (RAG)."""
    outputs = get_artifact_service(project_id).persist_run(
        workflow_id, task, state.get("plan", []), state.get("agent_outputs", [])
    )
    memory = get_memory_service(project_id)
    for o in outputs:
        if o.get("ok") and o.get("content"):
            agent_id = o.get("agent_id")
            # Stable id so re-persisting on resume upserts instead of duplicating
            # the same output into the RAG corpus on every approve/retry.
            memory.remember(
                o["content"],
                {"agent_id": agent_id, "workflow_id": workflow_id, "task": task},
                id=f"mem:{workflow_id}:{agent_id}",
            )
    return outputs


def _status_value(state: dict[str, Any]) -> str:
    status = state.get("status", WorkflowStatus.PENDING)
    return status.value if isinstance(status, WorkflowStatus) else str(status)


def _map_result(
    workflow_id: str,
    task: str,
    state: dict[str, Any],
    *,
    project_id: str,
    status_override: str | None = None,
    pending_payload: dict[str, Any] | None = None,
) -> RunResult:
    outputs = [
        AgentRunOutput(
            agent_id=o.get("agent_id", ""),
            content=o.get("content", ""),
            ok=o.get("ok", False),
            tokens=o.get("tokens", 0),
            artifacts=o.get("artifacts", []),
        )
        for o in state.get("agent_outputs", [])
    ]
    pending = pending_payload or state.get("pending_approval")
    pending_approval = (
        PendingApproval(
            approval_id=pending.get("approval_id", ""),
            kind=pending.get("kind", ""),
            summary=pending.get("summary", ""),
            requested_by=pending.get("requested_by", ""),
        )
        if pending
        else None
    )
    return RunResult(
        workflow_id=workflow_id,
        project_id=project_id,
        status=status_override or _status_value(state),
        task=task,
        plan=state.get("plan", []),
        delegations=state.get("delegations", []),
        agent_outputs=outputs,
        recursion_count=state.get("recursion_count", 0),
        result=state.get("result", {}),
        errors=state.get("errors", []),
        pending_approval=pending_approval,
    )


def _interrupt_payload(state: dict[str, Any]) -> dict[str, Any] | None:
    intr = state.get("__interrupt__") if isinstance(state, dict) else None
    if not intr:
        return None
    first = intr[0]
    return getattr(first, "value", None) or (first if isinstance(first, dict) else None)


async def run_workflow(task: str, project_id: str | None = None) -> RunResult:
    """Run the orchestration graph; pause + persist at the approval gate if reached."""
    pid = safe_project_id(project_id)
    workflow_id = "wf_" + uuid4().hex[:12]
    config = {"configurable": {"thread_id": workflow_id}}
    store = get_workflow_store(pid)

    await emit("workflow", {"workflowId": workflow_id, "projectId": pid, "status": "running", "task": task})
    state: dict[str, Any] = await get_compiled_graph().ainvoke(
        new_state(workflow_id=workflow_id, project_id=pid, task=task), config=config
    )

    # Persist each agent output as a workspace artifact (path-jailed) + a run report.
    state["agent_outputs"] = _persist_artifacts_and_memory(workflow_id, task, state, pid)

    payload = _interrupt_payload(state)
    if payload:
        run = _map_result(workflow_id, task, state, project_id=pid, status_override="awaiting_approval", pending_payload=payload)
        await emit(
            "approval",
            {
                "approvalId": payload.get("approval_id", ""),
                "title": "Workflow approval required",
                "kind": payload.get("kind", "final_code"),
                "requestedBy": payload.get("requested_by", "ceo-manager"),
                "priority": payload.get("priority", "high"),
            },
        )
        await emit("workflow", {"workflowId": workflow_id, "projectId": pid, "status": "awaiting_approval"})
    else:
        run = _map_result(workflow_id, task, state, project_id=pid)
        await emit("workflow", {"workflowId": workflow_id, "projectId": pid, "status": run.status, "agents": len(run.agent_outputs)})

    store.save(run)
    return run


async def resume_workflow(workflow_id: str, action: str, note: str | None = None, project_id: str | None = None) -> RunResult:
    """Resume a paused workflow with a human decision (approve/reject/retry/rollback).

    ``project_id`` scopes which project's stores receive the resumed artifacts/memory;
    when omitted it is discovered by scanning all projects for the run.
    """
    pid = safe_project_id(project_id)
    prior = None
    if project_id is None:
        located = find_run(workflow_id)
        if located is not None:
            pid, prior = located
    store = get_workflow_store(pid)
    if prior is None:
        prior = store.get(workflow_id)
    task = prior.task if prior else ""
    config = {"configurable": {"thread_id": workflow_id}}

    try:
        state: dict[str, Any] = await get_compiled_graph().ainvoke(
            Command(resume={"action": action, "note": note}), config=config
        )
    except Exception as exc:  # noqa: BLE001 - e.g. checkpoint lost after a restart (MemorySaver)
        logger.error("Resume failed for {}: {}", workflow_id, exc)
        if prior:
            prior.errors = [*prior.errors, f"Resume failed (state not in memory; needs durable checkpointer): {exc}"]
            store.save(prior)
            return prior
        raise

    state["agent_outputs"] = _persist_artifacts_and_memory(workflow_id, task, state, pid)
    run = _map_result(workflow_id, task, state, project_id=pid)
    await emit("workflow", {"workflowId": workflow_id, "projectId": pid, "status": run.status, "action": action})
    store.save(run)
    return run
