"""Reel render engine (cp-0018) — composes a storyboard into a vertical .mp4.

Import-guarded + degrades gracefully (the WORKSPACE-RULE / offline-first ethos):
  * moviepy NOT installed            -> returns a stub (caller keeps the manifest only).
  * moviepy installed, no API keys   -> a REAL .mp4 from per-scene color backgrounds
                                        + Pillow-drawn captions (fully offline).
  * + Pexels b-roll / Orpheus audio  -> stock footage + voiceover layered in.

Captions are rendered with Pillow (NOT MoviePy's TextClip) so there is NO ImageMagick
system dependency — everything stays inside the venv. This module is pure/sync (CPU
work); the orchestrator runs it off the event loop via asyncio.to_thread.
"""
from __future__ import annotations

import os
import textwrap
import tempfile
from pathlib import Path
from typing import Any

from app.core.logging import logger

_W, _H = 1080, 1920  # vertical 9:16
# Dark brand-ish per-scene background palette (cycled).
_PALETTE = [(11, 16, 32), (24, 14, 38), (10, 28, 38), (28, 20, 12), (14, 24, 20)]


def render_available() -> bool:
    """True when the optional render engine (moviepy + pillow) is importable."""
    try:
        import moviepy.editor  # noqa: F401
        import PIL  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


def _caption_png(text: str, tmp_paths: list[str]) -> str | None:
    """Draw a word-wrapped caption onto a transparent PNG; return its path (or None)."""
    from PIL import Image, ImageDraw, ImageFont

    text = (text or "").strip()
    if not text:
        return None
    img = Image.new("RGBA", (_W, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:  # a real font if the OS has one; else Pillow's bundled bitmap font
        font = ImageFont.truetype("arial.ttf", 64)
    except Exception:  # noqa: BLE001
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 64)
        except Exception:  # noqa: BLE001
            font = ImageFont.load_default()
    lines = textwrap.wrap(text, width=22) or [text]
    y = 20
    for line in lines[:4]:
        try:
            w = draw.textlength(line, font=font)
        except Exception:  # noqa: BLE001 - older Pillow
            w = len(line) * 30
        x = max(0, (_W - int(w)) // 2)
        # cheap outline for legibility over any background
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += 80
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    tmp_paths.append(path)
    return path


def _background_clip(mp: Any, broll: list[Path | None] | None, i: int, dur: float):
    """A per-scene background: the Pexels b-roll clip if present, else a color clip."""
    clip_path = broll[i] if broll and i < len(broll) else None
    if clip_path:
        try:
            v = mp.VideoFileClip(str(clip_path)).without_audio()
            v = v.subclip(0, min(dur, max(0.1, v.duration)))
            v = v.resize(height=_H)  # scale to height, then center-crop to width
            v = v.crop(x_center=v.w / 2, width=min(_W, v.w)) if v.w > _W else v.resize(width=_W)
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
    voiceover: Path | None = None,
) -> dict[str, Any]:
    """Render ``storyboard`` to ``output_path`` (.mp4). Returns {ok, stub, path?, note}.

    Never raises: a missing engine returns stub=True; a render error returns ok=False.
    """
    try:
        import moviepy.editor as mp
    except Exception as exc:  # noqa: BLE001 - engine not installed -> stub
        return {"ok": True, "stub": True, "note": f"render engine not installed ({type(exc).__name__}); storyboard saved as the draft."}

    scenes = list(getattr(storyboard, "scenes", []) or [])
    if not scenes:
        return {"ok": False, "stub": True, "note": "storyboard has no scenes to render"}

    to_close: list[Any] = []  # EVERY opened clip; closed in finally before unlinking PNGs (Windows locks open files)
    tmp_paths: list[str] = []
    final = None
    try:
        scene_clips: list[Any] = []
        for i, sc in enumerate(scenes):
            dur = max(1.0, float(getattr(sc, "duration_sec", 4.0) or 4.0))
            bg = _background_clip(mp, broll, i, dur)
            to_close.append(bg)
            cap_png = _caption_png(getattr(sc, "on_screen_text", ""), tmp_paths)
            if cap_png:
                cap = mp.ImageClip(cap_png).set_duration(dur).set_position(("center", 0.72), relative=True)
                comp = mp.CompositeVideoClip([bg, cap], size=(_W, _H)).set_duration(dur)
                to_close += [cap, comp]
                scene_clips.append(comp)
            else:
                scene_clips.append(bg)

        final = mp.concatenate_videoclips(scene_clips, method="compose")
        to_close.append(final)
        if voiceover and Path(voiceover).exists():
            try:
                audio = mp.AudioFileClip(str(voiceover))
                final = final.set_audio(audio.set_duration(min(audio.duration, final.duration)))
                to_close += [audio, final]  # set_audio returns a new clip
            except Exception as exc:  # noqa: BLE001 - silent on audio failure
                logger.warning("voiceover unusable, rendering silent: {}", repr(exc))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_path.with_suffix(".tmp.m4a")),
            remove_temp=True,
            logger=None,
        )
        return {"ok": True, "stub": False, "path": str(output_path), "note": "rendered"}
    except Exception as exc:  # noqa: BLE001 - report a render failure without raising
        logger.error("Reel render failed: {}", repr(exc))
        return {"ok": False, "stub": False, "note": f"render failed: {exc!r}"}
    finally:
        # Close every opened clip (bg / caption ImageClip / composite / audio / final)
        # BEFORE unlinking the temp PNGs, so no file handle locks them on Windows.
        for c in to_close:
            try:
                if c is not None:
                    c.close()
            except Exception:  # noqa: BLE001
                pass
        for p in tmp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass
