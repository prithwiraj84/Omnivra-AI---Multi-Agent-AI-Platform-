"""Document Studio tests (cp-0025): generate -> approve/reject, formats, isolation.

Everything runs offline: with no provider keys the documentation agent (Gemma) stubs,
so content falls back to the deterministic builder; with OMNIVRA_DISABLE_RENDER=1 (set
by conftest) the render engine is forced off, so every generate yields a markdown
deliverable (stub=True). A skipif test exercises a real PPTX/DOCX/PDF when the optional
libs are installed. Project-scoped via the X-Project-Id header.
"""
from __future__ import annotations

import importlib.util

import pytest
from fastapi.testclient import TestClient

from app.services.doc_render import _FMT_MODULE, render_document


def _engine_installed(fmt: str) -> bool:
    """True if the render lib for ``fmt`` is importable (ignores the disable flag)."""
    return importlib.util.find_spec(_FMT_MODULE[fmt]) is not None


def _generate(client: TestClient, prompt: str, fmt: str | None = None) -> dict:
    """Fire-and-poll: POST returns a 'generating' draft; return the TERMINAL draft.

    The TestClient runs the BackgroundTask before the next request, so the GET sees the
    finished (awaiting_approval) draft."""
    payload: dict = {"prompt": prompt}
    if fmt:
        payload["format"] = fmt
    res = client.post("/api/documents/generate", json=payload)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "generating", body
    return client.get(f"/api/documents/{body['id']}").json()


def test_generate_document_offline_stub(client: TestClient) -> None:
    body = _generate(client, "A roadmap for our AI company OS")
    assert body["status"] == "awaiting_approval"
    assert body["format"] == "pdf"  # default format
    assert body["title"], "a document must have a title"
    assert body["sections"], "a document must have sections"
    # Render engine is disabled in tests -> markdown deliverable.
    assert body["stub"] is True
    assert body["filePath"].endswith("document.md")
    assert any(a.endswith("content.json") for a in body["artifacts"])
    assert any(a.endswith("document.md") for a in body["artifacts"])
    # The stub explanation lives in renderNote (NOT the decision `note`), which is unset at draft time.
    assert body["renderNote"], "a stub draft must explain why it is a markdown deliverable"
    assert body["note"] is None


@pytest.mark.parametrize("fmt", ["pptx", "docx", "pdf"])
def test_generate_each_format(client: TestClient, fmt: str) -> None:
    body = _generate(client, f"Test {fmt}", fmt)
    assert body["format"] == fmt
    assert body["status"] == "awaiting_approval"


def test_unknown_format_defaults_to_pdf(client: TestClient) -> None:
    # An out-of-enum format is rejected by the request schema (422), never silently mis-rendered.
    res = client.post("/api/documents/generate", json={"prompt": "x", "format": "xlsx"})
    assert res.status_code == 422


def test_approve_document(client: TestClient) -> None:
    draft = _generate(client, "Approve me")
    res = client.post(f"/api/documents/{draft['id']}/decision", json={"action": "approve"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "approved"
    # Approving with no note must NOT wipe the stub explanation (render_note is separate from note).
    assert body["renderNote"] == draft["renderNote"]


def test_reject_document(client: TestClient) -> None:
    draft = _generate(client, "Reject me")
    res = client.post(f"/api/documents/{draft['id']}/decision", json={"action": "reject", "note": "off-topic"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "rejected"
    assert body["note"] == "off-topic"
    # The rejection reason lands in `note` only; the stub explanation in render_note is preserved.
    assert body["renderNote"] == draft["renderNote"]


def test_get_and_list_document(client: TestClient) -> None:
    draft = _generate(client, "Find me later")
    got = client.get(f"/api/documents/{draft['id']}")
    assert got.status_code == 200 and got.json()["id"] == draft["id"]
    listed = client.get("/api/documents").json()
    assert any(d["id"] == draft["id"] for d in listed)


def test_documents_project_isolated(client: TestClient) -> None:
    a = client.post("/api/projects", json={"name": "Docs A"}).json()["id"]
    b = client.post("/api/projects", json={"name": "Docs B"}).json()["id"]

    client.post("/api/documents/generate", json={"prompt": "Project A doc"}, headers={"X-Project-Id": a})

    list_a = client.get("/api/documents", headers={"X-Project-Id": a}).json()
    list_b = client.get("/api/documents", headers={"X-Project-Id": b}).json()
    assert list_a and all(d["projectId"] == a for d in list_a)
    assert list_b == [], "project B must not see project A's documents (isolation)"


def test_unknown_document_404(client: TestClient) -> None:
    assert client.get("/api/documents/nope-xyz").status_code == 404
    assert client.post("/api/documents/nope-xyz/decision", json={"action": "approve"}).status_code == 404


def test_project_delete_cascades_documents(client: TestClient) -> None:
    from app.workspace_fs.paths import project_root

    pid = client.post("/api/projects", json={"name": "Docs Cascade"}).json()["id"]
    hdr = {"X-Project-Id": pid}
    client.post("/api/documents/generate", json={"prompt": "doomed doc"}, headers=hdr)
    assert client.get("/api/documents", headers=hdr).json(), "doc exists before delete"
    assert (project_root(pid) / ".state" / "documents").exists()

    assert client.delete(f"/api/projects/{pid}").status_code == 200
    assert not project_root(pid).exists(), "the project workspace (incl. documents) is purged"


def test_render_document_disabled_returns_stub(tmp_path) -> None:
    # With OMNIVRA_DISABLE_RENDER=1 (conftest) the engine is off regardless of installed libs.
    out = tmp_path / "doc.pdf"
    result = render_document("T", [{"heading": "H", "body": "B"}], out, "pdf")
    assert result["ok"] and result["stub"] and not out.exists()


# --- Content parsing: full + truncated recovery (the 'half-completed document' fix) ---
def test_parse_full_json_document() -> None:
    from app.services.documents import DocumentService

    text = '{"title":"T","subtitle":"S","theme":"violet","sections":[{"heading":"H","body":"B","bullets":["x","y"]}]}'
    parsed = DocumentService._parse(text)
    assert parsed is not None
    title, subtitle, theme, sections = parsed
    assert (title, subtitle, theme) == ("T", "S", "violet")
    assert sections[0].bullets == ["x", "y"]


def test_parse_recovers_complete_sections_from_truncated_json() -> None:
    """A response cut off mid-document must still yield every COMPLETE section (not collapse to the
    tiny fallback). This is the core fix for half-completed documents."""
    from app.services.documents import DocumentService

    truncated = (
        '{"title": "Quarterly Plan", "subtitle": "FY26", "theme": "emerald", "sections": ['
        '{"heading": "Overview", "body": "Full first section.", "bullets": ["a", "b"]},'
        '{"heading": "Roadmap", "body": "Second section complete.", '
        '"table": {"headers": ["Phase","When"], "rows": [["1","Q1"],["2","Q2"]]}},'
        '{"heading": "Truncat'  # <-- the response was cut off here (no close)
    )
    parsed = DocumentService._parse(truncated)
    assert parsed is not None
    title, subtitle, theme, sections = parsed
    assert (title, subtitle, theme) == ("Quarterly Plan", "FY26", "emerald")
    assert [s.heading for s in sections] == ["Overview", "Roadmap"]  # the cut-off 3rd is dropped
    assert sections[1].table is not None and sections[1].table.headers == ["Phase", "When"]


def test_fallback_is_an_honest_notice_not_fabricated_content() -> None:
    """When the model returns nothing, the fallback must be an HONEST, on-topic notice — titled by
    the prompt, clearly stating content could not be generated, and with NO fabricated table/filler
    (the user complained the old scaffold served irrelevant boilerplate + a forced table)."""
    from app.services.documents import DocumentService

    title, subtitle, sections = DocumentService._fallback("Full documentation on how to use GitHub CI/CD")
    assert title.startswith("Full documentation on how to use GitHub CI/CD")  # on-topic title
    assert len(sections) == 1
    assert "could not" in sections[0].body.lower()  # plainly says it failed
    assert all(s.table is None for s in sections)  # never invents a table in the fallback


def test_latin1_transliterates_unicode_punctuation_for_pdf() -> None:
    """PDF latin-1 sanitization must transliterate smart punctuation to ASCII (not '?')."""
    from app.services.doc_render import _latin1

    out = _latin1("Scope creep — “quoted” café… bullet • arrow →")
    assert "—" not in out and "“" not in out and "•" not in out
    assert "?" not in out.replace("café", "")  # the accented é is latin-1-safe; no '?' from punctuation
    assert "-" in out and '"quoted"' in out and "..." in out and "->" in out


_RICH_SECTIONS = [
    {"heading": "Section 1", "body": "Body text.", "bullets": ["First point", "Second point ✓", "Third"]},
    {"heading": "Comparison", "body": "A small table.",
     "table": {"headers": ["Plan", "Price", "Notes"], "rows": [["Free", "$0", "Starter"], ["Pro", "$20", "Teams"]]}},
]


@pytest.mark.parametrize("fmt", ["pptx", "docx", "pdf"])
def test_real_render_produces_file(tmp_path, monkeypatch, fmt: str) -> None:
    """When the optional lib is installed, render a real, styled file (bullets + table + theme),
    bypassing the disable flag."""
    if not _engine_installed(fmt):
        pytest.skip(f"{_FMT_MODULE[fmt]} not installed")
    monkeypatch.delenv("OMNIVRA_DISABLE_RENDER", raising=False)
    out = tmp_path / f"doc.{fmt}"
    result = render_document(
        "Title ✓ unicode",  # exercises the latin-1 sanitizer for pdf
        _RICH_SECTIONS,
        out,
        fmt,
        subtitle="A styled subtitle ✓",
        theme="emerald",
    )
    assert result["ok"] and not result["stub"], result
    assert out.exists() and out.stat().st_size > 100


def test_unknown_theme_falls_back_without_error(tmp_path, monkeypatch) -> None:
    """An unknown theme name must resolve to the default palette, never raise."""
    if not _engine_installed("pdf"):
        pytest.skip("fpdf not installed")
    monkeypatch.delenv("OMNIVRA_DISABLE_RENDER", raising=False)
    out = tmp_path / "doc.pdf"
    result = render_document("T", _RICH_SECTIONS, out, "pdf", theme="not-a-real-theme")
    assert result["ok"] and not result["stub"] and out.exists()


@pytest.mark.parametrize("fmt", ["pptx", "docx", "pdf"])
def test_degenerate_table_does_not_break_render(tmp_path, monkeypatch, fmt: str) -> None:
    """A malformed all-empty table ({headers:[], rows:[[],[]]}) must NOT crash any renderer
    (regression: it once raised ZeroDivisionError in PPTX -> whole deck degraded to markdown)."""
    if not _engine_installed(fmt):
        pytest.skip(f"{_FMT_MODULE[fmt]} not installed")
    monkeypatch.delenv("OMNIVRA_DISABLE_RENDER", raising=False)
    out = tmp_path / f"doc.{fmt}"
    sections = [{"heading": "Bad table", "body": "x", "table": {"headers": [], "rows": [[], []]}}]
    result = render_document("T", sections, out, fmt)
    assert result["ok"] and not result["stub"], result
    assert out.exists()


def test_pptx_has_entrance_animations(tmp_path, monkeypatch) -> None:
    """Content-bearing slides must carry an injected <p:timing> entrance animation tree."""
    if not _engine_installed("pptx"):
        pytest.skip("pptx not installed")
    monkeypatch.delenv("OMNIVRA_DISABLE_RENDER", raising=False)
    out = tmp_path / "deck.pptx"
    assert render_document("Deck", _RICH_SECTIONS, out, "pptx", subtitle="Sub", theme="violet")["ok"]

    from pptx import Presentation
    from pptx.oxml.ns import qn

    prs = Presentation(str(out))
    animated = [s for s in prs.slides if s._element.find(qn("p:timing")) is not None]
    assert animated, "expected at least one slide with an entrance-animation <p:timing> tree"
