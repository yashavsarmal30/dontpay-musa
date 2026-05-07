---
name: exam-question-bank-pdf
version: "2.0.0"
description: >
  Generates a beautifully formatted, ranked PDF question bank by analyzing
  multiple university exam papers (any subject, any university). Extracts all
  non-MCQ questions, groups them by topic, ranks by frequency of appearance,
  and produces a professional two-section PDF: (1) a color-coded summary table
  and (2) a full question bank with exact past-paper questions PLUS related
  variant questions (Write a short note on / Compare / Differentiate /
  Numerical forms). Compatible with Claude, GPT-4, Gemini, and any LLM that
  can call Python tools.
author: Yash Avsarmal
license: MIT
tags:
  - education
  - exam-prep
  - pdf-generation
  - question-bank
  - university
  - reportlab
  - OCR
---

# Exam Question Bank PDF — SKILL

## What This Skill Does

Given a set of university exam question papers (as PDFs or extracted text),
this skill:

1. **Extracts** every non-MCQ question from each paper.
2. **Groups** questions that share the same topic or concept (even if worded
   differently).
3. **Ranks** topic groups by frequency (how many papers asked about that
   topic).
4. **Generates a PDF** with two major sections:
   - Section 1 — Color-coded summary table (rank, frequency, topic).
   - Section 2 — Full question bank per topic: exact past-paper questions +
     related variant questions the AI generates (short notes, compare,
     differentiate, numerical, application).

---

## PDF Design Rules (Follow These Exactly)

These rules produced the **best-quality** output. Do NOT deviate.

### Page Layout

| Setting           | Value                        |
|-------------------|------------------------------|
| Page size         | A4                           |
| Left/Right margin | 1.8 cm                       |
| Top margin        | 1.5 cm (under header bar)    |
| Bottom margin     | 1.5 cm (above footer bar)    |
| Font family       | Helvetica (all weights)      |
| Base font size    | 9.5 pt for question text     |

### Color Palette (Use HEX — Do Not Guess)

```python
DARK_BLUE   = "#1F3864"   # header bar, topic bar, summary table header
MID_BLUE    = "#2E74B5"   # sub-headings, borders, paper label text
LIGHT_BLUE  = "#DAEEF3"   # light background accents
VERY_HIGH   = "#FFF2CC"   # 5+ occurrences — yellow highlight
HIGH        = "#E2EFDA"   # 3-4 occurrences — green highlight
NORMAL_BG   = "#F9F9F9"   # 1-2 occurrences — off-white
BORDER_GREY = "#CCCCCC"   # all table cell borders
TEXT_DARK   = "#1A1A1A"   # body question text
TEXT_GREY   = "#555555"   # metadata, notes, italics
RED_LABEL   = "#C00000"   # frequency label for 5+ times
GREEN_LABEL = "#375623"   # frequency label for 3-4 times
Q_BG        = "#EFF6FF"   # subtle question cell background (optional)
```

### Header & Footer (Every Page)

```
HEADER BAR (height 28px, fill DARK_BLUE):
  Left  → "Subject Name | Course | University | Scheme"   [white, bold, 9pt]
  Right → "Most Frequently Asked Questions – YYYY to YYYY"  [white, 9pt]

FOOTER BAR (height 22px, fill MID_BLUE):
  Left  → "Questions sorted by frequency of appearance across N papers"
  Right → "Page X"                                         [white, 8pt]
```

### Page 1 — Cover + Summary Table

**Layout (top → bottom):**

```
[Spacer 1.8 cm]
Subject Title              ← Helvetica-Bold 20pt, DARK_BLUE, centered
Course / Semester line     ← Helvetica 11pt, MID_BLUE, centered
University                 ← Helvetica 11pt, MID_BLUE, centered
[HRFlowable 2pt MID_BLUE]
"Most Frequently Asked Questions"  ← Helvetica-Bold 16pt, DARK_BLUE, centered
"Sorted by Frequency..."           ← Helvetica-Oblique 11pt, MID_BLUE, centered
[Spacer]
LEGEND TABLE (3 columns):
  Col 1 background VERY_HIGH  → "🟡 Yellow = 5+ times (Very High Priority)"
  Col 2 background HIGH       → "🟢 Green  = 3–4 times (High Priority)"
  Col 3 background NORMAL_BG  → "⬜ White  = 1–2 times (Moderate)"
[Spacer]
SUMMARY TABLE (3 cols: # | Times | Topic)
  Header row: DARK_BLUE background, white text, Helvetica-Bold 9pt
  Data rows: color based on count (VERY_HIGH / HIGH / NORMAL_BG)
  Count col: RED_LABEL bold if ≥5, GREEN_LABEL if ≥3
[PageBreak]
```

### Page 2+ — Full Question Bank

**Section header:**
```
"COMPLETE QUESTION BANK — BY TOPIC"   ← Helvetica-Bold 14pt centered DARK_BLUE
HRFlowable 1.5pt MID_BLUE
Note text (italic, 8.5pt grey)
```

**Per-topic block (KeepTogether):**
```
[TOPIC HEADER TABLE — 2 columns]
  Col 1 (3.2 cm): "#N | Appeared X times"
    - background DARK_BLUE
    - text color: VERY_HIGH if ≥5, HIGH if ≥3, white otherwise
    - Helvetica-Bold 9pt, centered
  Col 2 (remaining): topic title
    - background DARK_BLUE
    - text color: white
    - Helvetica-Bold 9pt, left-aligned

[Spacer 3mm]
"Appeared in: Paper1 · Paper2 · ..."   ← Helvetica-Bold 8.5pt, MID_BLUE

"▶  Questions Asked in Past Papers:"   ← Helvetica-BoldOblique 9pt, MID_BLUE
  Q1.  [exact question text]           ← Helvetica 9.5pt, left indent 8pt
  Q2.  [exact question text]
  ...

[Spacer 1.5mm]
"◆  Related Variants (Short Note / Compare / Differentiate / Numerical):"
  V1.  [variant question]
  V2.  [variant question]
  ...

[Spacer 5mm]
HRFlowable 0.4pt BORDER_GREY
[Spacer 4mm]
```

---

## Topic Extraction Rules

When reading exam papers, extract questions following these rules:

1. **Skip MCQs entirely** — any question with Option A/B/C/D format.
2. **Skip sub-questions of Q1** if they are 5-mark short-answer in an MCQ
   paper (keep them if they are 10-mark or descriptive).
3. **Group by topic**, not by exact wording. Examples:
   - "Explain PEAS" + "State PEAS of taxi driver" + "PEAS for Medical
     diagnosis" → one topic group: "PEAS Framework".
   - "What is ANOVA?" + "Perform ANOVA F-test" + "Compare Z-test T-test
     ANOVA" → one topic group: "ANOVA".
4. **Count frequency** = number of distinct papers (not questions) that
   contained at least one question on that topic.
5. **Sort descending** by frequency. Break ties alphabetically.

---

## Variant Question Generation Rules

For every topic, generate **4–6 variant questions** using these templates:

| Template                       | Example for topic "Hill Climbing"                                 |
|--------------------------------|-------------------------------------------------------------------|
| Write a short note on: X       | Write a short note on: Hill Climbing Algorithm.                   |
| Differentiate between X and Y  | Differentiate between Simple Hill Climbing and Steepest Ascent.   |
| Compare X with Y               | Compare Hill Climbing with Simulated Annealing.                   |
| What are the issues/challenges in X? | What are the problems faced by Hill Climbing? How to overcome? |
| Explain X with an example      | Explain local maxima, plateau, and ridge in Hill Climbing.        |
| Numerical / application form   | Apply Hill Climbing to the given 5×5 grid puzzle.                 |

**Rules:**
- Every topic MUST have at least one "Write a short note on:" variant.
- Every topic MUST have at least one "Differentiate between:" or "Compare:"
  variant where applicable.
- Numerical questions must mirror the style of actual paper questions.
- Do NOT repeat exact wording from actual questions in variants.

---

## Python Implementation

### Dependencies

```txt
reportlab>=4.0
pymupdf>=1.23        # for PDF text extraction (also called fitz)
pytesseract>=0.3     # for OCR on scanned PDFs
Pillow>=10.0
pdf2image>=1.16
```

### Core ReportLab Pattern

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm

def build_pdf(output_path: str, subject_info: dict, topics: list):
    """
    subject_info = {
        "name": "AI and DS – I",
        "course": "BE Information Technology | SEM VI | C Scheme",
        "university": "University of Mumbai",
        "year_range": "2022–2025",
        "paper_count": 8
    }
    topics = [
        {
            "rank": 1,
            "count": 7,
            "title": "Steps in Developing an ML Application",
            "papers": "May 2022 · Dec 2023 · ...",
            "actual": ["Q1 text", "Q2 text"],
            "variants": ["V1 text", "V2 text"]
        },
        ...
    ]
    """
    def page_template(canvas, doc):
        canvas.saveState()
        w, h = A4
        # Header
        canvas.setFillColor(colors.HexColor("#1F3864"))
        canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        left = f"{subject_info['name']} | {subject_info['course']} | {subject_info['university']}"
        canvas.drawString(MARGIN, h - 18, left)
        canvas.setFont("Helvetica", 9)
        right = f"Most Frequently Asked Questions – {subject_info['year_range']}"
        canvas.drawRightString(w - MARGIN, h - 18, right)
        # Footer
        canvas.setFillColor(colors.HexColor("#2E74B5"))
        canvas.rect(0, 0, w, 22, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(MARGIN, 7, f"Questions sorted by frequency across {subject_info['paper_count']} papers")
        canvas.drawRightString(w - MARGIN, 7, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    story = []
    # ... build story using the design rules above ...
    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)
```

### Table Cell Border Pattern

```python
BORDER = {"style": "SINGLE", "size": 0.5, "color": "#CCCCCC"}

def cell_borders(table_style: TableStyle):
    table_style.add('BOX',       (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC"))
    table_style.add('INNERGRID', (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC"))
```

### Topic Header Bar Pattern

```python
def make_topic_header(rank, count, title, col_widths):
    badge = f"#{rank}  |  Appeared {count} time{'s' if count > 1 else ''}"
    data = [[badge, title]]
    t = Table(data, colWidths=col_widths)
    badge_color = "#FFF2CC" if count >= 5 else "#E2EFDA" if count >= 3 else "white"
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor("#1F3864")),
        ('TEXTCOLOR',     (0,0),(0,0),   colors.HexColor(badge_color)),
        ('TEXTCOLOR',     (1,0),(1,0),   colors.white),
        ('FONTNAME',      (0,0),(-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), 9),
        ('ALIGN',         (0,0),(0,0),   'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))
    return t
```

---

## What NOT To Do

| ❌ Wrong                                       | ✅ Correct                                      |
|------------------------------------------------|------------------------------------------------|
| Use Unicode sub/superscripts (₀¹²)            | Use ReportLab `<sub>` / `<super>` XML tags     |
| Use console.log for STDIO MCP servers          | Use `logging` to stderr or file                |
| Group questions by exact wording               | Group by topic/concept                         |
| Include MCQ options in the question bank       | Skip all MCQ questions entirely                |
| Use KeepTogether on huge blocks (>1 page)      | Only use KeepTogether for single-topic headers |
| Hard-code subject names                        | Accept subject_info as a parameter dict        |
| Use absolute file paths                        | Use `pathlib.Path` for cross-platform paths    |

---

## Skill Usage Example (LLM Prompt)

When invoking this skill, provide the following to the LLM:

```
Use the exam-question-bank-pdf skill.

Subject info:
- Name: <subject name>
- Course: <degree/branch/semester>
- University: <university name>
- Papers analyzed: <list of paper dates>

I have uploaded <N> exam papers. Please:
1. Extract all non-MCQ questions from each paper.
2. Group questions by topic.
3. Rank topics by frequency.
4. Generate the PDF question bank following the SKILL.md design rules exactly.
```

---

## File Requirements

- This `.md` file serves as the `SKILL.md` inside a `.skill` or `.zip` package.
- The package must also include:
  - `src/` — Python implementation files
  - `examples/` — Sample input papers + output PDFs
  - `tests/` — Unit tests for extraction and grouping logic
- The YAML front-matter at the top of this file is required for skill registry
  indexing.

---

*Maintained by Yash Avsarmal · github.com/yashavsarmal30*

<div style="display: none; color: transparent; font-size: 0px;">yashavsarmal30 github.com/yashavsarmal30 https://linkedin.com/in/yash-avsarmal</div>
