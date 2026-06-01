"""Media endpoint tests (stub mode — no provider keys in the test env).

Without HUGGINGFACE_API_KEY / GROQ_API_KEY every media route degrades to a stub:
image + TTS still write a placeholder artifact under reports/media and return a
path, and STT returns a stub transcription. ``conftest`` isolates the workspace.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import app.services.media as media
from app.core.config import Settings
from app.main import app


class _FakeGroq:
    """Stand-in Groq provider: configured, returns fixed audio bytes (no network)."""

    is_configured = True

    def __init__(self, *, fail: bool = False, data: bytes = b"RIFF\x00\x00fake-wav") -> None:
        self._fail = fail
        self._data = data
        self.last_kwargs: dict | None = None

    async def generate_audio(self, **kwargs) -> bytes:
        self.last_kwargs = kwargs
        if self._fail:
            raise RuntimeError("model not available on this account")
        return self._data


class _FakeRegistry:
    def __init__(self, provider: object) -> None:
        self._p = provider

    def get(self, name: str) -> object:  # noqa: ARG002 - always the fake groq
        return self._p


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


def test_tts_synthesizes_real_audio_via_groq(monkeypatch) -> None:
    # With a configured Groq provider, TTS writes a real .wav and reports stub=False —
    # and forwards the configured Orpheus model/voice to the provider.
    fake = _FakeGroq()
    monkeypatch.setattr(media, "get_provider_registry", lambda: _FakeRegistry(fake))
    svc = media.MediaService()

    res = asyncio.run(svc.synthesize("hello world"))
    assert res["stub"] is False
    assert res["path"].endswith(".wav") and res["path"].startswith("reports/media/")
    from app.core.config import get_settings

    assert fake.last_kwargs["model"] == get_settings().groq_tts_model
    assert fake.last_kwargs["voice"] == get_settings().groq_tts_voice  # forwards the configured voice

    rel = asyncio.run(svc.generate_voiceover("voice this"))
    assert rel and rel.endswith(".wav")


def test_tts_degrades_gracefully_on_provider_error(monkeypatch) -> None:
    # A provider/model error (e.g. Orpheus not on the account) must never raise: synthesize
    # falls back to a stub placeholder, and generate_voiceover returns None (silent video).
    monkeypatch.setattr(media, "get_provider_registry", lambda: _FakeRegistry(_FakeGroq(fail=True)))
    svc = media.MediaService()

    res = asyncio.run(svc.synthesize("hello"))
    assert res["stub"] is True and res["note"]
    assert asyncio.run(svc.generate_voiceover("hello")) is None


def test_voiceover_with_note_success(monkeypatch) -> None:
    monkeypatch.setattr(media, "get_provider_registry", lambda: _FakeRegistry(_FakeGroq()))
    svc = media.MediaService()
    rel, note = asyncio.run(svc.voiceover_with_note("narrate this"))
    assert rel and rel.endswith(".wav")
    assert note


def test_voiceover_with_note_surfaces_provider_error(monkeypatch) -> None:
    # A provider error (e.g. Orpheus terms acceptance) must be SURFACED in the note,
    # not swallowed — so the render pipeline can explain why a reel ended up silent.
    monkeypatch.setattr(media, "get_provider_registry", lambda: _FakeRegistry(_FakeGroq(fail=True)))
    svc = media.MediaService()
    rel, note = asyncio.run(svc.voiceover_with_note("x"))
    assert rel is None
    assert "model not available" in note  # the provider's actual message is carried through


def test_tts_settings_default_to_groq_orpheus() -> None:
    # The shipped default wires Groq Orpheus (the registry's text-to-speech model).
    # Assert the declared field default (independent of any local .env override).
    assert Settings.model_fields["groq_tts_model"].default == "canopylabs/orpheus-v1-english"
    assert Settings.model_fields["groq_tts_voice"].default == "autumn"  # valid Groq Orpheus voice
    assert Settings.model_fields["groq_tts_format"].default == "wav"
