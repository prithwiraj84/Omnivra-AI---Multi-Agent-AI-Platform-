"""Social content pipeline tests (cp-0016): draft -> approve/reject -> publish (stub).

Everything runs offline: with no provider keys the agents stub, so the storyboard /
caption fall back to deterministic builders, the FLUX image + Orpheus voiceover write
placeholders, and the platform publishers return stub results. Project-scoped via the
X-Project-Id header (default project when absent).
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.schemas.social import ReelScene, ReelStoryboard, SocialDraft
from app.services.reel_render import render_available, render_reel
from app.services.social import get_social_service




def test_draft_reel_offline(client: TestClient) -> None:
    res = client.post("/api/social/reel", json={"brief": "Launch our AI company OS"})
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "reel"
    assert body["status"] == "awaiting_approval"
    assert body["targets"] == ["youtube", "instagram"]
    assert body["storyboard"] and body["storyboard"]["scenes"], "a reel must have a storyboard with scenes"
    assert body["storyboard"]["totalDurationSec"] > 0
    assert body["artifacts"], "the reel must persist artifacts (storyboard + manifest + voiceover)"
    # camelCase scene fields
    scene = body["storyboard"]["scenes"][0]
    assert {"durationSec", "voiceover", "brollQuery", "onScreenText"}.issubset(scene.keys())


def test_draft_post_offline(client: TestClient) -> None:
    res = client.post("/api/social/post", json={"brief": "Announce our seed round"})
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "post"
    assert body["status"] == "awaiting_approval"
    assert body["targets"] == ["facebook", "linkedin", "twitter"]
    assert body["caption"], "a post must have a caption"
    assert body["hashtags"], "a post must have hashtags"
    assert body["artifacts"], "the post must persist artifacts (image + caption)"


def test_approve_publishes_to_targets_stub(client: TestClient) -> None:
    draft = client.post("/api/social/reel", json={"brief": "Behind the scenes of an AI company"}).json()
    res = client.post(f"/api/social/drafts/{draft['id']}/decision", json={"action": "approve"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "published"
    platforms = {r["platform"] for r in body["publishResults"]}
    assert platforms == {"youtube", "instagram"}
    assert all(r["ok"] and r["stub"] for r in body["publishResults"]), "Phase 1 publishes are stubs"


def test_reject_marks_rejected(client: TestClient) -> None:
    draft = client.post("/api/social/post", json={"brief": "Hiring announcement"}).json()
    res = client.post(f"/api/social/drafts/{draft['id']}/decision", json={"action": "reject", "note": "off-brand"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "rejected"
    assert body["publishResults"] == []
    assert body["note"] == "off-brand"


def test_custom_targets_are_respected(client: TestClient) -> None:
    draft = client.post("/api/social/reel", json={"brief": "Quick tip", "targets": ["youtube"]}).json()
    assert draft["targets"] == ["youtube"]
    published = client.post(f"/api/social/drafts/{draft['id']}/decision", json={"action": "approve"}).json()
    assert [r["platform"] for r in published["publishResults"]] == ["youtube"]


def test_drafts_are_project_isolated(client: TestClient) -> None:
    a = client.post("/api/projects", json={"name": "Social A"}).json()["id"]
    b = client.post("/api/projects", json={"name": "Social B"}).json()["id"]

    client.post("/api/social/post", json={"brief": "Project A only"}, headers={"X-Project-Id": a})

    list_a = client.get("/api/social/drafts", headers={"X-Project-Id": a}).json()
    list_b = client.get("/api/social/drafts", headers={"X-Project-Id": b}).json()
    assert list_a, "project A must see its own draft"
    assert all(d["projectId"] == a for d in list_a)
    assert list_b == [], "project B must not see project A's draft (isolation)"


def test_unknown_draft_is_404(client: TestClient) -> None:
    assert client.get("/api/social/drafts/nope-xyz").status_code == 404
    assert client.post("/api/social/drafts/nope-xyz/decision", json={"action": "approve"}).status_code == 404


def test_delete_draft_removes_record_and_artifacts(client: TestClient) -> None:
    from app.workspace_fs.paths import project_root

    draft = client.post("/api/social/post", json={"brief": "delete me"}).json()
    did = draft["id"]
    social_dir = project_root("__default__") / "reports" / "social" / did
    assert social_dir.exists(), "the draft's artifacts exist before delete"
    assert client.get(f"/api/social/drafts/{did}").status_code == 200

    res = client.delete(f"/api/social/drafts/{did}")
    assert res.status_code == 204
    assert client.get(f"/api/social/drafts/{did}").status_code == 404, "record is gone"
    assert not social_dir.exists(), "the draft's artifact folder is purged"


def test_delete_unknown_draft_is_404(client: TestClient) -> None:
    assert client.delete("/api/social/drafts/nope-xyz").status_code == 404


def test_delete_mid_render_does_not_resurrect(client: TestClient, monkeypatch) -> None:
    # If a DELETE lands while a render is in flight, run_render must NOT recreate the record
    # (save_if_exists guard). Simulate the concurrent delete from inside the b-roll phase.
    from app.services.social_store import get_social_store

    svc = get_social_service()
    did = client.post("/api/social/reel", json={"brief": "delete during render"}).json()["id"]
    svc.begin_render(did, None)
    store = get_social_store("__default__")
    assert store.get(did) is not None

    async def _deleting_fetch(query, dest):  # noqa: ANN001 - test stub
        store.delete(did)  # the user deletes the draft mid-render
        return None

    monkeypatch.setattr("app.services.social.fetch_broll", _deleting_fetch)
    asyncio.run(svc.run_render(did, None))
    assert store.get(did) is None, "run_render must not resurrect a draft deleted mid-render"


def test_delete_reclaims_render_voiceover(client: TestClient, monkeypatch) -> None:
    # A render-time voiceover (flat reports/media/<uuid>.wav) must be tracked in artifacts so
    # delete_draft reclaims it (it isn't under the per-draft folder).
    from app.services.media import get_media_service
    from app.workspace_fs.paths import project_root

    svc = get_social_service()
    did = client.post("/api/social/reel", json={"brief": "voiceover cleanup"}).json()["id"]

    vo_rel = "reports/media/vo_cleanup_probe.wav"
    vo_abs = project_root("__default__") / vo_rel
    vo_abs.parent.mkdir(parents=True, exist_ok=True)
    vo_abs.write_bytes(b"RIFFfake-wav")

    async def _fake_vo(text, pid):  # noqa: ANN001 - test stub
        return vo_rel, "synthesized"

    monkeypatch.setattr(get_media_service(), "voiceover_with_note", _fake_vo)
    svc.begin_render(did, None)
    asyncio.run(svc.run_render(did, None))

    tracked = client.get(f"/api/social/drafts/{did}").json()["artifacts"]
    assert vo_rel in tracked, "the render voiceover must be tracked so delete can reclaim it"

    assert client.delete(f"/api/social/drafts/{did}").status_code == 204
    assert not vo_abs.exists(), "delete must reclaim the render voiceover .wav"


def test_render_reel_transitions_to_rendered(client: TestClient) -> None:
    draft = client.post("/api/social/reel", json={"brief": "Render me a teaser"}).json()
    res = client.post(f"/api/social/drafts/{draft['id']}/render")
    assert res.status_code == 200
    assert res.json()["renderStatus"] == "rendering"  # immediate response (async kicked off)

    # In this test TestClient awaits the BackgroundTask before the request returns; in
    # production it runs async after the response (client polls the draft / watches /ws).
    # Mode-agnostic: stub (no engine) -> rendered + note, real -> rendered + an .mp4.
    done = client.get(f"/api/social/drafts/{draft['id']}").json()
    assert done["renderStatus"] == "rendered"
    assert done["renderNote"]


def test_render_missing_draft_reaches_terminal_state(client: TestClient) -> None:
    # If a draft vanishes before the background render runs, run_render must end
    # cleanly (emit a terminal status, no exception) — never hang on 'rendering'.
    asyncio.run(get_social_service().run_render("reel_does_not_exist", None))


def test_project_delete_cascades_social_drafts(client: TestClient) -> None:
    # Deleting a project hard-deletes its social drafts + artifacts (the .state/social subtree).
    from app.workspace_fs.paths import project_root

    pid = client.post("/api/projects", json={"name": "Social Cascade"}).json()["id"]
    hdr = {"X-Project-Id": pid}
    client.post("/api/social/post", json={"brief": "doomed draft"}, headers=hdr)
    assert client.get("/api/social/drafts", headers=hdr).json(), "draft exists before delete"
    assert (project_root(pid) / ".state" / "social").exists()

    assert client.delete(f"/api/projects/{pid}").status_code == 200
    assert not project_root(pid).exists(), "the project workspace (incl. social drafts) is purged"


def test_youtube_publisher_stubs_without_credentials(client: TestClient) -> None:
    # The real YouTube uploader degrades to a stub when no OAuth creds are set, so the
    # approve -> publish flow still completes offline.
    from app.services import publishers

    draft = SocialDraft(
        id="reel_x",
        project_id="__default__",
        kind="reel",
        brief="b",
        storyboard=ReelStoryboard(title="t"),
        targets=["youtube"],
        created_at="2026-01-01",
    )
    res = asyncio.run(publishers.publish_to("youtube", draft))
    assert res.platform == "youtube"
    assert res.ok is True and res.stub is True


def test_render_rejects_posts(client: TestClient) -> None:
    draft = client.post("/api/social/post", json={"brief": "An image post"}).json()
    res = client.post(f"/api/social/drafts/{draft['id']}/render")
    assert res.status_code == 400


def test_render_unknown_draft_404(client: TestClient) -> None:
    assert client.post("/api/social/drafts/nope-xyz/render").status_code == 404


def test_draft_emits_live_progress_events(client: TestClient) -> None:
    # Generating a post must broadcast per-step 'social_progress' frames (caption -> image
    # -> ready) so the Social Studio can show live progress before the approval view.
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "hello"
        assert ws.receive_json()["type"] == "system_health"

        job = client.post("/api/social/post", json={"brief": "Show me live progress"}).json()["id"]

        steps: list[tuple[str, str]] = []
        terminal = False
        for _ in range(50):
            ev = ws.receive_json()
            if ev["type"] != "social_progress":  # heartbeat frames interleave
                continue
            p = ev["payload"]
            # Every progress frame carries the routing + step contract the UI relies on.
            assert p["jobId"] and p["projectId"] and p["kind"] == "post" and p["phase"] == "draft"
            assert p["status"] in {"running", "done", "error"}
            assert 1 <= p["index"] <= p["total"]
            if p["jobId"] == job:
                steps.append((p["step"], p["status"]))
                if p["step"] == "ready" and p["status"] == "done":
                    terminal = True
                    break

        assert terminal, f"expected a terminal 'ready' progress for {job}; saw {steps}"
        assert ("caption", "running") in steps and ("image", "running") in steps


def test_render_emits_live_progress_events(client: TestClient) -> None:
    # Rendering a reel must broadcast 'social_progress' render frames (broll -> voiceover ->
    # assemble -> rendered) so the reel card can show live render progress.
    draft_id = client.post("/api/social/reel", json={"brief": "Render with progress"}).json()["id"]
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "hello"
        assert ws.receive_json()["type"] == "system_health"

        client.post(f"/api/social/drafts/{draft_id}/render")  # TestClient awaits the BackgroundTask

        steps: list[tuple[str, str]] = []
        for _ in range(80):
            ev = ws.receive_json()
            if ev["type"] != "social_progress":
                continue
            p = ev["payload"]
            if p["jobId"] == draft_id and p["phase"] == "render":
                steps.append((p["step"], p["status"]))
                if p["step"] == "rendered":
                    break

        assert ("broll", "running") in steps, f"expected a Pexels b-roll step; saw {steps}"
        assert ("assemble", "running") in steps, f"expected a MoviePy assemble step; saw {steps}"
        assert any(s[0] == "rendered" for s in steps), f"expected a terminal 'rendered' step; saw {steps}"


def test_patch_pillow_restores_resampling_aliases() -> None:
    # MoviePy 1.0.3's b-roll resize calls PIL.Image.ANTIALIAS, removed in Pillow 10 — without
    # the shim every Pexels clip silently degrades to a color background (only captions show).
    from PIL import Image

    from app.services.reel_render import _patch_pillow

    _patch_pillow()
    assert hasattr(Image, "ANTIALIAS"), "ANTIALIAS alias must be restored for MoviePy resize"
    for name in ("LANCZOS", "BILINEAR", "BICUBIC"):
        assert hasattr(Image, name)


@pytest.mark.skipif(not render_available(), reason="render engine not enabled (OMNIVRA_DISABLE_RENDER / moviepy)")
def test_real_render_produces_mp4(tmp_path) -> None:
    """When rendering is enabled, render a real .mp4 fully offline (color backgrounds, no
    b-roll/voiceover, NO caption overlay). The output is framed to an exact 1080x1920 9:16 even
    though there's no CompositeVideoClip canvas. (Skipped in the hermetic suite, which force-
    disables rendering for speed; runs when OMNIVRA_DISABLE_RENDER is cleared + moviepy present.)"""
    import moviepy.editor as mp

    sb = ReelStoryboard(
        title="t",
        hook="hook",
        scenes=[
            ReelScene(duration_sec=1.0, on_screen_text="Hello", voiceover="hi", broll_query=""),
            ReelScene(duration_sec=1.0, on_screen_text="World", voiceover="yo", broll_query=""),
        ],
        total_duration_sec=2.0,
    )
    out = tmp_path / "reel.mp4"
    result = render_reel(sb, out)
    assert result["ok"] and not result["stub"], result
    assert out.exists() and out.stat().st_size > 1000

    clip = mp.VideoFileClip(str(out))
    try:
        assert clip.size == [1080, 1920], f"reel must be a 9:16 1080x1920 frame, got {clip.size}"
    finally:
        clip.close()


@pytest.mark.skipif(not render_available(), reason="render engine not enabled (OMNIVRA_DISABLE_RENDER / moviepy)")
def test_real_render_audio_matches_video_duration(tmp_path) -> None:
    """Per-scene voiceover keeps audio in sync with the footage: the rendered video's duration
    equals its audio track's duration (each scene lasts as long as its own narration).
    Skipped in the hermetic suite (rendering force-disabled); runs when rendering is enabled."""
    import math
    import struct
    import wave

    import moviepy.editor as mp

    def _wav(path, seconds):  # a simple tone of a known length
        with wave.open(str(path), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            for n in range(int(22050 * seconds)):
                w.writeframes(struct.pack("<h", int(9000 * math.sin(2 * math.pi * 330 * n / 22050))))
        return path

    vos = [_wav(tmp_path / "a.wav", 2.0), _wav(tmp_path / "b.wav", 3.0)]
    sb = ReelStoryboard(
        title="t", hook="h",
        scenes=[
            ReelScene(duration_sec=1.0, on_screen_text="A", voiceover="a", broll_query=""),
            ReelScene(duration_sec=1.0, on_screen_text="B", voiceover="b", broll_query=""),
        ],
        total_duration_sec=2.0,
    )
    out = tmp_path / "reel.mp4"
    result = render_reel(sb, out, voiceovers=vos)
    assert result["ok"] and not result["stub"], result

    clip = mp.VideoFileClip(str(out))
    try:
        assert clip.audio is not None, "the reel must carry the per-scene voiceover audio"
        # Scene length = max(1.0, narration + 0.4) -> ~2.4 + ~3.4; audio spans the whole video.
        assert abs(clip.duration - clip.audio.duration) < 0.3, (clip.duration, clip.audio.duration)
    finally:
        clip.close()
