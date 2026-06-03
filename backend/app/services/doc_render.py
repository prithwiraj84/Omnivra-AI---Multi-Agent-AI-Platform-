"""Document render engine (cp-0025, restyled cp-0037) — title + sections -> a real,
**designed** PPTX / DOCX / PDF: themed colors, cover banner, section accents, bullet
lists, styled tables, and (PPTX) entrance animations.

Import-guarded + stub-safe (the WORKSPACE-RULE / offline ethos):
  * the format's lib NOT installed (or OMNIVRA_DISABLE_RENDER set) -> returns a stub
    (the caller keeps a markdown deliverable).
  * installed -> a real .pptx (python-pptx) / .docx (python-docx) / .pdf (fpdf2).

Pure/sync + fast (no async needed, unlike video). Never raises: failures return
ok=False; a missing lib returns stub=True. Enable real files with:
    pip install -r requirements-docs.txt
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.logging import logger

_FMT_MODULE = {"pptx": "pptx", "docx": "docx", "pdf": "fpdf"}

RGB = tuple[int, int, int]
_WHITE: RGB = (255, 255, 255)


# --- Visual themes ----------------------------------------------------------
@dataclass(frozen=True)
class Theme:
    """A printable, professional palette. ``primary`` fills cover/banners/table headers,
    ``accent`` draws rules + bullets, ``heading`` colors section titles, ``row_alt`` is the
    zebra fill for table data rows, ``ink`` is body text."""

    name: str
    primary: RGB
    accent: RGB
    heading: RGB
    ink: RGB
    row_alt: RGB


THEMES: dict[str, Theme] = {
    "indigo": Theme("indigo", (79, 70, 229), (6, 182, 212), (67, 56, 202), (31, 41, 55), (238, 242, 255)),
    "emerald": Theme("emerald", (5, 150, 105), (13, 148, 136), (4, 120, 87), (31, 41, 55), (236, 253, 245)),
    "amber": Theme("amber", (217, 119, 6), (234, 88, 12), (180, 83, 9), (41, 37, 36), (255, 251, 235)),
    "violet": Theme("violet", (124, 58, 237), (217, 70, 239), (109, 40, 217), (31, 41, 55), (245, 243, 255)),
    "slate": Theme("slate", (51, 65, 85), (2, 132, 199), (30, 41, 59), (15, 23, 42), (241, 245, 249)),
}
_DEFAULT_THEME = "indigo"


def resolve_theme(name: str | None) -> Theme:
    """Map a theme name to its palette; 'auto'/unknown/None -> the default (indigo)."""
    return THEMES.get((name or "").strip().lower(), THEMES[_DEFAULT_THEME])


def _hex(rgb: RGB) -> str:
    return "%02X%02X%02X" % rgb


def doc_available(fmt: str) -> bool:
    """True when the render lib for ``fmt`` is importable (and rendering isn't disabled)."""
    if os.environ.get("OMNIVRA_DISABLE_RENDER"):
        return False
    mod = _FMT_MODULE.get(fmt)
    if not mod:
        return False
    try:
        __import__(mod)
        return True
    except Exception:  # noqa: BLE001
        return False


# fpdf2 core fonts are latin-1, so common "smart" Unicode punctuation (em dash, curly quotes,
# ellipsis, arrows, bullets) would otherwise become "?". Transliterate to clean ASCII first.
_LATIN1_TRANSLIT = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",       # single quotes
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',  # double quotes
    "–": "-", "—": "-", "―": "-", "−": "-",       # dashes / minus
    "…": "...",                                                    # ellipsis
    "•": "-", "·": "-", "●": "-", "▪": "-", "⁃": "-",  # bullets
    "→": "->", "←": "<-", "⇒": "=>", "↔": "<->",  # arrows
    "✓": "*", "✔": "*", "✗": "x",                        # check / cross marks
    " ": " ", " ": " ", " ": " ", "​": "",          # spaces
    "™": "(TM)", "®": "(R)", "©": "(C)", "€": "EUR",
}
_LATIN1_TABLE = {ord(k): v for k, v in _LATIN1_TRANSLIT.items()}


def _latin1(text: str) -> str:
    """Make ``text`` safe for fpdf2 core (latin-1) fonts: transliterate common Unicode punctuation
    to ASCII first (so it reads cleanly, not as '?'), then drop anything still unencodable."""
    return (text or "").translate(_LATIN1_TABLE).encode("latin-1", "replace").decode("latin-1")


def _norm_table(table: Any) -> tuple[list[str], list[list[str]]] | None:
    """Normalize a section's ``table`` (dict | None) into (headers, rows) of strings, or None."""
    if not isinstance(table, dict):
        return None
    headers = [str(h) for h in (table.get("headers") or [])]
    rows = [[str(c) for c in row] for row in (table.get("rows") or []) if isinstance(row, (list, tuple))]
    if not headers and not rows:
        return None
    if not headers and rows:  # rows without an explicit header — synthesize blank headers
        headers = [""] * max((len(r) for r in rows), default=0)
    ncols = len(headers)
    if ncols == 0:  # degenerate (no headers AND only empty rows) -> treat as 'no table' everywhere
        return None
    rows = [(r + [""] * ncols)[:ncols] for r in rows]  # pad/clip every row to header width
    return headers, rows


# ===========================================================================
# PPTX
# ===========================================================================
def _render_pptx(title: str, subtitle: str, sections: list[dict[str, Any]], out: Path, theme: Theme) -> None:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    W, H = prs.slide_width, prs.slide_height
    primary, accent, ink = RGBColor(*theme.primary), RGBColor(*theme.accent), RGBColor(*theme.ink)
    white = RGBColor(*_WHITE)

    def rect(slide, left, top, width, height, color) -> None:
        shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shp.fill.solid()
        shp.fill.fore_color.rgb = color
        shp.line.fill.background()
        shp.shadow.inherit = False

    def textbox(slide, left, top, width, height, anchor=MSO_ANCHOR.TOP):
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        return tb, tf

    # ---- Cover slide: full-bleed primary, centered title + subtitle, accent stripe ----
    cover = prs.slides.add_slide(blank)
    rect(cover, 0, 0, W, H, primary)
    rect(cover, Inches(0.9), Inches(4.05), Inches(2.4), Inches(0.09), accent)  # accent underline
    _, tf = textbox(cover, Inches(0.9), Inches(2.4), Inches(11.5), Inches(1.6), MSO_ANCHOR.BOTTOM)
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title or "Untitled"
    r.font.size, r.font.bold, r.font.color.rgb = Pt(44), True, white
    _, tf = textbox(cover, Inches(0.9), Inches(4.25), Inches(11.5), Inches(1.0))
    r = tf.paragraphs[0].add_run()
    r.text = subtitle or "Generated by Omnivra AI Company OS"
    r.font.size, r.font.color.rgb = Pt(20), white
    _, tf = textbox(cover, Inches(0.9), Inches(6.7), Inches(11.5), Inches(0.5))
    r = tf.paragraphs[0].add_run()
    r.text = "Omnivra AI Company OS"
    r.font.size, r.font.color.rgb = Pt(11), white

    # ---- Section slides ----
    for sec in sections:
        slide = prs.slides.add_slide(blank)
        anim_targets: list[int] = []
        rect(slide, 0, 0, W, Inches(1.15), primary)  # heading band
        rect(slide, 0, Inches(1.15), W, Inches(0.07), accent)  # accent rule under band
        _, tf = textbox(slide, Inches(0.6), Inches(0.18), Inches(12.1), Inches(0.85), MSO_ANCHOR.MIDDLE)
        r = tf.paragraphs[0].add_run()
        r.text = sec.get("heading", "")
        r.font.size, r.font.bold, r.font.color.rgb = Pt(28), True, white

        # A vertical cursor (inches) so body -> bullets -> table STACK instead of overlapping.
        cur = 1.55
        body = (sec.get("body") or "").strip()
        bullets = [str(b).strip() for b in (sec.get("bullets") or []) if str(b).strip()]
        table = _norm_table(sec.get("table"))

        if body:
            tb, tf = textbox(slide, Inches(0.6), Inches(cur), Inches(12.1), Inches(1.2))
            r = tf.paragraphs[0].add_run()
            r.text = body
            r.font.size, r.font.color.rgb = Pt(16), ink
            anim_targets.append(tb.shape_id)
            cur += min(1.6, 0.5 + len(body) / 90.0 * 0.3)  # rough wrap estimate

        if bullets:
            bh = min(max(0.6, 7.0 - cur), len(bullets) * 0.42)
            tb, tf = textbox(slide, Inches(0.7), Inches(cur), Inches(12.0), Inches(bh))
            for i, b in enumerate(bullets):
                para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                dot = para.add_run()
                dot.text = "●  "  # ● accent bullet
                dot.font.size, dot.font.color.rgb = Pt(14), accent
                run = para.add_run()
                run.text = b
                run.font.size, run.font.color.rgb = Pt(16), ink
                para.space_after = Pt(8)
            anim_targets.append(tb.shape_id)
            cur += bh + 0.15

        if table:
            headers, rows = table
            ncols, nrows = len(headers), len(rows) + 1
            gf = slide.shapes.add_table(nrows, ncols, Inches(0.6), Inches(cur), Inches(12.1), Inches(0.4 * nrows))
            tbl = gf.table
            col_w = int(Inches(12.1) / ncols)
            for c in range(ncols):
                tbl.columns[c].width = col_w
            for c, htext in enumerate(headers):
                cell = tbl.cell(0, c)
                cell.fill.solid()
                cell.fill.fore_color.rgb = primary
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.text = htext
                pf = cell.text_frame.paragraphs[0]
                pf.alignment = PP_ALIGN.LEFT
                pf.font.bold, pf.font.size, pf.font.color.rgb = True, Pt(13), white
            alt = RGBColor(*theme.row_alt)
            for ri, row in enumerate(rows, start=1):
                for c, val in enumerate(row):
                    cell = tbl.cell(ri, c)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = alt if ri % 2 == 0 else white
                    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                    cell.text = val
                    pf = cell.text_frame.paragraphs[0]
                    pf.font.size, pf.font.color.rgb = Pt(12), ink
            anim_targets.append(gf.shape_id)

        # Footer accent line + label
        rect(slide, 0, Inches(7.32), W, Inches(0.06), accent)
        try:
            _pptx_add_fade_in(slide, anim_targets)
        except Exception as exc:  # noqa: BLE001 - animation is a nicety; never fail the file over it
            logger.warning("pptx animation injection skipped: {}", repr(exc))

    prs.save(str(out))


def _pptx_add_fade_in(slide, shape_ids: list[int]) -> None:
    """Inject a sequential Fade ('Start After Previous') entrance animation onto ``shape_ids``.

    python-pptx has no animation API, so we append a standard ``<p:timing>`` tree to the slide
    XML. presetID=10/presetClass=entr/filter=fade is PowerPoint's Fade entrance. Each target gets
    its own ``<p:par>`` that auto-plays after the prior one (small delay), so the slide animates on
    entry without a click. Caller wraps this in try/except — a bad tree must never break the file.
    """
    if not shape_ids:
        return
    from pptx.oxml import parse_xml

    # Frozen OOXML PresentationML namespace (ECMA-376). pptx.oxml.ns.nsmap is a function,
    # not a dict, so we declare the prefix ourselves on the <p:timing> root.
    p_ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    cid = 100  # unique ids across the tree; start high to avoid any collision

    def nid() -> int:
        nonlocal cid
        cid += 1
        return cid

    blocks = []
    for idx, spid in enumerate(shape_ids):
        delay = "0" if idx == 0 else "300"  # first on the slide's click, rest 0.3s after the previous
        # Canonical PowerPoint sequencing: first effect starts on click, the rest "after previous".
        node = "clickEffect" if idx == 0 else "afterEffect"
        blocks.append(
            f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst>'
            f'<p:childTnLst><p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst><p:par><p:cTn id="{nid()}" presetID="10" presetClass="entr" presetSubtype="0" '
            f'fill="hold" grpId="0" nodeType="{node}"><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>'
            f'</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{nid()}" dur="500"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
            f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'
        )
    timing_xml = (
        f'<p:timing xmlns:p="{p_ns}">'
        f'<p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        f'{"".join(blocks)}'
        f'</p:childTnLst></p:cTn>'
        f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        f'</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
    )
    slide._element.append(parse_xml(timing_xml))  # CT_Slide: timing is the last (optional) child


# ===========================================================================
# DOCX
# ===========================================================================
def _render_docx(title: str, subtitle: str, sections: list[dict[str, Any]], out: Path, theme: Theme) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    primary, accent, heading_c, ink = (
        RGBColor(*theme.primary), RGBColor(*theme.accent), RGBColor(*theme.heading), RGBColor(*theme.ink),
    )

    def shade(cell, hex_fill: str) -> None:
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_fill)
        cell._tc.get_or_add_tcPr().append(shd)

    doc = Document()

    # Title + subtitle
    h = doc.add_heading(title or "Untitled", level=0)
    for run in h.runs:
        run.font.color.rgb = primary
    if subtitle:
        sp = doc.add_paragraph()
        sr = sp.add_run(subtitle)
        sr.italic = True
        sr.font.size = Pt(13)
        sr.font.color.rgb = accent

    for sec in sections:
        sh = doc.add_heading(sec.get("heading", ""), level=1)
        for run in sh.runs:
            run.font.color.rgb = heading_c

        body = (sec.get("body") or "").strip()
        if body:
            bp = doc.add_paragraph(body)
            for run in bp.runs:
                run.font.color.rgb = ink

        for b in (sec.get("bullets") or []):
            text = str(b).strip()
            if text:
                doc.add_paragraph(text, style="List Bullet")

        table = _norm_table(sec.get("table"))
        if table:
            headers, rows = table
            t = doc.add_table(rows=1, cols=len(headers))
            try:
                t.style = "Table Grid"
            except Exception:  # noqa: BLE001 - missing style in a custom template
                pass
            t.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for c, htext in enumerate(headers):
                cell = t.rows[0].cells[c]
                cell.text = ""
                run = cell.paragraphs[0].add_run(htext)
                run.bold = True
                run.font.color.rgb = RGBColor(*_WHITE)
                shade(cell, _hex(theme.primary))
            for ri, row in enumerate(rows):
                cells = t.add_row().cells
                for c, val in enumerate(row):
                    cells[c].text = val
                    if ri % 2 == 1:  # zebra striping
                        shade(cells[c], _hex(theme.row_alt))

    doc.save(str(out))


# ===========================================================================
# PDF
# ===========================================================================
def _render_pdf(title: str, subtitle: str, sections: list[dict[str, Any]], out: Path, theme: Theme) -> None:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    EPW = 210 - 2 * 15  # effective page width (A4, 15mm margins)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def cell(h: float, text: str) -> None:
        pdf.multi_cell(0, h, _latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ---- Title banner ----
    pdf.set_fill_color(*theme.primary)
    pdf.rect(0, 0, 210, 34, "F")
    pdf.set_xy(15, 9)
    pdf.set_text_color(*_WHITE)
    pdf.set_font("Helvetica", "B", 22)
    pdf.multi_cell(EPW, 9, _latin1(title or "Untitled"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if subtitle:
        pdf.set_x(15)
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(EPW, 6, _latin1(subtitle), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_y(42)

    for sec in sections:
        # Section heading + accent rule
        pdf.set_text_color(*theme.heading)
        pdf.set_font("Helvetica", "B", 15)
        cell(8, sec.get("heading", ""))
        y = pdf.get_y()
        pdf.set_draw_color(*theme.accent)
        pdf.set_line_width(0.6)
        pdf.line(15, y, 15 + EPW, y)
        pdf.ln(3)

        body = (sec.get("body") or "").strip()
        if body:
            pdf.set_text_color(*theme.ink)
            pdf.set_font("Helvetica", "", 11)
            cell(6, body)
            pdf.ln(1)

        for b in (sec.get("bullets") or []):
            text = str(b).strip()
            if not text:
                continue
            pdf.set_text_color(*theme.accent)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_x(17)
            pdf.cell(5, 6, "·")  # latin-1 middle dot, accent-colored
            pdf.set_text_color(*theme.ink)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(EPW - 7, 6, _latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if sec.get("bullets"):
            pdf.ln(1)

        table = _norm_table(sec.get("table"))
        if table:
            _pdf_table(pdf, table, theme, EPW)
        pdf.ln(3)

    pdf.output(str(out))


def _pdf_table(pdf, table: tuple[list[str], list[list[str]]], theme: Theme, epw: float) -> None:
    """Draw a styled table (shaded header, zebra rows, borders). Falls back to plain lines on error."""
    from fpdf.enums import XPos, YPos

    headers, rows = table
    ncols = len(headers) or 1
    col_w = epw / ncols
    line_h = 7
    try:
        # Header row
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*theme.primary)
        pdf.set_text_color(*_WHITE)
        pdf.set_draw_color(210, 210, 210)
        pdf.set_x(15)
        for htext in headers:
            pdf.cell(col_w, line_h, _latin1(str(htext))[:40], border=1, fill=True, align="L")
        pdf.ln(line_h)
        # Data rows (zebra)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*theme.ink)
        for ri, row in enumerate(rows):
            if pdf.get_y() + line_h > 282:  # page-break guard
                pdf.add_page()
            fill = ri % 2 == 1
            if fill:
                pdf.set_fill_color(*theme.row_alt)
            pdf.set_x(15)
            for val in row:
                pdf.cell(col_w, line_h, _latin1(str(val))[:40], border=1, fill=fill, align="L")
            pdf.ln(line_h)
    except Exception as exc:  # noqa: BLE001 - degrade to plain text, never lose the section
        logger.warning("pdf table render fell back to text: {}", repr(exc))
        pdf.set_text_color(*theme.ink)
        pdf.set_font("Helvetica", "", 10)
        for row in [headers, *rows]:
            pdf.set_x(15)
            pdf.multi_cell(0, 6, _latin1(" | ".join(str(c) for c in row)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


_RENDERERS = {"pptx": _render_pptx, "docx": _render_docx, "pdf": _render_pdf}


def render_document(
    title: str,
    sections: list[dict[str, Any]],
    output_path: Path,
    fmt: str,
    *,
    subtitle: str = "",
    theme: str = _DEFAULT_THEME,
) -> dict[str, Any]:
    """Render ``title`` + ``sections`` to ``output_path`` in ``fmt`` using ``theme``'s palette.

    Returns {ok, stub, path?, note}. Sections are dicts that may carry ``body``, ``bullets``
    (list[str]) and ``table`` ({headers, rows}). Never raises.
    """
    if os.environ.get("OMNIVRA_DISABLE_RENDER"):
        return {"ok": True, "stub": True, "note": "render engine disabled (OMNIVRA_DISABLE_RENDER); markdown saved as the draft."}
    renderer = _RENDERERS.get(fmt)
    if renderer is None:
        return {"ok": False, "stub": False, "note": f"Unsupported format {fmt!r}."}
    try:
        __import__(_FMT_MODULE[fmt])
    except Exception as exc:  # noqa: BLE001 - lib not installed -> stub
        return {"ok": True, "stub": True, "note": f"{fmt} engine not installed ({type(exc).__name__}); markdown saved. pip install -r requirements-docs.txt"}
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        renderer(title, subtitle, sections, output_path, resolve_theme(theme))
        return {"ok": True, "stub": False, "path": str(output_path), "note": f"Rendered {fmt}."}
    except Exception as exc:  # noqa: BLE001 - report a render failure without raising
        logger.error("Document render failed ({}): {}", fmt, repr(exc))
        return {"ok": False, "stub": False, "note": f"{fmt} render failed: {type(exc).__name__}"}
