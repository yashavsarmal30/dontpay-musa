"""
exam_mcp/pdf_gen.py
───────────────────
Builds the ranked question-bank PDF using ReportLab.

Design follows the SKILL.md specification exactly:
  • Page 1  : Cover + legend + summary table
  • Page 2+ : Full question bank, one block per topic

Author : Yash Avsarmal  (github.com/yashavsarmal30)
"""

from __future__ import annotations

import logging
from pathlib import Path

from reportlab.lib              import colors
from reportlab.lib.enums        import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes    import A4
from reportlab.lib.styles       import ParagraphStyle
from reportlab.lib.units        import cm, mm
from reportlab.platypus         import (
    HRFlowable, KeepTogether, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

log = logging.getLogger(__name__)

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm

# ── Color constants ───────────────────────────────────────────────────────────
C = {
    "dark_blue":   colors.HexColor("#1F3864"),
    "mid_blue":    colors.HexColor("#2E74B5"),
    "very_high":   colors.HexColor("#FFF2CC"),
    "high":        colors.HexColor("#E2EFDA"),
    "normal_bg":   colors.HexColor("#F9F9F9"),
    "border":      colors.HexColor("#CCCCCC"),
    "text_dark":   colors.HexColor("#1A1A1A"),
    "text_grey":   colors.HexColor("#555555"),
    "red_label":   colors.HexColor("#C00000"),
    "green_label": colors.HexColor("#375623"),
}

# ── Paragraph styles ──────────────────────────────────────────────────────────
def _s(name, **kw):
    return ParagraphStyle(name, **kw)

STYLES = {
    "title":   _s("title",   fontName="Helvetica-Bold",    fontSize=20, textColor=C["dark_blue"], alignment=TA_CENTER, spaceAfter=4),
    "sub":     _s("sub",     fontName="Helvetica",         fontSize=11, textColor=C["mid_blue"],  alignment=TA_CENTER, spaceAfter=2),
    "big_h":   _s("big_h",   fontName="Helvetica-Bold",    fontSize=16, textColor=C["dark_blue"], alignment=TA_CENTER, spaceAfter=6),
    "sub2":    _s("sub2",    fontName="Helvetica-Oblique", fontSize=11, textColor=C["mid_blue"],  alignment=TA_CENTER, spaceAfter=4),
    "sec_h":   _s("sec_h",   fontName="Helvetica-Bold",    fontSize=14, textColor=C["dark_blue"], alignment=TA_CENTER, spaceBefore=0, spaceAfter=10),
    "note":    _s("note",    fontName="Helvetica-Oblique", fontSize=8.5, textColor=C["text_grey"], spaceAfter=14),
    "paper":   _s("paper",   fontName="Helvetica-Bold",    fontSize=8.5, textColor=C["mid_blue"], spaceAfter=3),
    "type":    _s("type",    fontName="Helvetica-BoldOblique", fontSize=9, textColor=C["mid_blue"], spaceAfter=2, spaceBefore=4, leftIndent=8),
    "q":       _s("q",       fontName="Helvetica",         fontSize=9.5, textColor=C["text_dark"], alignment=TA_JUSTIFY, leftIndent=8, spaceAfter=2, leading=14),
}

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def build_question_bank_pdf(
    output_path: str,
    subject_info: dict,
    topics: list[dict],
) -> int:
    """
    Build the question-bank PDF and return the page count.

    subject_info keys:
        name, course, university, year_range, paper_count

    topics: list from analyser.group_and_rank_topics()
    """
    story = []
    _add_cover(story, subject_info, topics)
    _add_question_bank(story, topics)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    def page_template(canvas, doc):
        _draw_header_footer(canvas, doc, subject_info)

    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)
    log.info("PDF written to %s", output_path)

    # Count pages
    try:
        import fitz
        with fitz.open(output_path) as pdf:
            return len(pdf)
    except Exception:
        return -1


# ─────────────────────────────────────────────────────────────────────────────
# Header / footer
# ─────────────────────────────────────────────────────────────────────────────


def _draw_header_footer(canvas, doc, info: dict):
    canvas.saveState()
    w, h = A4

    # ── Header bar ──
    canvas.setFillColor(C["dark_blue"])
    canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    left = f"{info.get('name','')} | {info.get('course','')} | {info.get('university','')}"
    canvas.drawString(MARGIN, h - 18, left[:90])
    canvas.setFont("Helvetica", 9)
    right = f"Most Frequently Asked Questions – {info.get('year_range','')}"
    canvas.drawRightString(w - MARGIN, h - 18, right)

    # ── Footer bar ──
    canvas.setFillColor(C["mid_blue"])
    canvas.rect(0, 0, w, 22, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    n = info.get("paper_count", "?")
    canvas.drawString(MARGIN, 7, f"Questions sorted by frequency of appearance across {n} papers")
    canvas.drawRightString(w - MARGIN, 7, f"Page {doc.page}")
    
    # ── Ghost Text ──
    canvas.setFillColor(C["mid_blue"])
    canvas.setFont("Helvetica", 4)
    canvas.drawString(w / 2, 2, "yashavsarmal30 github.com/yashavsarmal30 https://linkedin.com/in/yash-avsarmal")
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Section builders
# ─────────────────────────────────────────────────────────────────────────────


def _add_cover(story: list, info: dict, topics: list):
    """Build cover page: title + legend + summary table."""
    story.append(Spacer(1, 1.8 * cm))
    story.append(Paragraph(info.get("name", "Subject"), STYLES["title"]))
    story.append(Paragraph(info.get("course", ""), STYLES["sub"]))
    story.append(Paragraph(info.get("university", ""), STYLES["sub"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C["mid_blue"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Most Frequently Asked Questions", STYLES["big_h"]))
    story.append(Paragraph(
        f"Sorted by Frequency of Appearance Across {info.get('paper_count','?')} Papers "
        f"({info.get('year_range','')})",
        STYLES["sub2"],
    ))
    story.append(Spacer(1, 0.4 * cm))

    # Legend
    avail_w = PAGE_W - 2 * MARGIN
    leg_data = [[
        "🟡 Yellow = 5+ times (Very High Priority – Must Prepare)",
        "🟢 Green = 3–4 times (High Priority)",
        "⬜ White = 1–2 times (Moderate)",
    ]]
    leg = Table(leg_data, colWidths=[avail_w / 3] * 3)
    leg.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), C["very_high"]),
        ("BACKGROUND",    (1, 0), (1, 0), C["high"]),
        ("BACKGROUND",    (2, 0), (2, 0), C["normal_bg"]),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX",           (0, 0), (-1, -1), 0.5, C["border"]),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, C["border"]),
    ]))
    story.append(leg)
    story.append(Spacer(1, 0.5 * cm))

    # Summary table
    col_w = [0.8 * cm, 1.4 * cm, avail_w - 2.2 * cm]
    rows = [["#", "Times", "Topic"]]
    for t in topics:
        rows.append([f"#{t['rank']}", f"{t['count']}x", t["title"]])

    summ = Table(rows, colWidths=col_w, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  C["dark_blue"]),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("ALIGN",         (0, 0), (1, -1),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("BOX",           (0, 0), (-1, -1), 0.5, C["border"]),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, C["border"]),
    ])
    for i, t in enumerate(topics, start=1):
        bg = C["very_high"] if t["count"] >= 5 else C["high"] if t["count"] >= 3 else C["normal_bg"]
        ts.add("BACKGROUND", (0, i), (-1, i), bg)
        if t["count"] >= 5:
            ts.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")
            ts.add("TEXTCOLOR", (1, i), (1, i), C["red_label"])
        elif t["count"] >= 3:
            ts.add("TEXTCOLOR", (1, i), (1, i), C["green_label"])
    summ.setStyle(ts)
    story.append(summ)
    story.append(PageBreak())


def _add_question_bank(story: list, topics: list):
    """Build the per-topic question sections."""
    avail_w = PAGE_W - 2 * MARGIN

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("COMPLETE QUESTION BANK — BY TOPIC", STYLES["sec_h"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C["mid_blue"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Each topic section lists: (A) Exact questions from past papers, and "
        "(B) Related variants — Write a short note on / Differentiate / "
        "Compare / Numerical forms of the same topic.",
        STYLES["note"],
    ))

    for t in topics:
        block = _make_topic_block(t, avail_w)
        story.append(block)


def _make_topic_block(t: dict, avail_w: float) -> KeepTogether:
    """Build one topic block as a KeepTogether flowable."""
    badge = f"#{t['rank']}  |  Appeared {t['count']} time{'s' if t['count'] > 1 else ''}"
    badge_color = C["very_high"] if t["count"] >= 5 else C["high"] if t["count"] >= 3 else colors.white

    # Topic header bar
    hdr = Table([[badge, t["title"]]], colWidths=[3.2 * cm, avail_w - 3.2 * cm])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C["dark_blue"]),
        ("TEXTCOLOR",     (0, 0), (0, 0),   badge_color),
        ("TEXTCOLOR",     (1, 0), (1, 0),   colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (0, 0), (0, 0),   "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))

    items = [
        hdr,
        Spacer(1, 3 * mm),
        Paragraph(f"<b>Appeared in:</b>  {t['papers']}", STYLES["paper"]),
        Paragraph("▶  Questions Asked in Past Papers:", STYLES["type"]),
    ]
    for i, q in enumerate(t.get("actual", []), 1):
        items.append(Paragraph(f"<b>Q{i}.</b>  {q}", STYLES["q"]))

    items.append(Spacer(1, 1.5 * mm))
    items.append(Paragraph(
        "◆  Related Variants (Short Note / Compare / Differentiate / Numerical):",
        STYLES["type"],
    ))
    for i, v in enumerate(t.get("variants", []), 1):
        items.append(Paragraph(f"<b>V{i}.</b>  {v}", STYLES["q"]))

    items += [
        Spacer(1, 5 * mm),
        HRFlowable(width="100%", thickness=0.4, color=C["border"]),
        Spacer(1, 4 * mm),
    ]
    return KeepTogether(items)
