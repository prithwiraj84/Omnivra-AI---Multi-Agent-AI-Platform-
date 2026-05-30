"""Media endpoint tests (stub mode — no provider keys in the test env).

Without HUGGINGFACE_API_KEY / GROQ_API_KEY every media route degrades to a stub:
image + TTS still write a placeholder artifact under reports/media and return a
path, and STT returns a stub transcription. ``conftest`` isolates the workspace.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_image_endpoint_stub_writes_artifact() -> None:
    with TestClient(app) as c:
        resp = c.post("/api/media/image", json={"prompt": "a neon dashboard"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["stub"] is True
        assert body["path"], "a placeholder artifact path must be returned"
        assert body["path"].startswith("reports/media/")
        assert body["note"]

        # The placeholder artifact is actually readable through the workspace API.
        read = c.get(f"/api/workspace/artifacts/{body['path']}")
        assert read.status_code == 200


def test_tts_endpoint_stub() -> None:
    with TestClient(app) as c:
        resp = c.post("/api/media/tts", json={"text": "hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["stub"] is True
        assert body["note"]


def test_stt_endpoint_stub() -> None:
    with TestClient(app) as c:
        resp = c.post("/api/media/stt", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["text"]
        assert body["stub"] is True
