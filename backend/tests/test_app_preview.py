"""Static app preview (cp-0070): a real URL in production, where the launch runner is off.

On a shared host (HF Space) APP_RUNNER_ENABLED=false — a launched app's localhost port isn't
reachable and running generated code there is an AUP risk. Serving the app's FILES is neither,
so a static frontend still previews. These tests pin the discovery heuristics (what actually
renders in a browser), the path-jailed serving route, and the cookie leg that lets the page's
relative asset requests authenticate after the ?t= query is dropped.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.app_runner import preview_rel
from app.workspace_fs.paths import project_root

APP = "docs/wf_preview"


def _write(rel: str, body: str = "x") -> None:
    p = project_root("__default__") / APP / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


@pytest.fixture(autouse=True)
def _clean_app() -> None:
    import shutil

    root = project_root("__default__") / APP
    shutil.rmtree(root, ignore_errors=True)
    yield
    shutil.rmtree(root, ignore_errors=True)
    # preview_user publishes the request's owner via set_key_owner (correct in a request, where
    # the middleware re-sets it per call) — but a DIRECT call in a test leaves it in this
    # thread's ContextVar and poisons every later provider-key test. Always clear it.
    from app.services.provider_keys import set_key_owner

    set_key_owner(None)


# --- discovery: pick what a browser can actually render -----------------------------------


def test_plain_html_app_previews() -> None:
    _write("site/index.html", "<h1>hi</h1>")
    _write("site/styles.css", "body{}")
    assert preview_rel(None, APP) == f"{APP}/site/index.html"


def test_index_beats_other_names_and_shallower_beats_deeper() -> None:
    _write("deep/nested/other.html")
    _write("page.html")
    _write("index.html")
    assert preview_rel(None, APP) == f"{APP}/index.html"


def test_source_html_of_a_node_app_is_not_previewable() -> None:
    """A Vite/CRA project's root index.html references /src/main.tsx — only a dev server or a
    build resolves that. Previewing it would show a confidently broken page."""
    _write("web/package.json", "{}")
    _write("web/index.html", '<script type="module" src="/src/main.tsx"></script>')
    assert preview_rel(None, APP) is None


def test_built_output_previews_even_inside_a_node_app() -> None:
    """dist/ is the COMPILED app — self-contained html that renders as-is."""
    _write("web/package.json", "{}")
    _write("web/index.html", "source template")
    _write("web/dist/index.html", "<h1>built</h1>")
    assert preview_rel(None, APP) == f"{APP}/web/dist/index.html"


def test_node_modules_is_never_scanned() -> None:
    _write("web/package.json", "{}")
    _write("web/node_modules/pkg/index.html", "vendor page")
    assert preview_rel(None, APP) is None


def test_no_html_means_no_preview() -> None:
    _write("api/main.py", "print('hi')")
    assert preview_rel(None, APP) is None


def test_preview_rel_never_escapes_the_sandbox() -> None:
    assert preview_rel(None, "../../etc") is None


# --- the serving route --------------------------------------------------------------------


def test_preview_route_serves_html_and_relative_assets(client: TestClient) -> None:
    _write("site/index.html", "<link rel='stylesheet' href='styles.css'><h1>hi</h1>")
    _write("site/styles.css", "body{color:red}")
    _write("site/app.js", "console.log(1)")

    r = client.get(f"/api/workspace/app/preview/__default__/{APP}/site/index.html")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "hi" in r.text

    css = client.get(f"/api/workspace/app/preview/__default__/{APP}/site/styles.css")
    assert css.status_code == 200 and css.headers["content-type"].startswith("text/css")

    # Explicit JS MIME: Windows' registry can map .js to application/x-javascript, and browsers
    # hard-refuse module scripts served with a non-JS MIME type.
    js = client.get(f"/api/workspace/app/preview/__default__/{APP}/site/app.js")
    assert js.status_code == 200 and js.headers["content-type"].startswith("text/javascript")


def test_preview_route_is_path_jailed(client: TestClient) -> None:
    r = client.get("/api/workspace/app/preview/__default__/..%2f..%2f..%2fbackend%2f.env")
    assert r.status_code in (400, 404), r.status_code


def test_preview_route_404s_on_missing_file(client: TestClient) -> None:
    assert client.get(f"/api/workspace/app/preview/__default__/{APP}/nope.html").status_code == 404


def test_tokened_request_plants_the_preview_cookie(client: TestClient) -> None:
    """The page's relative asset URLs drop ?t=, so the first request must leave a path-scoped
    cookie behind for the asset requests to authenticate with."""
    from app.api.deps import PREVIEW_COOKIE
    from app.core.security import create_token

    _write("site/index.html", "<h1>hi</h1>")
    tok = create_token("admin", ttl_seconds=60, scope="media")
    r = client.get(f"/api/workspace/app/preview/__default__/{APP}/site/index.html?t={tok}")
    assert r.status_code == 200
    cookie = r.headers.get("set-cookie", "")
    assert PREVIEW_COOKIE in cookie
    assert "/api/workspace/app/preview" in cookie, "cookie must be path-scoped to previews only"


def test_preview_user_accepts_the_cookie(monkeypatch) -> None:
    """Per-user mode: the cookie leg must authenticate an asset request that has no header and
    no query token — and reject garbage."""
    from fastapi import HTTPException

    from app.api import deps
    from app.core.security import create_token

    monkeypatch.setattr(deps, "per_user_mode", lambda: True)
    tok = create_token("user-1", ttl_seconds=60, scope="media")
    assert deps.preview_user(authorization=None, t=None, omnivra_media=tok) == "user-1"

    with pytest.raises(HTTPException):
        deps.preview_user(authorization=None, t=None, omnivra_media="garbage")
    with pytest.raises(HTTPException):
        deps.preview_user(authorization=None, t=None, omnivra_media=None)


def test_session_token_cannot_ride_the_preview_cookie(monkeypatch) -> None:
    """Scope check: a SESSION token in the cookie must not work (media scope only), so a stolen
    preview cookie can never be replayed as an API session and vice versa."""
    from fastapi import HTTPException

    from app.api import deps
    from app.core.security import create_token

    monkeypatch.setattr(deps, "per_user_mode", lambda: True)
    session_tok = create_token("user-1", ttl_seconds=60, scope="session")
    with pytest.raises(HTTPException):
        deps.preview_user(authorization=None, t=None, omnivra_media=session_tok)


# --- surfacing: list/status/run all carry the preview -------------------------------------


def test_app_list_and_status_carry_the_preview_path(client: TestClient) -> None:
    _write("site/index.html", "<h1>hi</h1>")
    apps = client.get("/api/workspace/app/list").json()
    mine = next((a for a in apps if a["dir"] == APP), None)
    assert mine is not None
    assert mine["previewPath"] == f"{APP}/site/index.html"

    status = client.get("/api/workspace/app/status", params={"dir": APP}).json()
    assert status["previewPath"] == f"{APP}/site/index.html"


def test_disabled_runner_run_returns_the_preview_instead_of_a_dead_end(client: TestClient, monkeypatch) -> None:
    """The reported symptom: Run on the Space answered only 'disabled… download the ZIP'. With a
    previewable app it must now hand back the preview path so the tab has somewhere to go."""
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "app_runner_enabled", False, raising=False)
    _write("site/index.html", "<h1>hi</h1>")

    body = client.post("/api/workspace/app/run", json={"dir": APP}).json()
    assert body["targets"] == []
    assert body["previewPath"] == f"{APP}/site/index.html"
    assert "static preview" in body["note"]


def test_disabled_runner_without_preview_keeps_the_zip_note(client: TestClient, monkeypatch) -> None:
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "app_runner_enabled", False, raising=False)
    _write("api/main.py", "print('server only')")

    body = client.post("/api/workspace/app/run", json={"dir": APP}).json()
    assert body["previewPath"] is None
    assert "ZIP" in body["note"]


def test_system_info_exposes_the_runner_flag(client: TestClient) -> None:
    info = client.get("/api/system/info").json()
    assert info["appRunnerEnabled"] is True  # local default; the Space Dockerfile sets false


# --- SPA source harness: run Vite/React source in the visitor's browser -------------------


def test_vite_source_app_gets_the_harness_preview() -> None:
    """The gap the static preview left: most generated frontends are Vite SOURCE. They now
    preview via the in-browser build harness instead of 'download the ZIP'."""
    _write("web/package.json", "{}")
    _write("web/index.html", '<div id="root"></div><script type="module" src="/src/main.jsx"></script>')
    _write("web/src/main.jsx", "import App from './App'; console.log(App)")
    _write("web/src/App.jsx", "export default function App(){return null}")
    assert preview_rel(None, APP) == f"{APP}/web/__app__.html"


def test_static_html_still_beats_the_harness() -> None:
    """A real static page needs no in-browser build — it stays the preferred preview."""
    _write("web/package.json", "{}")
    _write("web/src/main.jsx", "x")
    _write("site/index.html", "<h1>plain</h1>")
    assert preview_rel(None, APP) == f"{APP}/site/index.html"


def test_entry_prefers_what_the_apps_own_index_names() -> None:
    from pathlib import Path

    from app.services.spa_preview import spa_entry

    _write("web/package.json", "{}")
    _write("web/index.html", '<script type="module" src="/custom/boot.jsx"></script>')
    _write("web/custom/boot.jsx", "x")
    _write("web/src/main.jsx", "conventional entry also exists")
    root = project_root("__default__") / APP / "web"
    found = spa_entry(Path(root))
    assert found is not None and found[1] == "custom/boot.jsx"


def test_missing_entry_file_means_no_harness() -> None:
    """An index.html pointing at a src/main.tsx that was never generated has nothing to run —
    promising a preview would just render an error page."""
    _write("web/package.json", "{}")
    _write("web/index.html", '<script type="module" src="/src/main.tsx"></script>')
    assert preview_rel(None, APP) is None


def test_harness_route_serves_the_builder_page(client: TestClient) -> None:
    _write("web/package.json", "{}")
    _write("web/src/main.jsx", "export default 1")
    r = client.get(f"/api/workspace/app/preview/__default__/{APP}/web/__app__.html")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    # The page must know its entry and carry the in-browser toolchain + pinned React CDN.
    assert '"./src/main.jsx"' in r.text
    assert "babel" in r.text.lower() and "esm.sh" in r.text
    assert "REACT_PIN = '18.3.1'" in r.text, "React must be pinned so all packages share one instance"


def test_harness_404s_where_there_is_nothing_to_run(client: TestClient) -> None:
    _write("api/main.py", "print('backend only')")
    r = client.get(f"/api/workspace/app/preview/__default__/{APP}/api/__app__.html")
    assert r.status_code == 404
    assert "browser-runnable" in r.json()["detail"]


def test_disabled_runner_now_offers_the_harness_for_vite_source(client: TestClient, monkeypatch) -> None:
    """The exact reported flow: Run on the Space for a vite-source app used to dead-end at
    'download the ZIP'; it must now hand back the harness preview."""
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "app_runner_enabled", False, raising=False)
    _write("web/package.json", "{}")
    _write("web/src/main.jsx", "export default 1")

    body = client.post("/api/workspace/app/run", json={"dir": APP}).json()
    assert body["previewPath"] == f"{APP}/web/__app__.html"
    assert "static preview" in body["note"]


def test_preview_is_found_across_sibling_category_dirs(client: TestClient) -> None:
    """The reported card: dir=backend/wf_x (it holds the only runnable target), html living in
    frontend/wf_x. The root election is scored by targets, so the loose html scored zero and
    the root-only preview scan reported nothing to show. The list must scan the workflow's
    OTHER category dirs too."""
    from pathlib import Path

    root = project_root("__default__")
    api = root / "backend/wf_split/main.py"
    api.parent.mkdir(parents=True, exist_ok=True)
    api.write_text("print('api')", encoding="utf-8")
    (root / "backend/wf_split/requirements.txt").write_text("fastapi\n", encoding="utf-8")
    page = root / "frontend/wf_split/index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("<h1>the actual website</h1>", encoding="utf-8")
    try:
        apps = client.get("/api/workspace/app/list").json()
        mine = next((a for a in apps if a["wfId"] == "wf_split"), None)
        assert mine is not None
        assert mine["dir"] == "backend/wf_split", "the runnable target still owns the card"
        assert mine["previewPath"] == "frontend/wf_split/index.html", "…but the sibling html previews"
    finally:
        import shutil

        shutil.rmtree(root / "backend/wf_split", ignore_errors=True)
        shutil.rmtree(root / "frontend/wf_split", ignore_errors=True)
