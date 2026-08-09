"""Error Log tests (cp-0071): every WARNING+ becomes a user-visible, classified record.

The capture is a loguru sink — the one funnel every subsystem already logs through — so the
key properties are: nothing needs to opt in, categories are user-meaningful, repeats coalesce,
records are owner-scoped, and the capture itself can never break the app.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.logging import logger
from app.services import error_log


@pytest.fixture(autouse=True)
def _clean() -> None:
    error_log.install()  # idempotent; the app lifespan installs it too
    error_log.reset()
    yield
    error_log.reset()


# --- capture at the funnel ----------------------------------------------------------------


def test_logger_warning_and_error_are_captured() -> None:
    logger.warning("something soft failed")
    logger.error("something hard failed")
    out = error_log.list_errors(all_owners=True)
    assert out["total"] == 2
    levels = {i["message"]: i["level"] for i in out["items"]}
    assert levels["something soft failed"] == "warning"
    assert levels["something hard failed"] == "error"


def test_info_level_is_not_captured() -> None:
    logger.info("routine chatter must not clutter the error log")
    assert error_log.list_errors(all_owners=True)["total"] == 0


def test_install_is_idempotent() -> None:
    """configure_logging can run more than once (tests, reloads); a duplicate sink would
    double-count every error."""
    error_log.install()
    error_log.install()
    logger.warning("count me once")
    out = error_log.list_errors(all_owners=True)
    assert out["total"] == 1 and out["items"][0]["count"] == 1


def test_exception_detail_is_attached() -> None:
    try:
        raise ValueError("the underlying cause")
    except ValueError:
        logger.exception("operation blew up")
    item = error_log.list_errors(all_owners=True)["items"][0]
    assert item["level"] == "error"
    assert "ValueError" in item["detail"] and "the underlying cause" in item["detail"]


# --- classification: categories a user can act on -----------------------------------------


@pytest.mark.parametrize(
    ("module", "message", "expected"),
    [
        ("app.providers.openrouter", "429: too many requests", "rate_limit"),
        ("app.services.media", "Rate limit exceeded for playai-tts", "rate_limit"),
        ("app.providers.groq", "model_not_found for llama-x", "llm"),
        ("app.agents.runner", "Agent qa-engineer failed: empty response", "llm"),
        ("app.services.elevenlabs_tts", "voice needs a paid plan", "auth"),
        ("app.services.google_tts", "response carried no audio", "media"),
        ("app.services.reel_render", "moviepy assemble failed", "render"),
        ("app.services.publishers", "youtube upload rejected", "publish"),
        ("app.services.documents", "draft could not be completed", "documents"),
        ("app.api.deps", "Not authenticated", "auth"),
        ("app.somewhere", "401 unauthorized from provider", "auth"),
        ("app.somewhere", "connection timed out after 60s", "network"),
        ("app.somewhere", "unexpected KeyError in handler", "system"),
    ],
)
def test_classification(module: str, message: str, expected: str) -> None:
    assert error_log._classify(module, message) == expected


def test_rate_limit_wins_over_subsystem() -> None:
    """A 429 from the LLM stack is actionable as a RATE LIMIT (wait / pool keys), not as a
    generic LLM failure — the category is the advice."""
    assert error_log._classify("app.providers.groq", "429 rate limit hit") == "rate_limit"
    assert error_log._classify("app.services.elevenlabs_tts", "quota exceeded") == "rate_limit"


# --- coalescing ---------------------------------------------------------------------------


def test_repeats_coalesce_into_one_row() -> None:
    """A retry storm must read as one row ×N, not fill the whole log."""
    for _ in range(5):
        error_log.record("WARNING", "OpenRouter exhausted", module="app.providers.openrouter", source="s")
    out = error_log.list_errors(all_owners=True)
    assert out["total"] == 1
    assert out["items"][0]["count"] == 5


def test_different_messages_do_not_coalesce() -> None:
    error_log.record("WARNING", "one thing", source="s")
    error_log.record("WARNING", "another thing", source="s")
    assert error_log.list_errors(all_owners=True)["total"] == 2


# --- owner scoping ------------------------------------------------------------------------


def test_errors_are_scoped_per_owner() -> None:
    """One user's failures must not appear in another user's log."""
    error_log.record("ERROR", "user A's provider died", owner="user-a")
    error_log.record("ERROR", "user B's render died", owner="user-b")
    a = error_log.list_errors("user-a")
    assert a["total"] == 1 and a["items"][0]["message"] == "user A's provider died"
    assert error_log.list_errors("user-b")["total"] == 1
    assert error_log.list_errors("user-c")["total"] == 0
    # open/single-admin mode sees everything
    assert error_log.list_errors(all_owners=True)["total"] == 2


def test_owner_is_never_serialized() -> None:
    """The wire shape must not leak whose record it is (the response is already scoped)."""
    error_log.record("ERROR", "x", owner="user-a")
    item = error_log.list_errors("user-a")["items"][0]
    assert "owner" not in item and not any(k.startswith("_") for k in item)


def test_clear_is_scoped_too() -> None:
    error_log.record("ERROR", "a's", owner="user-a")
    error_log.record("ERROR", "b's", owner="user-b")
    assert error_log.clear("user-a") == 1
    assert error_log.list_errors("user-a")["total"] == 0
    assert error_log.list_errors("user-b")["total"] == 1


# --- the API ------------------------------------------------------------------------------


def test_errors_endpoint_returns_classified_records(client: TestClient) -> None:
    logger.warning("Groq TTS failed (429 rate limit); trying the next engine")
    body = client.get("/api/system/errors").json()
    assert body["total"] >= 1
    top = body["items"][0]
    assert top["category"] == "rate_limit"
    assert top["level"] == "warning"
    assert body["counts"].get("rate_limit", 0) >= 1


def test_errors_endpoint_clears(client: TestClient) -> None:
    logger.error("to be cleared")
    assert client.get("/api/system/errors").json()["total"] >= 1
    cleared = client.delete("/api/system/errors").json()["cleared"]
    assert cleared >= 1
    assert client.get("/api/system/errors").json()["total"] == 0


def test_errors_endpoint_respects_limit(client: TestClient) -> None:
    for i in range(6):
        error_log.record("ERROR", f"distinct error {i}", source=f"s{i}")
    body = client.get("/api/system/errors", params={"limit": 3}).json()
    assert len(body["items"]) == 3
    assert body["total"] == 6, "total reports everything even when items are limited"


def test_unhandled_route_exception_lands_in_the_log(client: TestClient) -> None:
    """The middleware leg: a crash in any endpoint must surface here, not just in uvicorn's
    console. /workspace/artifacts with a path-jail violation 400s (handled); to get a real
    unhandled crash we log through the same funnel the middleware uses."""
    logger.exception("Unhandled error on POST /api/example")
    body = client.get("/api/system/errors").json()
    assert any("Unhandled error" in i["message"] for i in body["items"])


def test_captured_error_pushes_a_realtime_frame(monkeypatch) -> None:
    """The live leg: an error logged INSIDE the event loop (i.e. inside a request handler)
    must schedule an 'error_log' broadcast, so the UI refreshes the moment something fails
    instead of on the next poll."""
    import asyncio

    from app.services import realtime

    sent: list[tuple[str, dict]] = []

    async def fake_emit(event_type: str, payload: dict) -> None:
        sent.append((event_type, payload))

    monkeypatch.setattr(realtime, "emit", fake_emit)

    async def go() -> None:
        logger.error("live frame probe")  # sink runs synchronously, schedules the emit task
        await asyncio.sleep(0.02)  # let the scheduled task actually run

    asyncio.run(go())
    frames = [p for t, p in sent if t == "error_log"]
    assert frames, "no realtime frame was broadcast for a captured error"
    assert frames[0]["level"] == "error" and frames[0]["category"]


def test_capture_outside_a_loop_skips_realtime_but_still_records() -> None:
    """Worker-thread contexts (renders, thread pools) have no running loop — the frame is
    skipped (polling covers it) and recording must still succeed without raising."""
    logger.warning("recorded from a plain thread")
    assert error_log.list_errors(all_owners=True)["total"] == 1
