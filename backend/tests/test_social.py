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


@pytest.mark.skipif(not render_available(), reason="render engine (moviepy+pillow) not installed")
def test_real_render_produces_mp4(tmp_path) -> None:
    """When the optional engine is installed, render a real .mp4 fully offline
    (color backgrounds + Pillow captions, no b-roll/voiceover). Skipped otherwise."""
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
