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

import hashlib
import math
import os
from dataclasses import dataclass, field
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
    zebra fill for table data rows, ``ink`` is body text, ``series`` colors chart data."""

    name: str
    primary: RGB
    accent: RGB
    heading: RGB
    ink: RGB
    row_alt: RGB
    series: tuple[RGB, ...] = field(default_factory=tuple)

    def chart_colors(self) -> list[RGB]:
        """Palette for chart series/points — the explicit ``series`` or a primary/accent default."""
        return list(self.series) if self.series else [self.primary, self.accent, self.heading]


THEMES: dict[str, Theme] = {
    "indigo": Theme("indigo", (79, 70, 229), (6, 182, 212), (67, 56, 202), (31, 41, 55), (238, 242, 255),
                    ((79, 70, 229), (6, 182, 212), (168, 85, 247), (244, 114, 182), (52, 211, 153))),
    "emerald": Theme("emerald", (5, 150, 105), (13, 148, 136), (4, 120, 87), (31, 41, 55), (236, 253, 245),
                     ((5, 150, 105), (16, 185, 129), (13, 148, 136), (132, 204, 22), (45, 212, 191))),
    "amber": Theme("amber", (217, 119, 6), (234, 88, 12), (180, 83, 9), (41, 37, 36), (255, 251, 235),
                   ((217, 119, 6), (234, 88, 12), (245, 158, 11), (202, 138, 4), (251, 191, 36))),
    "violet": Theme("violet", (124, 58, 237), (217, 70, 239), (109, 40, 217), (31, 41, 55), (245, 243, 255),
                    ((124, 58, 237), (217, 70, 239), (168, 85, 247), (139, 92, 246), (236, 72, 153))),
    "slate": Theme("slate", (51, 65, 85), (2, 132, 199), (30, 41, 59), (15, 23, 42), (241, 245, 249),
                   ((51, 65, 85), (2, 132, 199), (100, 116, 139), (14, 165, 233), (148, 163, 184))),
    "crimson": Theme("crimson", (190, 18, 60), (244, 63, 94), (159, 18, 57), (35, 20, 25), (255, 241, 242),
                     ((190, 18, 60), (244, 63, 94), (251, 113, 133), (225, 29, 72), (252, 165, 165))),
    "teal": Theme("teal", (13, 148, 136), (6, 182, 212), (15, 118, 110), (19, 42, 46), (240, 253, 250),
                  ((13, 148, 136), (6, 182, 212), (45, 212, 191), (20, 184, 166), (34, 211, 238))),
    "ocean": Theme("ocean", (2, 132, 199), (14, 165, 233), (3, 105, 161), (15, 30, 45), (240, 249, 255),
                   ((2, 132, 199), (14, 165, 233), (56, 189, 248), (59, 130, 246), (99, 102, 241))),
    "sunset": Theme("sunset", (234, 88, 12), (244, 63, 94), (194, 65, 12), (41, 25, 20), (255, 247, 237),
                    ((234, 88, 12), (244, 63, 94), (249, 115, 22), (251, 146, 60), (245, 158, 11))),
    "forest": Theme("forest", (22, 101, 52), (101, 163, 13), (20, 83, 45), (20, 35, 25), (240, 253, 244),
                    ((22, 101, 52), (101, 163, 13), (34, 197, 94), (132, 204, 22), (74, 222, 128))),
    "midnight": Theme("midnight", (30, 41, 59), (99, 102, 241), (15, 23, 42), (15, 23, 42), (241, 245, 249),
                      ((30, 41, 59), (99, 102, 241), (129, 140, 248), (56, 189, 248), (167, 139, 250))),
    "rose": Theme("rose", (190, 24, 93), (236, 72, 153), (157, 23, 77), (40, 20, 30), (253, 242, 248),
                  ((190, 24, 93), (236, 72, 153), (244, 114, 182), (219, 39, 119), (251, 182, 206))),
}
_DEFAULT_THEME = "indigo"

# Layout/style variants — vary the deck's look (cover + section header treatment) so documents
# don't all look identical. Picked deterministically from the title (stable on regenerate, varied
# across topics) by :func:`pick_style`.
STYLES = ("band", "sidebar", "minimal")


def resolve_theme(name: str | None) -> Theme:
    """Map a theme name to its palette; 'auto'/unknown/None -> the default (indigo)."""
    return THEMES.get((name or "").strip().lower(), THEMES[_DEFAULT_THEME])


def pick_style(seed: str) -> str:
    """Deterministically choose a layout style from ``seed`` (the title) — stable per document,
    varied across documents (the 'different style each time' the user asked for)."""
    h = int(hashlib.sha1((seed or "doc").encode("utf-8", "replace")).hexdigest(), 16)
    return STYLES[h % len(STYLES)]


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


_CHART_TYPES = {"column", "bar", "line", "pie", "area"}


def _num(v: Any) -> float:
    """Coerce a possibly-stringy value to a FINITE float (strip %, $, commas); non-numeric or
    non-finite (inf/nan) -> 0.0 so it never breaks the chart's embedded worksheet writer."""
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else 0.0
    s = str(v).strip().replace(",", "").replace("$", "").replace("%", "")
    try:
        f = float(s)
    except (TypeError, ValueError):
        return 0.0
    return f if math.isfinite(f) else 0.0


def _norm_chart(chart: Any) -> tuple[str, str, list[str], list[tuple[str, list[float]]]] | None:
    """Normalize a section's ``chart`` (dict | None) into (type, title, categories, series), or None
    when there's no usable numeric data. Categories/series are padded so every series aligns."""
    if not isinstance(chart, dict):
        return None
    ctype = str(chart.get("type", "column")).strip().lower()
    if ctype not in _CHART_TYPES:
        ctype = "column"
    title = str(chart.get("title", "")).strip()
    categories = [str(c).strip() for c in (chart.get("categories") or [])]
    series: list[tuple[str, list[float]]] = []
    for s in (chart.get("series") or []):
        if not isinstance(s, dict):
            continue
        values = [_num(v) for v in (s.get("values") or [])]
        if values:
            series.append((str(s.get("name", "")).strip(), values))
    if not series:
        return None
    width = max(len(categories), max(len(v) for _, v in series))
    if width == 0:
        return None
    if len(categories) < width:  # synthesize missing category labels
        categories += [str(i + 1) for i in range(len(categories), width)]
    categories = categories[:width]
    series = [(name, (vals + [0.0] * width)[:width]) for name, vals in series]
    if ctype == "pie" and len(series) > 1:  # a pie is single-series — keep only the first so
        series = series[:1]                  # PPTX and the DOCX/PDF data table agree
    return ctype, title, categories, series


def _chart_to_table(chart_tuple: tuple[str, str, list[str], list[tuple[str, list[float]]]]) -> tuple[str, tuple[list[str], list[list[str]]]]:
    """Render a normalized chart as a (caption, table) pair for DOCX/PDF (which don't draw charts).
    Caption is the chart title; the table is Category + one column per series."""
    ctype, title, categories, series = chart_tuple
    headers = ["Category"] + [name or f"Series {i+1}" for i, (name, _) in enumerate(series)]

    def _fmt(x: float) -> str:
        return str(int(x)) if float(x).is_integer() else f"{x:g}"

    rows = [[cat] + [_fmt(vals[i]) for _, vals in series] for i, cat in enumerate(categories)]
    return (title or f"{ctype.title()} chart"), (headers, rows)


# ===========================================================================
# PPTX
# ===========================================================================
def _render_pptx(title: str, subtitle: str, sections: list[dict[str, Any]], out: Path, theme: Theme) -> None:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    W, H = prs.slide_width, prs.slide_height
    primary, accent = RGBColor(*theme.primary), RGBColor(*theme.accent)
    ink, heading_c = RGBColor(*theme.ink), RGBColor(*theme.heading)
    white, light, muted = RGBColor(*_WHITE), RGBColor(248, 250, 252), RGBColor(140, 140, 150)
    style = pick_style(title)  # 'band' | 'sidebar' | 'minimal' — varies the look per document

    def rect(slide, left, top, width, height, color):
        shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shp.fill.solid()
        shp.fill.fore_color.rgb = color
        shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def textbox(slide, left, top, width, height, anchor=MSO_ANCHOR.TOP):
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        return tb, tf

    def put(tf, text, size, color, *, bold=False, para=None):
        p = tf.paragraphs[0] if para is None else para
        r = p.add_run()
        r.text = text
        r.font.size, r.font.bold, r.font.color.rgb = Pt(size), bold, color
        return r

    # ---- Cover slide (per style) ----
    cover = prs.slides.add_slide(blank)
    if style == "sidebar":
        rect(cover, 0, 0, Inches(5.1), H, primary)
        rect(cover, Inches(0.7), Inches(3.5), Inches(2.0), Inches(0.11), accent)
        _, tf = textbox(cover, Inches(0.7), Inches(1.4), Inches(3.9), Inches(3.2), MSO_ANCHOR.MIDDLE)
        put(tf, title or "Untitled", 46, white, bold=True)
        _, tf = textbox(cover, Inches(5.6), Inches(2.9), Inches(7.0), Inches(2.0), MSO_ANCHOR.MIDDLE)
        put(tf, subtitle or "Generated by Omnivra AI Company OS", 26, ink)
        _, tf = textbox(cover, Inches(5.6), Inches(6.8), Inches(7.0), Inches(0.4))
        put(tf, "Omnivra AI Company OS", 11, muted)
    elif style == "minimal":
        rect(cover, 0, 0, W, H, light)
        rect(cover, Inches(0.9), Inches(4.0), Inches(3.0), Inches(0.14), accent)
        _, tf = textbox(cover, Inches(0.9), Inches(2.2), Inches(11.5), Inches(1.8), MSO_ANCHOR.BOTTOM)
        put(tf, title or "Untitled", 60, primary, bold=True)
        _, tf = textbox(cover, Inches(0.9), Inches(4.3), Inches(11.5), Inches(1.0))
        put(tf, subtitle or "Generated by Omnivra AI Company OS", 26, ink)
        _, tf = textbox(cover, Inches(0.9), Inches(6.85), Inches(11.5), Inches(0.4))
        put(tf, "Omnivra AI Company OS", 11, muted)
    else:  # band — full-bleed
        rect(cover, 0, 0, W, H, primary)
        rect(cover, Inches(0.9), Inches(4.2), Inches(2.6), Inches(0.13), accent)
        _, tf = textbox(cover, Inches(0.9), Inches(2.4), Inches(11.5), Inches(1.7), MSO_ANCHOR.BOTTOM)
        put(tf, title or "Untitled", 56, white, bold=True)
        _, tf = textbox(cover, Inches(0.9), Inches(4.45), Inches(11.5), Inches(1.0))
        put(tf, subtitle or "Generated by Omnivra AI Company OS", 26, white)
        _, tf = textbox(cover, Inches(0.9), Inches(6.9), Inches(11.5), Inches(0.4))
        put(tf, "Omnivra AI Company OS", 12, white)

    def section_header(slide, heading: str) -> tuple[float, float, float]:
        """Draw the per-style section header; return (content_left, content_width, content_top) in inches."""
        if style == "sidebar":
            rect(slide, 0, 0, Inches(0.45), H, primary)  # full-height accent bar
            _, tf = textbox(slide, Inches(0.85), Inches(0.4), Inches(12.0), Inches(0.95), MSO_ANCHOR.MIDDLE)
            put(tf, heading, 36, heading_c, bold=True)
            rect(slide, Inches(0.85), Inches(1.42), Inches(11.9), Inches(0.05), accent)
            return 0.85, 11.9, 1.7
        if style == "minimal":
            _, tf = textbox(slide, Inches(0.7), Inches(0.45), Inches(12.0), Inches(0.95), MSO_ANCHOR.MIDDLE)
            put(tf, heading, 38, heading_c, bold=True)
            rect(slide, Inches(0.7), Inches(1.45), Inches(4.6), Inches(0.08), accent)
            return 0.7, 11.95, 1.8
        # band
        rect(slide, 0, 0, W, Inches(1.2), primary)
        rect(slide, 0, Inches(1.2), W, Inches(0.07), accent)
        _, tf = textbox(slide, Inches(0.6), Inches(0.2), Inches(12.1), Inches(0.85), MSO_ANCHOR.MIDDLE)
        put(tf, heading, 38, white, bold=True)
        return 0.6, 12.1, 1.65

    FLOOR = 6.9  # content bottom limit (in): everything must end above the footer rule (7.35in)

    def draw_table(slide, headers, rows, cl, cw, top, max_h) -> tuple[list[int], float]:
        """Draw a styled table clamped to ``max_h``: only the rows that fit are shown, with a
        '+N more rows' note when truncated. Returns (shape_ids, height_used)."""
        ncols, per_row = len(headers), 0.52
        fit = max(1, int(max_h / per_row) - 1)
        truncated = len(rows) > fit
        if truncated:  # reserve a line for the note
            fit = max(1, int((max_h - 0.32) / per_row) - 1)
        shown = rows[:fit]
        nrows = len(shown) + 1
        theight = min(max_h - (0.32 if truncated else 0.0), per_row * nrows)
        gf = slide.shapes.add_table(nrows, ncols, Inches(cl), Inches(top), Inches(cw), Inches(theight))
        tbl = gf.table
        col_w = int(Inches(cw) / ncols)
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
            pf.font.bold, pf.font.size, pf.font.color.rgb = True, Pt(18), white
        alt = RGBColor(*theme.row_alt)
        for ri, row in enumerate(shown, start=1):
            for c, val in enumerate(row):
                cell = tbl.cell(ri, c)
                cell.fill.solid()
                cell.fill.fore_color.rgb = alt if ri % 2 == 0 else white
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.text = val
                pf = cell.text_frame.paragraphs[0]
                pf.font.size, pf.font.color.rgb = Pt(16), ink
        ids, used = [gf.shape_id], theight
        if truncated:
            tb, tf = textbox(slide, Inches(cl), Inches(top + theight + 0.02), Inches(cw), Inches(0.28))
            put(tf, f"+{len(rows) - len(shown)} more rows", 12, muted)
            ids.append(tb.shape_id)
            used += 0.32
        return ids, used

    # ---- Section slides ----
    for idx, sec in enumerate(sections, start=1):
        slide = prs.slides.add_slide(blank)
        anim_targets: list[int] = []
        cl, cw, ctop = section_header(slide, sec.get("heading", ""))
        cur = ctop
        body = (sec.get("body") or "").strip()
        bullets = [str(b).strip() for b in (sec.get("bullets") or []) if str(b).strip()]
        chart = _norm_chart(sec.get("chart"))
        table = _norm_table(sec.get("table"))
        has_visual = bool(chart or table)

        # Each text block is sized to a bounded box with TEXT_TO_FIT_SHAPE (shrink-on-overflow),
        # and `cur` advances by the box height — so text never spills below its box or off-slide,
        # and a following chart/table never overlaps it.
        if body:
            room = max(0.6, FLOOR - cur)
            bx = max(0.7, min(2.6, room * (0.42 if has_visual else (0.72 if bullets else 1.0))))
            tb, tf = textbox(slide, Inches(cl), Inches(cur), Inches(cw), Inches(bx))
            tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            put(tf, body, 26, ink)
            anim_targets.append(tb.shape_id)
            cur += bx + 0.12

        if bullets:
            reserve = 2.2 if has_visual else 0.0  # leave room for the chart/table below
            avail = max(0.6, FLOOR - cur - reserve)
            per = 0.62  # taller per-bullet allowance for the larger 26pt text
            max_b = max(1, int(avail / per))
            shown = bullets[:max_b]
            more = len(bullets) - len(shown)
            box_h = min(avail, len(shown) * per + (0.32 if more else 0.0))
            tb, tf = textbox(slide, Inches(cl + 0.1), Inches(cur), Inches(cw - 0.1), Inches(box_h))
            tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            for i, b in enumerate(shown):
                para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                dot = para.add_run()
                dot.text = "▪  "
                dot.font.size, dot.font.color.rgb = Pt(24), accent
                run = para.add_run()
                run.text = b
                run.font.size, run.font.color.rgb = Pt(26), ink
                para.space_after = Pt(8)
            if more:
                p = tf.add_paragraph()
                r = p.add_run()
                r.text = f"(+{more} more)"
                r.font.size, r.font.italic, r.font.color.rgb = Pt(14), True, muted
            anim_targets.append(tb.shape_id)
            cur += box_h + 0.15

        # Visual(s): a chart, then a distinct table if one ALSO exists (matching DOCX/PDF, which
        # render both). Each is clamped to the remaining room above the footer so nothing runs off.
        if chart:
            room = FLOOR - cur
            if room >= 1.7:
                try:
                    ch_h = min(4.2, room)
                    gf = _pptx_chart(slide, chart, Inches(cl), Inches(cur), Inches(cw), Inches(ch_h), theme)
                    anim_targets.append(gf.shape_id)
                    cur += ch_h + 0.12
                except Exception as exc:  # noqa: BLE001 - degrade to the chart's data table
                    logger.warning("pptx chart fell back to a table: {}", repr(exc))
                    if table is None:
                        table = _chart_to_table(chart)[1]
            elif table is None:  # not enough room for a chart -> show its data compactly instead
                table = _chart_to_table(chart)[1]

        if table:
            room = FLOOR - cur
            if room >= 0.7:
                ids, used = draw_table(slide, table[0], table[1], cl, cw, cur, room)
                anim_targets.extend(ids)
                cur += used + 0.1

        # Footer accent line + slide number
        rect(slide, 0, Inches(7.35), W, Inches(0.05), accent)
        _, tf = textbox(slide, Inches(12.2), Inches(6.95), Inches(0.9), Inches(0.4), MSO_ANCHOR.MIDDLE)
        tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
        put(tf, str(idx), 11, muted)
        try:
            _pptx_add_fade_in(slide, anim_targets)
        except Exception as exc:  # noqa: BLE001 - animation is a nicety; never fail the file over it
            logger.warning("pptx animation injection skipped: {}", repr(exc))

    prs.save(str(out))


def _pptx_chart(slide, chart_tuple, x, y, cx, cy, theme: Theme):
    """Draw a native PPTX chart (column/bar/line/pie/area) themed with the palette. Returns the
    GraphicFrame. Raises on bad data so the caller can fall back to a data table."""
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    from pptx.util import Pt

    ctype, title, categories, series = chart_tuple
    type_map = {
        "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "bar": XL_CHART_TYPE.BAR_CLUSTERED,
        "line": XL_CHART_TYPE.LINE_MARKERS,
        "pie": XL_CHART_TYPE.PIE,
        "area": XL_CHART_TYPE.AREA,
    }
    xltype = type_map.get(ctype, XL_CHART_TYPE.COLUMN_CLUSTERED)

    cd = CategoryChartData()
    cd.categories = categories
    if ctype == "pie":  # pie shows a single series
        name, values = series[0]
        cd.add_series(name or title or "Series", values)
    else:
        for name, values in series:
            cd.add_series(name or "Series", values)

    gframe = slide.shapes.add_chart(xltype, x, y, cx, cy, cd)
    chart = gframe.chart
    palette = theme.chart_colors()

    chart.has_title = bool(title)
    if title:
        tf = chart.chart_title.text_frame
        tf.text = title
        tf.paragraphs[0].font.size = Pt(20)
        tf.paragraphs[0].font.bold = True

    multi = len(series) > 1 or ctype == "pie"
    chart.has_legend = multi
    if multi:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(14)

    plot = chart.plots[0]
    if ctype == "pie":
        plot.has_data_labels = True
        # show_percentage makes PowerPoint compute each slice's SHARE of the whole; without it,
        # numFmt '0%' would format the raw value (e.g. 70 -> '7000%').
        plot.data_labels.show_percentage = True
        plot.data_labels.show_value = False
        plot.data_labels.number_format = "0%"
        plot.data_labels.number_format_is_linked = False
        plot.data_labels.font.size = Pt(14)
        for i, point in enumerate(chart.series[0].points):
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = RGBColor(*palette[i % len(palette)])
    else:
        for i, s in enumerate(chart.series):
            col = RGBColor(*palette[i % len(palette)])
            if ctype == "line":
                s.format.line.color.rgb = col
            else:
                s.format.fill.solid()
                s.format.fill.fore_color.rgb = col
        try:  # bigger axis tick labels for readability
            chart.category_axis.tick_labels.font.size = Pt(14)
            chart.value_axis.tick_labels.font.size = Pt(14)
        except Exception:  # noqa: BLE001 - some chart types lack one of the axes
            pass
    return gframe


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

    def add_data_table(headers: list[str], rows: list[list[str]]) -> None:
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
            add_data_table(*table)

        # DOCX has no easy native chart -> render the chart's data as a captioned table.
        chart = _norm_chart(sec.get("chart"))
        if chart:
            caption, (c_headers, c_rows) = _chart_to_table(chart)
            cap = doc.add_paragraph()
            cr = cap.add_run(caption)
            cr.bold = True
            cr.italic = True
            cr.font.color.rgb = heading_c
            add_data_table(c_headers, c_rows)

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

        # PDF: render the chart's data as a captioned table (no native chart engine).
        chart = _norm_chart(sec.get("chart"))
        if chart:
            caption, c_table = _chart_to_table(chart)
            pdf.ln(1)
            pdf.set_text_color(*theme.heading)
            pdf.set_font("Helvetica", "BI", 11)
            cell(6, caption)
            _pdf_table(pdf, c_table, theme, EPW)
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
