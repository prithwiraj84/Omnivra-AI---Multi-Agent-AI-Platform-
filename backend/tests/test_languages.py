"""Content-language tests (cp-0068): the script and the voice must agree on the language.

The property that actually matters is the routing one: Groq's speech models are ENGLISH-ONLY
and will "read" Devanagari as mangled phonetics instead of erroring, so a Hindi reel reaching
Groq produces confidently wrong audio. These tests pin that door shut, then check the rest of
the plumbing (prompt directive, offline fallback copy, duration parsing, persistence).
"""
from __future__ import annotations

import asyncio
import re

import pytest
from fastapi.testclient import TestClient

from app.services import elevenlabs_tts, google_tts, media as media_mod
from app.services.languages import ENGLISH, HINDI, get_language, language_options, normalize_digits
from app.services.social import SocialService, requested_duration_sec, resolve_language

DEVANAGARI = re.compile(r"[ऀ-ॿ]")


# --- routing: the one that can silently produce garbage ---------------------------------


def test_hindi_never_routes_to_groq() -> None:
    """Groq's playai-tts/Orpheus are English models. Hindi must not list them at all."""
    assert "groq" not in HINDI.tts_chain
    assert HINDI.tts_chain[0] == "elevenlabs", "the natural-sounding engine goes first"
    assert "google" in HINDI.tts_chain, "Hindi needs a FREE engine, and Gemini is the only one"
    assert "groq" in ENGLISH.tts_chain, "English keeps its free fallback"


def test_no_dead_engines_in_any_chain() -> None:
    """Every engine named in a chain must have a handler in MediaService, or a render silently
    skips it. Hugging Face was removed here after its serverless tier dropped all TTS models."""
    handled = {"elevenlabs", "google", "groq"}
    for lang in (ENGLISH, HINDI):
        assert set(lang.tts_chain) <= handled, f"{lang.code} names an engine with no handler"


def test_hindi_with_only_groq_configured_stays_silent_with_an_honest_note(monkeypatch) -> None:
    """A Groq-only account gets NO Hindi audio — and is told exactly which key would fix it,
    rather than a reel narrated in phonetic gibberish."""
    calls: list[str] = []

    class _Groq:
        is_configured = True

        async def generate_audio(self, **_kw):  # noqa: ANN003
            calls.append("groq")
            return b"RIFFshould-never-happen"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: False)
    monkeypatch.setattr(google_tts, "is_configured", lambda: False)
    monkeypatch.setattr(media_mod, "get_provider_registry", lambda: type("R", (), {"get": staticmethod(lambda _n: _Groq())})())

    rel, note = asyncio.run(media_mod.MediaService()._tts("नमस्ते दुनिया", "default", "hi"))

    assert rel is None
    assert calls == [], "Groq must never be asked to speak Hindi"
    assert "English-only" in note, note
    assert "ElevenLabs" in note and "Google AI Studio" in note, note


def test_hindi_prefers_elevenlabs_and_passes_the_language_through(monkeypatch) -> None:
    seen: list[str] = []

    async def fake_synth(text, *, language="en"):  # noqa: ANN001
        seen.append(language)
        return b"ID3fake-mp3"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: True)
    monkeypatch.setattr(elevenlabs_tts, "synthesize", fake_synth)

    rel, note = asyncio.run(media_mod.MediaService()._tts("नमस्ते", "default", "hi"))
    assert rel and rel.endswith(".mp3")
    assert seen == ["hi"], "the engine must be told which language to speak"
    assert "Hindi" in note


def test_hindi_falls_back_to_gemini_when_elevenlabs_is_absent(monkeypatch) -> None:
    """No ElevenLabs key still gets REAL Hindi audio — free, on the Google AI key the LLM
    agents already use. This is the ONLY free engine that speaks Hindi: Groq is English-only
    and Hugging Face's serverless tier hosts no TTS model at all."""
    seen: list[str] = []

    async def fake_google(text, *, language="en"):  # noqa: ANN001
        seen.append(language)
        return b"RIFFfake-wav"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: False)
    monkeypatch.setattr(google_tts, "is_configured", lambda: True)
    monkeypatch.setattr(google_tts, "synthesize", fake_google)

    rel, note = asyncio.run(media_mod.MediaService()._tts("नमस्ते", "default", "hi"))
    assert rel and rel.endswith(".wav")
    assert seen == ["hi"]
    assert "Hindi" in note and "Gemini" in note


def test_english_chain_is_unchanged(monkeypatch) -> None:
    """Regression guard: adding languages must not alter the English path at all."""
    used: list[str] = []

    class _Groq:
        is_configured = True

        async def generate_audio(self, *, text, model, voice, response_format):  # noqa: ANN001
            used.append("groq")
            return b"RIFFgroq-wav"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: False)
    monkeypatch.setattr(google_tts, "is_configured", lambda: False)
    monkeypatch.setattr(media_mod, "get_provider_registry", lambda: type("R", (), {"get": staticmethod(lambda _n: _Groq())})())

    rel, _note = asyncio.run(media_mod.MediaService()._tts("hello", "default"))
    assert rel and used == ["groq"], "Groq must still cover English when nothing else is configured"


# --- ElevenLabs model selection ---------------------------------------------------------


def test_english_only_elevenlabs_model_is_upgraded_for_hindi(monkeypatch) -> None:
    """An English-only model would mangle Devanagari rather than fail, so it gets swapped."""
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "elevenlabs_model", "eleven_monolingual_v1", raising=False)
    assert elevenlabs_tts._model_for("hi") == "eleven_multilingual_v2"
    assert elevenlabs_tts._model_for("en") == "eleven_monolingual_v1", "English keeps the user's choice"


def test_per_language_voice_override(monkeypatch) -> None:
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "elevenlabs_voice_id", "english-voice", raising=False)
    monkeypatch.setattr(s, "elevenlabs_voice_id_hi", "hindi-voice", raising=False)
    assert elevenlabs_tts._configured_voice_for("hi") == "hindi-voice"
    assert elevenlabs_tts._configured_voice_for("en") == "english-voice"

    # With no Hindi-specific voice it falls back to the general one rather than failing.
    monkeypatch.setattr(s, "elevenlabs_voice_id_hi", None, raising=False)
    assert elevenlabs_tts._configured_voice_for("hi") == "english-voice"


# --- language resolution + duration parsing ---------------------------------------------


@pytest.mark.parametrize(
    ("brief", "expected"),
    [
        ("दो मिनट का वीडियो", 120.0),
        ("४५ सेकंड की रील", 45.0),  # Devanagari digits
        ("एक मिनट", 60.0),
        ("45 सेकंड", 45.0),
        ("1 minute video on python", 60.0),  # English still works
        ("90-second clip", 90.0),
        ("no duration here", None),
    ],
)
def test_duration_is_parsed_in_both_scripts(brief: str, expected: float | None) -> None:
    assert requested_duration_sec(brief) == expected


@pytest.mark.parametrize(
    "brief",
    [
        "Reel for Instagram about our launch",  # "Instagr-am"
        "a reel about our team culture",  # "te-am"
        "Promote our new program",  # "progr-am"
        "what this means for you",  # "me-ans"
        "How the platform was built",  # "w-as"
        "buy our phones",  # "ph-ones"
        "a reel about dogs",
    ],
)
def test_ordinary_words_are_not_read_as_a_duration(brief: str) -> None:
    """The bare 'a'/'m'/'s' alternatives must not match INSIDE a word.

    Without a left word boundary "Instagram" parsed as a + m = one minute, so an ordinary
    brief silently produced a 60s reel instead of the 30s default.
    """
    assert requested_duration_sec(brief) is None


def test_a_latin_word_cannot_outrank_the_real_duration() -> None:
    """search() returns the FIRST match, so a false positive early in the string used to
    override the duration the user actually asked for later in it."""
    assert requested_duration_sec("Instagram के लिए 30 सेकंड की रील") == 30.0
    assert requested_duration_sec("हमारे team पर 45 सेकंड की रील") == 45.0
    assert requested_duration_sec("Instagram reel, 30 seconds") == 30.0


def test_hindi_inflected_units_still_parse() -> None:
    """The right-hand guard must not reject Hindi's oblique/plural forms."""
    assert requested_duration_sec("45 सेकंडों में") == 45.0


def test_explicit_language_beats_the_briefs_script() -> None:
    assert resolve_language("en", "नमस्ते दुनिया") == "en", "the user's pick is authoritative"
    assert resolve_language("hi", "hello world") == "hi"
    assert resolve_language(None, "नमस्ते दुनिया") == "hi", "a Devanagari brief infers Hindi"
    assert resolve_language(None, "hello world") == "en"
    assert resolve_language("klingon", "hello") == "en", "an unknown code degrades, never raises"


def test_normalize_digits() -> None:
    assert normalize_digits("४५ सेकंड") == "45 सेकंड"
    assert normalize_digits("45s") == "45s"


# --- offline fallback copy ---------------------------------------------------------------


def test_hindi_fallback_storyboard_is_actually_hindi() -> None:
    sb = SocialService._fallback_storyboard("पायथन कैसे सीखें", 30.0, "hi")
    assert sb.language == "hi"
    assert DEVANAGARI.search(sb.scenes[0].voiceover), "narration must be in Devanagari"
    assert DEVANAGARI.search(sb.call_to_action)


def test_broll_queries_stay_english_even_for_a_hindi_reel() -> None:
    """Pexels only indexes English — a Devanagari search term returns nothing, so the reel
    would silently lose all of its stock footage."""
    sb = SocialService._fallback_storyboard("पायथन प्रोग्रामिंग सीखिए", 40.0, "hi")
    for scene in sb.scenes:
        assert scene.broll_query, "every scene needs a searchable b-roll term"
        assert not DEVANAGARI.search(scene.broll_query), f"b-roll query must be English: {scene.broll_query!r}"


def test_english_fallback_storyboard_is_unchanged() -> None:
    sb = SocialService._fallback_storyboard("Launch our AI company OS", 30.0)
    assert sb.language == "en"
    assert "changes everything" in sb.scenes[0].voiceover


def test_hindi_scripts_are_sized_for_a_slower_spoken_pace() -> None:
    """Hindi words carry more syllables, so the same second holds fewer of them. Sizing a
    Hindi script with English pacing is what makes narration overrun its scene."""
    assert HINDI.words_per_second < ENGLISH.words_per_second


# --- API surface -------------------------------------------------------------------------


def test_languages_endpoint(client: TestClient) -> None:
    res = client.get("/api/social/languages")
    assert res.status_code == 200
    codes = {row["code"] for row in res.json()}
    assert codes == {"en", "hi"}
    assert res.json() == language_options()


def test_draft_reel_in_hindi_persists_the_language(client: TestClient) -> None:
    body = client.post("/api/social/reel", json={"brief": "पायथन कैसे सीखें", "language": "hi"}).json()
    assert body["language"] == "hi"
    # Stored ON the storyboard too, so a re-render months later still picks a Hindi voice.
    assert body["storyboard"]["language"] == "hi"
    assert DEVANAGARI.search(body["storyboard"]["scenes"][0]["voiceover"])

    # And it survives the round-trip through the store.
    again = client.get(f"/api/social/drafts/{body['id']}").json()
    assert again["language"] == "hi" and again["storyboard"]["language"] == "hi"


def test_draft_reel_defaults_to_english(client: TestClient) -> None:
    body = client.post("/api/social/reel", json={"brief": "Launch our AI company OS"}).json()
    assert body["language"] == "en"
    assert body["storyboard"]["language"] == "en"


def test_draft_reel_infers_hindi_from_a_devanagari_brief(client: TestClient) -> None:
    """A user who types entirely in Hindi shouldn't have to find the toggle first."""
    body = client.post("/api/social/reel", json={"brief": "एआई से कंटेंट कैसे बनाएँ"}).json()
    assert body["language"] == "hi"


def test_draft_post_in_hindi(client: TestClient) -> None:
    body = client.post("/api/social/post", json={"brief": "हमारी नई एआई कंपनी", "language": "hi"}).json()
    assert body["language"] == "hi"
    assert DEVANAGARI.search(body["caption"])
    # Hashtags stay Latin so they remain searchable cross-platform.
    assert all(not DEVANAGARI.search(tag) for tag in body["hashtags"])


def test_unknown_language_is_rejected_by_the_schema(client: TestClient) -> None:
    res = client.post("/api/social/reel", json={"brief": "x", "language": "klingon"})
    assert res.status_code == 422


def test_old_drafts_without_a_language_still_load() -> None:
    """Drafts persisted before languages existed must not fail validation."""
    from app.schemas.social import ReelStoryboard, SocialDraft

    draft = SocialDraft(id="reel_x", project_id="p", kind="reel", brief="b", created_at="now")
    assert draft.language == "en"
    assert ReelStoryboard(title="t").language == "en"
    assert get_language(None) is ENGLISH


# --- Gemini TTS: the free multilingual engine -------------------------------------------


def test_gemini_pcm_is_wrapped_in_a_wav_container() -> None:
    """The API returns RAW PCM, not a container. Unwrapped samples are unplayable and ffmpeg
    refuses them, so the reel would render silent with no error anywhere."""
    import io
    import wave

    pcm = b"\x00\x01" * 2400
    data = google_tts._pcm_to_wav(pcm, "audio/L16;codec=pcm;rate=24000")
    assert data[:4] == b"RIFF"
    with wave.open(io.BytesIO(data), "rb") as r:
        assert r.getframerate() == 24_000
        assert r.getnchannels() == 1
        assert r.getsampwidth() == 2
        assert r.getnframes() == 2400


def test_gemini_mime_variants_are_parsed() -> None:
    """The two TTS models report the format differently; assuming one shape resamples the other
    to the wrong rate, which sounds like a chipmunk or a slowed-down drone."""
    import io
    import wave

    for mime, rate in [
        ("audio/L16;codec=pcm;rate=24000", 24_000),
        ("audio/l16; rate=24000; channels=1", 24_000),
        ("audio/l16; rate=16000; channels=1", 16_000),
        ("audio/unknown", 24_000),  # documented default
    ]:
        with wave.open(io.BytesIO(google_tts._pcm_to_wav(b"\x00\x01" * 100, mime)), "rb") as r:
            assert r.getframerate() == rate, mime


def test_gemini_extracts_audio_from_either_payload_casing() -> None:
    """Google's REST payloads use inlineData; some client shapes use inline_data."""
    import base64

    raw = b"\x00\x01\x02\x03"
    b64 = base64.b64encode(raw).decode()
    for key in ("inlineData", "inline_data"):
        payload = {"candidates": [{"content": {"parts": [{key: {"data": b64, "mimeType": "audio/L16;rate=24000"}}]}}]}
        got = google_tts._extract_audio(payload)
        assert got and got[0] == raw

    # A text-only answer (e.g. the model refused) must be "no audio", not a crash.
    assert google_tts._extract_audio({"candidates": [{"content": {"parts": [{"text": "sorry"}]}}]}) is None
    assert google_tts._extract_audio({}) is None


def test_gemini_model_order_puts_the_configured_one_first(monkeypatch) -> None:
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "google_tts_model", "gemini-2.5-flash-preview-tts", raising=False)
    models = google_tts._models()
    assert models[0] == "gemini-2.5-flash-preview-tts"
    assert len(models) == len(set(models)), "no duplicates when the configured model is a known one"

    monkeypatch.setattr(s, "google_tts_model", None, raising=False)
    assert google_tts._models() == list(google_tts._MODELS)


def test_gemini_per_language_voice(monkeypatch) -> None:
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "google_tts_voice", "Charon", raising=False)
    monkeypatch.setattr(s, "google_tts_voice_hi", "Kore", raising=False)
    assert google_tts._voice_for("hi") == "Kore"
    assert google_tts._voice_for("en") == "Charon"
    monkeypatch.setattr(s, "google_tts_voice_hi", None, raising=False)
    assert google_tts._voice_for("hi") == "Charon"


# --- ElevenLabs: free accounts cannot use library voices --------------------------------


def test_elevenlabs_prefers_free_usable_voice_categories() -> None:
    """Picking "the account's first voice" 402s on a free account whose Voice Library entries
    sort first ("Free users cannot use library voices"). Premade must win."""
    import asyncio

    import httpx

    voices = {
        "voices": [
            {"voice_id": "lib-1", "category": "professional", "name": "Library One"},
            {"voice_id": "premade-1", "category": "premade", "name": "Rachel"},
            {"voice_id": "cloned-1", "category": "cloned", "name": "My Clone"},
        ]
    }
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, json=voices))
    async def run():
        async with httpx.AsyncClient(transport=transport) as c:
            return await elevenlabs_tts._voice_candidates(c, "k", "en")

    got = asyncio.run(run())
    assert got[0] == "premade-1", "a free-usable premade voice must be tried first"
    assert "cloned-1" in got
    assert got.index("premade-1") < got.index("cloned-1")
    assert "lib-1" not in got, "paid-only library/professional voices must not be offered"


def test_elevenlabs_falls_back_to_global_defaults_when_listing_fails() -> None:
    """A permission-scoped key can 401 on /v1/voices while still being able to synthesize —
    that must not mute the reel."""
    import asyncio

    import httpx

    transport = httpx.MockTransport(lambda _req: httpx.Response(401, json={"detail": "nope"}))
    async def run():
        async with httpx.AsyncClient(transport=transport) as c:
            return await elevenlabs_tts._voice_candidates(c, "k", "en")

    got = asyncio.run(run())
    assert got, "must still offer the global premade defaults"
    assert set(got) == set(elevenlabs_tts._DEFAULT_VOICE_IDS)
    assert len(got) > 1, "one default is not enough — free-tier access to premade voices varies"


def test_elevenlabs_voice_walk_is_bounded() -> None:
    """Each rejected voice costs a round trip; a scene must not stall discovering that nothing
    on the account is usable."""
    import asyncio

    import httpx

    many = {"voices": [{"voice_id": f"v{i}", "category": "premade"} for i in range(50)]}
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, json=many))
    async def run():
        async with httpx.AsyncClient(transport=transport) as c:
            return await elevenlabs_tts._voice_candidates(c, "k", "en")

    assert len(asyncio.run(run())) <= elevenlabs_tts._MAX_VOICE_ATTEMPTS


def test_elevenlabs_configured_voice_is_tried_before_discovery() -> None:
    import asyncio

    import httpx
    from app.core.config import get_settings

    s = get_settings()
    original = s.elevenlabs_voice_id
    s.elevenlabs_voice_id = "pinned"
    try:
        transport = httpx.MockTransport(
            lambda _req: httpx.Response(200, json={"voices": [{"voice_id": "premade-1", "category": "premade"}]})
        )
        async def run():
            async with httpx.AsyncClient(transport=transport) as c:
                return await elevenlabs_tts._voice_candidates(c, "k", "en")

        assert asyncio.run(run())[0] == "pinned"
    finally:
        s.elevenlabs_voice_id = original
