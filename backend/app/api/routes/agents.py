"""Agent routes: list all agents and fetch a single agent by id."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app import schemas
from app.api.deps import get_repo
from app.db.repositories import DashboardRepository

router = APIRouter(tags=["agents"])


@router.get("", response_model=list[schemas.Agent])
def list_agents(repo: DashboardRepository = Depends(get_repo)) -> list[schemas.Agent]:
    """Return all agents (primary + system-ops)."""
    return repo.list_agents()


@router.get("/{agent_id}", response_model=schemas.Agent)
def get_agent(agent_id: str, repo: DashboardRepository = Depends(get_repo)) -> schemas.Agent:
    """Return a single agent by id, 404 when unknown."""
    agent = repo.get_agent(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    return agent
