"""MediaService — stub-safe image / TTS / STT, always writing inside the workspace.

Every method degrades gracefully: when the underlying provider key is missing it
writes a small placeholder artifact (so something still shows up in the Workspace
view) and returns ``stub=True`` with a note explaining what to configure. Writes
reuse :class:`ArtifactService`'s path-jailed FileManager, so media artifacts can
never escape the workspace sandbox (the WORKSPACE RULE).

Real provider calls:
  - Image: HF serverless (configured model + fallbacks; hf-inference retires models
           without warning) -> Gemini image -> stub. Extension picked by magic bytes.
  - STT:   Groq Whisper (whisper-large-v3-turbo) — needs an audio upload + key.
  - TTS:   a per-LANGUAGE engine chain (services/languages.py). English tries ElevenLabs ->
           Gemini -> Groq; Hindi tries ElevenLabs -> Gemini and never Groq, whose playai-tts /
           Orpheus are English-only models that would "read" Devanagari as mangled phonetics
           rather than failing. Degrades to silent / a stub placeholder with a note naming
           exactly which key would fix it.
"""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.providers.base import FatalProviderError
from app.providers.registry import get_provider_registry
from app.services import elevenlabs_tts, google_image, google_tts
from app.services.artifacts import get_artifact_service
from app.services.languages import DEFAULT_LANGUAGE, Language, get_language
from app.services.usage import record_media_call
from app.workspace_fs.paths import DEFAULT_PROJECT

# All media artifacts live under reports/media so they surface in the Workspace view.
_MEDIA_DIR = "reports/media"
_AGENT_ID = "reel-automation"


# --- TTS model fallback ----------------------------------------------------------------------
# Groq accounts differ in which speech models they can use: a model may be retired, gated behind
# a one-time terms acceptance, or simply absent from the plan. A voice ALSO only works with its
# own model family, so a fallback must swap model AND voice together. We try the configured pair
# first, then these, so a reel gets a voiceover instead of rendering mute.
# Image models on the HF serverless tier, tried after the configured one. FLUX.1-schnell is
# deliberately NOT here — hf-inference returns 410 'deprecated' for it now.
_IMAGE_FALLBACK_MODELS: tuple[str, ...] = (
    "stabilityai/stable-diffusion-3-medium-diffusers",
)


def _image_candidates(model: str | None) -> list[str]:
    """The configured image model first, then the known-good fallbacks, de-duplicated."""
    out = [model] if model else []
    return out + [m for m in _IMAGE_FALLBACK_MODELS if m not in out]


_TTS_FALLBACK_PAIRS: tuple[tuple[str, str], ...] = (
    ("playai-tts", "Fritz-PlayAI"),
    ("canopylabs/orpheus-v1-english", "autumn"),
)


def _tts_candidates(model: str | None, voice: str | None) -> list[tuple[str, str]]:
    """The configured (model, voice) first, then the known-good fallbacks, de-duplicated."""
    out: list[tuple[str, str]] = []
    if model and voice:
        out.append((model, voice))
    for pair in _TTS_FALLBACK_PAIRS:
        if pair[0] not in {m for m, _ in out}:
            out.append(pair)
    return out


class MediaService:
    """Generate (or stub) media artifacts inside the workspace sandbox."""

    async def generate_image(self, prompt: str, project_id: str = DEFAULT_PROJECT) -> dict[str, Any]:
        """Generate an image (JPEG/PNG) from ``prompt`` via Hugging Face, or write a stub placeholder.

        Returns ``{"path", "stub", "note"}``. Never raises to the caller: any
        provider/IO failure falls back to a placeholder artifact + ``stub=True``.
        """
        record_media_call("image")
        fm = get_artifact_service(project_id).fm
        provider = get_provider_registry().get("huggingface")
        s = get_settings()
        failures: list[str] = []

        # 1) Hugging Face serverless — trying each model in turn: hf-inference retires models
        #    without warning (FLUX went 410 'deprecated'), and a retired model must roll on to
        #    the next candidate rather than silently degrading every post to a stub.
        if getattr(provider, "is_configured", False):
            for model in _image_candidates(s.huggingface_image_model):
                try:
                    data = await provider.generate_image(prompt=prompt, model=model)  # type: ignore[attr-defined]
                except FatalProviderError as exc:
                    failures.append(f"{model}: {str(exc)[:120]}")
                    logger.warning("Image model {} rejected ({}); trying the next candidate", model, str(exc)[:120])
                    continue
                except Exception as exc:  # noqa: BLE001 - transient/network: stop this engine
                    failures.append(f"huggingface: {str(exc)[:120]}")
                    logger.warning("Image generation via HF failed ({}); trying the next engine", repr(exc))
                    break
                if data:
                    rel = self._write_image(fm, data)
                    return {"path": rel, "stub": False, "note": f"Image generated via Hugging Face {model}."}
                failures.append(f"{model}: returned no image")

        # 2) Gemini image — the Google AI key the agents already use. Free quota is tight, so a
        #    429 here just means "stub this one", not a broken pipeline.
        if google_image.is_configured():
            try:
                data = await google_image.generate(prompt)
                if data:
                    rel = self._write_image(fm, data)
                    return {"path": rel, "stub": False, "note": "Image generated via Google Gemini."}
                failures.append("google: returned no image")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"google: {str(exc)[:120]}")
                logger.warning("Gemini image failed ({}); writing stub", str(exc)[:160])

        why = ("Tried: " + "; ".join(failures)[:300] + ". ") if failures else ""
        note = (
            f"{why}Add a Hugging Face key (stable-diffusion) or a Google AI Studio key (Gemini) "
            "in Integrations to generate real images."
        )
        rel = self._write_placeholder(fm, suffix="txt", body=f"[stub image]\nprompt: {prompt}\n{note}")
        return {"path": rel, "stub": True, "note": note}

    @staticmethod
    def _write_image(fm: Any, data: bytes) -> str:
        """Persist image bytes with the extension their magic bytes say they are."""
        if data[:3] == b"\xff\xd8\xff":
            ext = "jpg"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            ext = "webp"
        else:
            ext = "png"
        rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.{ext}"
        fm.write_bytes(rel, data, agent_id=_AGENT_ID)
        return rel

    async def transcribe(self, filename: str | None) -> dict[str, Any]:
        """Transcribe an audio file (STT). Stubs when the Groq key is unset."""
        record_media_call("stt")
        provider = get_provider_registry().get("groq")
        if getattr(provider, "is_configured", False):
            # A real call needs the uploaded audio bytes, not just a name; until the
            # upload path is wired we still return a stub but flag it as such.
            return {
                "text": "[stub transcription]",
                "stub": True,
                "note": (
                    "Groq Whisper STT (whisper-large-v3-turbo) needs an uploaded audio file; "
                    "filename alone is not enough."
                ),
            }
        return {
            "text": "[stub transcription]",
            "stub": True,
            "note": (
                "Set GROQ_API_KEY and upload audio to enable real Groq Whisper STT "
                "(whisper-large-v3-turbo)."
            ),
        }

    async def voiceover_with_note(
        self, text: str, project_id: str = DEFAULT_PROJECT, language: str = DEFAULT_LANGUAGE
    ) -> tuple[str | None, str]:
        """Synthesize a reel voiceover in ``language``; return ``(rel_path | None, note)``.

        The note explains a miss (no key / terms-acceptance / model access / provider error)
        so the render pipeline can surface WHY a reel ended up silent instead of swallowing it.
        """
        record_media_call("tts")
        return await self._tts(text, project_id, language)

    async def generate_voiceover(
        self, text: str, project_id: str = DEFAULT_PROJECT, language: str = DEFAULT_LANGUAGE
    ) -> str | None:
        """Synthesize a real voiceover into the workspace; rel path or None.

        Returns None (no audio) when no speech engine can serve this language — the reel
        renderer then composes a silent video. Used by the reel render engine.
        """
        rel, _note = await self.voiceover_with_note(text, project_id, language)
        return rel

    async def synthesize(
        self, text: str, project_id: str = DEFAULT_PROJECT, language: str = DEFAULT_LANGUAGE
    ) -> dict[str, Any]:
        """Synthesize speech from ``text`` (TTS); stub placeholder if no engine can serve it."""
        record_media_call("tts")
        rel, note = await self._tts(text, project_id, language)
        if rel:
            return {"path": rel, "stub": False, "note": note}
        fm = get_artifact_service(project_id).fm
        placeholder = self._write_placeholder(fm, suffix="txt", body=f"[stub tts]\ntext: {text}\n{note}")
        return {"path": placeholder, "stub": True, "note": note}

    # --- TTS engine chain ---------------------------------------------------------------
    # Which engines can speak a given language — and in what order — is declared once, per
    # language, in services/languages.py. That's deliberate: Groq's voices are ENGLISH-ONLY
    # models that will happily "read" Devanagari as mangled phonetics instead of failing, so
    # the routing has to be a property of the language rather than a runtime guess here.

    async def _tts(self, text: str, project_id: str, language: str = DEFAULT_LANGUAGE) -> tuple[str | None, str]:
        """Core TTS: synthesize ``text`` in ``language`` into a workspace audio file.

        Returns ``(rel_path | None, note)``. Never raises: an unconfigured key, empty text,
        or any provider/model error returns ``(None, note)`` so callers degrade gracefully
        (silent video / stub placeholder).
        """
        clean = (text or "").strip()
        if not clean:
            return None, "No text to synthesize."

        lang = get_language(language)
        failures: list[str] = []
        engines = {
            "elevenlabs": self._tts_elevenlabs,
            "google": self._tts_google,
            "groq": self._tts_groq,
        }
        for name in lang.tts_chain:
            run = engines.get(name)
            if run is None:  # unknown engine in the table — skip rather than crash a render
                continue
            result = await run(clean, project_id, lang, failures)
            if result:
                return result
        return None, self._no_engine_note(lang, failures)

    async def _tts_elevenlabs(self, text: str, project_id: str, lang: Language, failures: list[str]):
        """ElevenLabs — the natural-sounding engine, and the only one that speaks every language."""
        if not elevenlabs_tts.is_configured():
            return None
        try:
            data = await elevenlabs_tts.synthesize(text, language=lang.code)
        except Exception as exc:  # noqa: BLE001 - degrade to the next engine, never break the caller
            failures.append(f"elevenlabs: {str(exc)[:120]}")
            logger.warning("ElevenLabs TTS failed ({}); trying the next engine", str(exc)[:160])
            return None
        if not data:
            failures.append("elevenlabs: returned no audio")
            return None
        rel = self._write_audio(project_id, data, elevenlabs_tts.AUDIO_EXT)
        return rel, f"{lang.name} voiceover via {elevenlabs_tts.describe(lang.code)}."

    async def _tts_google(self, text: str, project_id: str, lang: Language, failures: list[str]):
        """Gemini TTS — the FREE multilingual engine, on the Google AI key agents already use."""
        if not google_tts.is_configured():
            return None
        try:
            data = await google_tts.synthesize(text, language=lang.code)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"google: {str(exc)[:120]}")
            logger.warning("Gemini TTS failed ({}); trying the next engine", str(exc)[:160])
            return None
        if not data:
            failures.append("google: returned no audio")
            return None
        rel = self._write_audio(project_id, data, google_tts.AUDIO_EXT)
        return rel, f"{lang.name} voiceover via {google_tts.describe(lang.code)}."

    async def _tts_groq(self, text: str, project_id: str, lang: Language, failures: list[str]):
        """Groq speech models (free tier), trying each model+voice pair in turn. English only."""
        provider = get_provider_registry().get("groq")
        if not getattr(provider, "is_configured", False):
            return None
        s = get_settings()
        fmt = s.groq_tts_format or "wav"
        for model, voice in _tts_candidates(s.groq_tts_model, s.groq_tts_voice):
            try:
                data = await provider.generate_audio(  # type: ignore[attr-defined]
                    text=text, model=model, voice=voice, response_format=fmt
                )
            except FatalProviderError as exc:
                # 4xx: this model/voice isn't usable on the account (retired, terms not accepted,
                # no access, or a voice that belongs to a different model family). Try the next
                # candidate instead of going silent — that's the difference between a working
                # voiceover and a mute reel.
                failures.append(f"{model}: {str(exc)[:120]}")
                logger.warning("Groq TTS model {} rejected ({}); trying the next candidate", model, str(exc)[:120])
                continue
            except Exception as exc:  # noqa: BLE001 - transient/network: stop trying this engine
                logger.warning("Groq TTS failed (continuing without audio): {}", repr(exc))
                failures.append(f"groq: {str(exc)[:120]}")
                return None
            if not data:
                failures.append(f"{model}: returned no audio")
                continue
            rel = self._write_audio(project_id, data, fmt)
            note = f"Voiceover via Groq {model} (voice: {voice})."
            if model != s.groq_tts_model:
                note += f" Fell back from {s.groq_tts_model}, which this account can't use."
            return rel, note
        return None

    def _write_audio(self, project_id: str, data: bytes, ext: str) -> str:
        """Persist synthesized audio into the project's media dir; returns the rel path."""
        rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.{ext}"
        get_artifact_service(project_id).fm.write_bytes(rel, data, agent_id=_AGENT_ID)
        return rel

    @staticmethod
    def _no_engine_note(lang: Language, failures: list[str]) -> str:
        """Why there's no audio — naming the engines that COULD serve this language.

        Kept language-aware because the fix differs: English can use the free Groq voices,
        while Hindi cannot (they're English-only models) and needs ElevenLabs or Hugging Face.
        """
        options = {
            "elevenlabs": "an ElevenLabs key (natural-sounding)",
            "google": "a Google AI Studio key (free)",
            "groq": "a Groq key (free)",
        }
        fix = " or ".join(options[e] for e in lang.tts_chain if e in options)
        head = f"No speech engine available for {lang.name} narration."
        if lang.code != DEFAULT_LANGUAGE:
            head += " Groq's voices are English-only, so they can't be used here."
        if not failures:
            return f"{head} Add {fix} in Integrations → API keys."
        note = f"{head} Tried every configured engine and found no usable voice model: {'; '.join(failures)[:280]}. Add {fix} in Integrations."
        if "groq" in lang.tts_chain:
            # Keep the Groq-specific remedy: "model terms not accepted" is by far the most
            # common cause here, and it's fixed on Groq's site, not in our UI.
            note += (
                " For Groq, set GROQ_TTS_MODEL/GROQ_TTS_VOICE to a model your account has, "
                "or accept the model terms at console.groq.com."
            )
        return note

    @staticmethod
    def _write_placeholder(fm: Any, *, suffix: str, body: str) -> str | None:
        """Write a small placeholder artifact under reports/media; return its rel path."""
        rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.{suffix}"
        try:
            fm.write_text(rel, body, agent_id=_AGENT_ID)
            return rel
        except Exception as exc:  # noqa: BLE001 - never raise to the caller
            logger.warning("Placeholder media write failed: {}", repr(exc))
            return None


@lru_cache(maxsize=1)
def get_media_service() -> MediaService:
    """Process-wide MediaService singleton."""
    return MediaService()
