"""Reel render engine (cp-0018) — composes a storyboard into a vertical .mp4.

Import-guarded + degrades gracefully (the WORKSPACE-RULE / offline-first ethos):
  * moviepy NOT installed            -> returns a stub (caller keeps the manifest only).
  * moviepy installed, no API keys   -> a REAL .mp4 from per-scene color backgrounds.
  * + Pexels b-roll / Orpheus audio  -> stock footage + per-scene voiceover, synced.

PER-SCENE composition keeps the Pexels b-roll and the TTS narration in lockstep: each
scene shows its own footage for exactly as long as its own narration plays. There is NO
burned-in subtitle/caption overlay (it broke the render on some font/codec setups and was
redundant with the storyboard preview). This module is pure/sync (CPU work); the
orchestrator runs it off the event loop via asyncio.to_thread.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.core.logging import logger

_W, _H = 1080, 1920  # vertical 9:16
# Dark brand-ish per-scene background palette (cycled).
_PALETTE = [(11, 16, 32), (24, 14, 38), (10, 28, 38), (28, 20, 12), (14, 24, 20)]
_AUDIO_PAD = 0.4       # trailing visual padding after a scene's narration finishes
_MAX_SCENE_SEC = 30.0  # cap one scene's duration (guard against a runaway TTS clip)


def _patch_pillow() -> None:
    """Restore the legacy PIL resampling aliases removed in Pillow 10.

    MoviePy 1.0.3's clip ``.resize()`` (used to scale Pexels b-roll to the 9:16 frame)
    calls ``PIL.Image.ANTIALIAS``, which Pillow 10 removed in favor of
    ``Image.Resampling.*``. Without this shim, b-roll resize raises AttributeError and
    every scene silently degrades to a plain color background (no footage). Idempotent + safe.
    """
    try:
        from PIL import Image

        resampling = getattr(Image, "Resampling", None)
        if resampling is None:  # very old Pillow already exposes the top-level names
            return
        for name in ("NEAREST", "BILINEAR", "BICUBIC", "LANCZOS", "HAMMING", "BOX"):
            if not hasattr(Image, name):
                setattr(Image, name, getattr(resampling, name))
        if not hasattr(Image, "ANTIALIAS"):  # ANTIALIAS was an alias of LANCZOS
            Image.ANTIALIAS = resampling.LANCZOS
    except Exception:  # noqa: BLE001 - never let the shim break rendering
        pass


def render_available() -> bool:
    """True when the optional render engine (moviepy + pillow) is importable.

    Honors OMNIVRA_DISABLE_RENDER (set in tests / to force stub mode without
    uninstalling the engine), so render behavior is deterministic regardless of
    whether moviepy happens to be installed locally.
    """
    if os.environ.get("OMNIVRA_DISABLE_RENDER"):
        return False
    try:
        import moviepy.editor  # noqa: F401
        import PIL  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


def _background_clip(mp: Any, broll: list[Path | None] | None, i: int, dur: float, to_close: list[Any]):
    """A per-scene background that fills the WHOLE scene duration: the Pexels b-roll
    (looped if shorter than ``dur``, trimmed if longer) framed to 9:16, else a color clip.

    Filling ``dur`` exactly is what keeps the b-roll in lockstep with the scene's
    (audio-driven) length — no early-ending clip or frozen frame.
    """
    clip_path = broll[i] if broll and i < len(broll) else None
    if clip_path:
        try:
            # Track the opened source clip in ``to_close`` BEFORE transforming it: VideoFileClip
            # spawns an ffmpeg reader + holds the .mp4 handle, and the transforms below are shallow
            # copies sharing that reader. If a transform raises, the deterministic finally still
            # closes the reader (VideoFileClip has no __del__, so otherwise it leaks to GC).
            v = mp.VideoFileClip(str(clip_path)).without_audio()
            to_close.append(v)
            # Reject a degenerate aspect ratio BEFORE the resize chain: a few-px-wide source would
            # survive resize(height=1920) as a tiny width, then resize(width=1080) would explode the
            # height (e.g. 4x1000 -> 1080x296228, ~960MB/frame -> OOM at write time). Raising here lets
            # the except below degrade THIS scene to a color background instead of failing the render.
            if not v.w or not v.h or not (0.05 < v.w / v.h < 20):
                raise ValueError(f"degenerate b-roll aspect ratio {v.w}x{v.h}")
            # Frame to an EXACT 1080x1920: scale to height, fit width (crop wide / upscale narrow),
            # then center-crop any height overshoot. Every scene must be _W x _H so concatenate
            # produces a uniform frame — there's no CompositeVideoClip canvas to normalize size now.
            v = v.resize(height=_H)
            v = v.crop(x_center=v.w / 2, width=_W) if v.w > _W else v.resize(width=_W)
            if v.h > _H:  # width-upscaling a narrower-than-9:16 clip overshoots height -> crop back
                v = v.crop(y_center=v.h / 2, height=_H)
            # Span the scene: loop a short clip, trim a long one.
            v = v.fx(mp.vfx.loop, duration=dur) if v.duration < dur else v.subclip(0, dur)
            return v.set_duration(dur)
        except Exception as exc:  # noqa: BLE001 - any b-roll issue -> color background
            logger.warning("b-roll clip unusable (scene {}), using color bg: {}", i, repr(exc))
    # ColorClip is synthetic (no file handle) but is still tracked + closed for uniformity.
    return mp.ColorClip((_W, _H), color=_PALETTE[i % len(_PALETTE)], duration=dur)


def render_reel(
    storyboard: Any,
    output_path: Path,
    *,
    broll: list[Path | None] | None = None,
    voiceovers: list[Path | None] | None = None,
) -> dict[str, Any]:
    """Render ``storyboard`` to ``output_path`` (.mp4). Returns {ok, stub, path?, note}.

    PER-SCENE composition keeps everything in sync: each scene = its b-roll (or color
    background) + its OWN voiceover, and the scene's length is driven by that scene's narration
    (``max(storyboard duration, audio + pad)``). So the audio you hear and the footage you see
    belong to the same scene and start/end together — instead of one combined audio track
    drifting over fixed-length visuals. No burned-in subtitle/caption overlay.

    ``voiceovers[i]`` is scene i's audio (or None for a silent scene). Never raises: a missing
    engine returns stub=True; a render error returns ok=False.
    """
    if os.environ.get("OMNIVRA_DISABLE_RENDER"):
        return {"ok": True, "stub": True, "note": "render engine disabled (OMNIVRA_DISABLE_RENDER); storyboard saved as the draft."}
    try:
        import moviepy.editor as mp
    except Exception as exc:  # noqa: BLE001 - engine not installed -> stub
        return {"ok": True, "stub": True, "note": f"render engine not installed ({type(exc).__name__}); storyboard saved as the draft."}
    _patch_pillow()  # make MoviePy's b-roll resize work on Pillow >= 10 (see _patch_pillow)

    scenes = list(getattr(storyboard, "scenes", []) or [])
    if not scenes:
        return {"ok": False, "stub": True, "note": "storyboard has no scenes to render"}

    to_close: list[Any] = []  # EVERY opened clip; closed in the finally so no file handle leaks (Windows locks)
    final = None
    try:
        scene_clips: list[Any] = []
        for i, sc in enumerate(scenes):
            base_dur = max(1.0, float(getattr(sc, "duration_sec", 4.0) or 4.0))
            # Scene i's own voiceover (if any) DRIVES the scene length so the b-roll plays for exactly
            # as long as the narration — keeping Pexels footage + TTS audio in sync, scene by scene.
            vo_path = voiceovers[i] if voiceovers and i < len(voiceovers) else None
            vo_clip = None
            if vo_path and Path(vo_path).exists():
                try:
                    vo_clip = mp.AudioFileClip(str(vo_path))
                    to_close.append(vo_clip)
                except Exception as exc:  # noqa: BLE001 - one bad clip -> silent scene, not a failed render
                    logger.warning("scene {} voiceover unusable (silent scene): {}", i, repr(exc))
                    vo_clip = None
            dur = max(base_dur, min(_MAX_SCENE_SEC, vo_clip.duration + _AUDIO_PAD)) if vo_clip else base_dur

            # The scene IS its background (b-roll or color), framed to 9:16 and spanning `dur`.
            # No caption/subtitle overlay — just footage + its own narration.
            scene = _background_clip(mp, broll, i, dur, to_close)
            to_close.append(scene)
            if vo_clip is not None:
                scene = scene.set_audio(vo_clip.set_duration(min(vo_clip.duration, dur)))  # scene-local audio
                to_close.append(scene)
            scene_clips.append(scene)

        final = mp.concatenate_videoclips(scene_clips, method="compose")  # concatenates per-scene audio too
        to_close.append(final)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_kwargs: dict[str, Any] = {"fps": 24, "codec": "libx264", "logger": None}
        if final.audio is not None:  # only encode an audio track if at least one scene had narration
            write_kwargs.update(audio_codec="aac", temp_audiofile=str(output_path.with_suffix(".tmp.m4a")), remove_temp=True)
        final.write_videofile(str(output_path), **write_kwargs)
        return {"ok": True, "stub": False, "path": str(output_path), "note": "rendered"}
    except Exception as exc:  # noqa: BLE001 - report a render failure without raising
        logger.error("Reel render failed: {}", repr(exc))
        return {"ok": False, "stub": False, "note": f"render failed: {exc!r}"}
    finally:
        # Close every opened clip (b-roll reader / audio / set_audio result / final) so no
        # ffmpeg subprocess or file handle leaks (Windows locks open files).
        for c in to_close:
            try:
                if c is not None:
                    c.close()
            except Exception:  # noqa: BLE001
                pass
