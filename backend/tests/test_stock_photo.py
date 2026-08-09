"""Stock-photo image fallback (cp-0076).

Generation engines fail routinely — hf-inference retires models without warning and Gemini's
free image quota is small — and a placeholder .txt is a bad deliverable for a post the user is
about to publish. A licensed Pexels photograph is the last real option before the stub.

Pexels rather than scraping a search engine, deliberately: this pipeline PUBLISHES to
Instagram/LinkedIn/YouTube, so image rights are a live exposure and Pexels' license explicitly
permits commercial use; and it's an API, so it needs no browser engine on a shared host.
"""
from __future__ import annotations

import asyncio

import pytest

from app.services import media as media_mod
from app.services import pexels


# --- prompt -> search query ----------------------------------------------------------------
# The whole difference between a RELEVANT photo and zero results.


def test_boilerplate_and_styling_words_are_stripped() -> None:
    q = pexels.photo_query(
        "High-quality social media marketing image for: Launch our AI company OS to founders. "
        "Clean, modern, brand-forward, vibrant."
    )
    for dead in ("high", "quality", "social", "media", "marketing", "clean", "modern", "vibrant"):
        assert dead not in q.split(), f"{dead!r} should not reach the search"
    assert "launch" in q and "company" in q


def test_query_keeps_prompt_order_and_is_capped() -> None:
    """Subjects come before modifiers in a prompt, and Pexels matches 2-4 words best."""
    q = pexels.photo_query("bakery storefront morning bread pastry counter display window")
    assert q.split() == ["bakery", "storefront", "morning", "bread"]
    assert len(pexels.photo_query("a b c d e f g h i j k").split()) <= 4


def test_stopwords_short_words_and_duplicates_are_dropped() -> None:
    q = pexels.photo_query("the of a to in on at by dog dog running")
    assert q.split() == ["dog", "running"]


def test_unsearchable_prompt_degrades_to_a_generic_visual_query() -> None:
    """Pexels only indexes English, so a Devanagari prompt would match nothing — a generic
    query still yields a usable image instead of an empty result."""
    assert pexels.photo_query("पायथन प्रोग्रामिंग कैसे सीखें") == pexels._GENERIC_QUERY
    assert pexels.photo_query("") == pexels._GENERIC_QUERY
    assert pexels.photo_query("clean modern vibrant 4k") == pexels._GENERIC_QUERY


# --- picking a usable photo -----------------------------------------------------------------


def test_picks_the_largest_publishable_photo() -> None:
    photos = [
        {"width": 400, "height": 300, "src": {"large": "small.jpg"}},
        {"width": 3000, "height": 2000, "src": {"large": "big.jpg"}},
        {"width": 1200, "height": 800, "src": {"large": "mid.jpg"}},
    ]
    assert pexels._pick_photo(photos)["src"]["large"] == "big.jpg"


def test_falls_back_to_a_small_photo_rather_than_nothing() -> None:
    assert pexels._pick_photo([{"width": 300, "height": 200, "src": {"large": "tiny.jpg"}}]) is not None


def test_photos_without_a_usable_src_are_skipped() -> None:
    assert pexels._pick_photo([{"width": 4000, "height": 3000, "src": {}}]) is None
    assert pexels._pick_photo([]) is None


# --- fetch_photo --------------------------------------------------------------------------


def test_fetch_photo_is_a_no_op_without_a_key(monkeypatch) -> None:
    monkeypatch.setattr(pexels, "is_configured", lambda: False)
    assert asyncio.run(pexels.fetch_photo("anything")) is None


def test_fetch_photo_broadens_the_query_before_giving_up(monkeypatch) -> None:
    """A 4-word search can be too specific to match anything; broadening keeps the deliverable
    real instead of dropping to a placeholder."""
    tried: list[str] = []

    async def fake_search(query: str, _orientation: str):
        tried.append(query)
        # Only the 2-word broadening matches.
        if len(query.split()) == 2:
            return [{"width": 2000, "height": 1200, "src": {"large": "http://x/p.jpg"}, "photographer": "Ada"}]
        return []

    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "_search_photos", fake_search)
    monkeypatch.setattr(pexels.httpx, "AsyncClient", _fake_client(b"\xff\xd8\xffJPEG"))

    got = asyncio.run(pexels.fetch_photo("bakery storefront morning bread"))
    assert got is not None
    data, credit = got
    assert data.startswith(b"\xff\xd8\xff")
    assert "Ada" in credit and "Pexels" in credit
    assert len(tried) == 2 and len(tried[1].split()) == 2, tried


def test_fetch_photo_never_raises_on_a_provider_error(monkeypatch) -> None:
    async def boom(_q, _o):
        raise RuntimeError("pexels down")

    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "_search_photos", boom)
    assert asyncio.run(pexels.fetch_photo("anything")) is None


# --- the image chain ------------------------------------------------------------------------


def _dead_hf(exc: Exception):
    class _HF:
        is_configured = True

        async def generate_image(self, **_kw):
            raise exc

    return type("R", (), {"get": staticmethod(lambda _n: _HF())})()


def test_stock_photo_rescues_a_post_when_every_generator_is_down(monkeypatch, tmp_path) -> None:
    """The reported situation: hf-inference 410s and Gemini is out of quota. The post gets a
    real photo instead of a placeholder .txt."""
    from app.providers.base import FatalProviderError
    from app.services import google_image

    async def fake_photo(_prompt, **_kw):
        return b"\xff\xd8\xffJPEGBYTES", "Ada Lovelace on Pexels"

    monkeypatch.setattr(media_mod, "get_provider_registry", lambda: _dead_hf(FatalProviderError("410: deprecated")))
    monkeypatch.setattr(google_image, "is_configured", lambda: False)
    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "fetch_photo", fake_photo)

    out = asyncio.run(media_mod.MediaService().generate_image("a bakery storefront", "default"))
    assert out["stub"] is False
    assert out["path"].endswith(".jpg")
    # The note must NOT imply the image was generated — a photo is not generated art.
    assert "Stock photo" in out["note"] and "Ada Lovelace" in out["note"]


def test_a_working_generator_is_never_replaced_by_stock(monkeypatch) -> None:
    """Regression guard: stock is a FALLBACK. Generated art must always win."""
    used: list[str] = []

    class _HF:
        is_configured = True

        async def generate_image(self, **_kw):
            used.append("hf")
            return b"\x89PNG\r\n\x1a\n"

    async def fake_photo(_prompt, **_kw):
        used.append("pexels")
        return b"x", "nobody"

    monkeypatch.setattr(media_mod, "get_provider_registry", lambda: type("R", (), {"get": staticmethod(lambda _n: _HF())})())
    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "fetch_photo", fake_photo)

    out = asyncio.run(media_mod.MediaService().generate_image("anything", "default"))
    assert used == ["hf"], "Pexels must not be consulted when generation succeeded"
    assert "Hugging Face" in out["note"] and out["path"].endswith(".png")


def test_stub_still_happens_when_nothing_at_all_is_configured(monkeypatch) -> None:
    from app.services import google_image

    class _Off:
        is_configured = False

    monkeypatch.setattr(media_mod, "get_provider_registry", lambda: type("R", (), {"get": staticmethod(lambda _n: _Off())})())
    monkeypatch.setattr(google_image, "is_configured", lambda: False)
    monkeypatch.setattr(pexels, "is_configured", lambda: False)

    out = asyncio.run(media_mod.MediaService().generate_image("anything", "default"))
    assert out["stub"] is True
    assert "Pexels" in out["note"], "the stub must name stock photos as an option too"


# --- helpers --------------------------------------------------------------------------------


def _fake_client(payload: bytes):
    """An httpx.AsyncClient stand-in whose GET returns ``payload``."""

    class _Resp:
        content = payload

        @staticmethod
        def raise_for_status() -> None:
            return None

    class _Client:
        def __init__(self, *a, **k) -> None: ...

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a) -> None:
            return None

        async def get(self, *_a, **_k):
            return _Resp()

    return _Client


# --- bounded + honest -----------------------------------------------------------------------


def test_fetch_photo_is_bounded_by_a_total_budget(monkeypatch) -> None:
    """Post drafting is on the REQUEST path and has already spent time failing two generators.
    Retries x broadening attempts could otherwise outlast the browser's own timeout."""
    async def slow(_q, _o):
        await asyncio.sleep(30)
        return []

    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "_search_photos", slow)
    monkeypatch.setattr(pexels, "_PHOTO_BUDGET_SECONDS", 0.2)

    async def run():
        loop = asyncio.get_running_loop()
        started = loop.time()
        got = await pexels.fetch_photo("anything")
        return got, loop.time() - started

    got, elapsed = asyncio.run(run())
    assert got is None
    assert elapsed < 5, f"budget not enforced (took {elapsed:.1f}s)"


def test_a_non_image_body_is_rejected_rather_than_saved(monkeypatch) -> None:
    """raise_for_status catches 4xx/5xx, but a 200 carrying an HTML interstitial would be
    written as a .png and render as a silently broken image."""
    async def fake_search(_q, _o):
        return [{"width": 2000, "height": 1200, "src": {"large": "http://x/p.jpg"}, "photographer": "Ada"}]

    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "_search_photos", fake_search)
    monkeypatch.setattr(pexels.httpx, "AsyncClient", _fake_client(b"<!doctype html><html>nope</html>"))
    assert asyncio.run(pexels.fetch_photo("anything")) is None


def test_one_dead_query_does_not_abort_the_broadening_walk(monkeypatch) -> None:
    calls: list[str] = []

    async def flaky(query: str, _o):
        calls.append(query)
        if len(calls) == 1:
            raise RuntimeError("transient blip")
        return [{"width": 1500, "height": 1000, "src": {"large": "http://x/p.jpg"}, "photographer": "Grace"}]

    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "_search_photos", flaky)
    monkeypatch.setattr(pexels.httpx, "AsyncClient", _fake_client(b"\xff\xd8\xffJPEG"))

    got = asyncio.run(pexels.fetch_photo("bakery storefront morning bread"))
    assert got is not None and "Grace" in got[1]
    assert len(calls) == 2


def test_attempts_are_deduplicated(monkeypatch) -> None:
    """A one-word prompt must not spend two attempts searching the identical query."""
    seen: list[str] = []

    async def record(query: str, _o):
        seen.append(query)
        return []

    monkeypatch.setattr(pexels, "is_configured", lambda: True)
    monkeypatch.setattr(pexels, "_search_photos", record)
    asyncio.run(pexels.fetch_photo("bakery"))
    assert len(seen) == len(set(seen)), seen


def test_post_artifact_records_the_image_provenance(client) -> None:
    """A published post should still be able to say where its image came from — the credit must
    live in the durable artifact, not only in a progress note that vanishes."""
    from app.services.artifacts import get_artifact_service

    draft = client.post("/api/social/post", json={"brief": "announce our bakery launch"}).json()
    md = next((a for a in draft["artifacts"] if a.endswith("post.md")), None)
    assert md, draft["artifacts"]
    body = get_artifact_service(draft["projectId"]).read_artifact(md)
    assert "## Image" in body, "post.md must record which engine produced the image"


def test_publishable_rendition_is_preferred_over_the_small_one() -> None:
    """Pexels' `large` is capped at 940x650 — under Instagram's 1080px feed width, so it would
    upscale and soften. `original` is routinely 6000px/4MB and wasteful to fetch and upload."""
    src = {"original": "o.jpg", "large2x": "l2.jpg", "large": "l.jpg", "medium": "m.jpg"}
    assert pexels._photo_url({"src": src}) == "l2.jpg"
    # Degrades in order when the preferred rendition is absent.
    assert pexels._photo_url({"src": {"large": "l.jpg", "medium": "m.jpg"}}) == "l.jpg"
    assert pexels._photo_url({"src": {"original": "o.jpg"}}) == "o.jpg"
    assert pexels._photo_url({"src": {}}) is None
    assert pexels._photo_url({}) is None
