"""Auth routes: report whether auth is required, log in, and identify the caller.

Auth is opt-in (settings.auth_enabled). In open mode /login accepts any username and
issues a token so the SPA has one; when enabled it validates the configured admin creds.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import require_user
from app.core.config import get_settings
from app.core.security import create_token, verify_credentials

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str = ""


class LoginResult(BaseModel):
    token: str
    username: str


class Me(BaseModel):
    username: str


@router.get("/config")
def auth_config() -> dict[str, bool]:
    """Tell the SPA whether a login is required."""
    return {"authEnabled": get_settings().auth_enabled}


@router.post("/login", response_model=LoginResult)
def login(req: LoginRequest) -> LoginResult:
    settings = get_settings()
    if settings.auth_enabled and not verify_credentials(req.username, req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    username = req.username or settings.admin_username
    return LoginResult(token=create_token(username), username=username)


@router.get("/me", response_model=Me)
def me(user: str = Depends(require_user)) -> Me:
    return Me(username=user)
