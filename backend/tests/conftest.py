"""Shared pytest fixtures for the Omnivra backend.

The workspace root is redirected to a temp directory *before* the app is imported,
so the test suite never writes into the real ``workspace/`` sandbox and ``get_settings()``
(which is ``lru_cache``d) picks up the override the first time it is constructed.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

# Redirect the artifact sandbox to a throwaway dir before anything imports app.*
_TMP_WORKSPACE = tempfile.mkdtemp(prefix="omnivra-test-ws-")
os.environ.setdefault("WORKSPACE_ROOT", _TMP_WORKSPACE)
os.environ.setdefault("APP_ENV", "test")


@pytest.fixture(scope="session")
def client() -> Iterator["object"]:
    """A FastAPI TestClient with lifespan (startup/shutdown) actually run."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
