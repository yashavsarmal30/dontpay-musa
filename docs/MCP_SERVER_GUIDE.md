# MCP Server Implementation Guide

**Author:** Yash Avsarmal · [github.com/yashavsarmal30](https://github.com/yashavsarmal30)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP CLIENT (e.g. Claude)                  │
│  User: "Upload paper.pdf and generate question bank PDF"     │
└───────────────────┬─────────────────────────────────────────┘
                    │  MCP Protocol (JSON-RPC 2.0)
                    │  Transport: STDIO  or  HTTP/SSE
                    ▼
┌─────────────────────────────────────────────────────────────┐
│               dontpay-musa MCP Server              │
│                                                              │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐   │
│  │ server.py│  │extractor  │  │analyser  │  │pdf_gen   │   │
│  │ (FastMCP)│→ │.py (OCR + │→ │.py (topic│→ │.py       │   │
│  │  tools   │  │  parser)  │  │ grouping)│  │(ReportLab│   │
│  └──────────┘  └───────────┘  └──────────┘  └──────────┘   │
│                                    │                         │
│                               ┌────▼────┐                    │
│                               │database │                    │
│                               │.py      │                    │
│                               │(SQLite) │                    │
│                               └─────────┘                    │
└──────────────────────────────────────────────────────────────┘
                    │  Optional LLM API calls
                    │  (Anthropic / OpenAI / Gemini)
                    ▼
         ┌─────────────────────┐
         │  Third-party LLM    │
         │  (for fuzzy grouping│
         │   of edge cases)    │
         └─────────────────────┘
```

---

## MCP Protocol Basics

MCP uses **JSON-RPC 2.0** over one of two transports:

| Transport       | Use Case                                  | How                                   |
|-----------------|-------------------------------------------|---------------------------------------|
| `stdio`         | Local MCP clients (Claude Desktop, etc.)  | Process stdin/stdout                  |
| `streamable-http` | Remote / HTTP clients                   | POST to `/mcp` endpoint               |

The three MCP primitives we use:

| Primitive  | What it is                            | Our usage                              |
|------------|---------------------------------------|----------------------------------------|
| **Tool**   | A callable function (like a POST endpoint) | All 6 tools (upload, analyse, etc.) |
| **Resource** | Read-only data (like a GET endpoint) | Not used (tools cover our use case)   |
| **Prompt** | Reusable prompt template              | Not used                               |

---

## FastMCP Pattern — How Each Tool Is Defined

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Exam Question Analyser", version="1.0.0")

@mcp.tool()
def upload_paper(pdf_path: str, label: str, subject: str = "") -> dict:
    """
    Register a local PDF exam paper.          ← This docstring becomes the
                                                 tool description visible to the AI.
    Args:
        pdf_path: Absolute path to the PDF.  ← Args section becomes parameter
        label: Human label, e.g. 'May 2024'.    descriptions in the tool schema.
    Returns:
        dict with status and questions_found
    """
    # ... implementation ...
    return {"status": "ok", "questions_found": 42}
```

FastMCP automatically:
- Converts Python type hints → JSON Schema for the tool input
- Uses the docstring → tool description shown to the AI
- Handles serialization of return values

---

## Extraction Pipeline (extractor.py)

```
PDF File
  │
  ├─ PyMuPDF (fitz.open)  ──→  Native text (fast, for born-digital PDFs)
  │     └─ If text < 100 chars ──→ OCR fallback
  │
  └─ OCR Fallback
       ├─ pdf2image.convert_from_path(dpi=300)  →  PIL Images
       └─ pytesseract.image_to_string(img)       →  Raw text
              │
              ▼
       _parse_questions(raw_text)
              │
              ├─ Split by line
              ├─ Skip: MCQ options (Option A/B/C/D)
              ├─ Skip: Noise (QP CODE, Date, Page N of N, hash strings)
              ├─ Skip: Instructions (Attempt any four, etc.)
              ├─ Detect question start: Q1a. / 2b) / a. patterns
              └─ Flush accumulated lines → question dict
                     { text, marks, section, raw_line }
```

### Regex Patterns (Key Ones)

```python
# Skip MCQ options
_MCQ_LINE = re.compile(r"^\s*(Option\s+[A-D]|[A-D]\))", re.IGNORECASE)

# Detect question start
_Q_START  = re.compile(r"^\s*(Q\s*\d+\s*[a-f]?\.?|\d+\s*[a-f]\s*[\.\)]|\d+\s*[\.\)])", re.IGNORECASE)

# Extract marks
_MARKS    = re.compile(r"\[(\d+)\]|(\d+)\s*M\b|\((\d+)\s*marks?\)", re.IGNORECASE)

# Noise filter
_NOISE    = re.compile(r"(Page\s+\d+\s+of\s+\d+|QP\s*CODE|DATE:|^\s*[A-F0-9]{32,}\s*$)", re.IGNORECASE)
```

---

## Topic Grouping (analyser.py)

### Phase 1 — Keyword Matching

```python
TOPIC_KEYWORDS = {
    "PEAS Framework": [r"\bpeas\b", "peas.*taxi", "actuators.*sensors", ...],
    "ANOVA":          [r"\banova\b", "f.?test", "one way anova", ...],
    # ... 30+ topics
}

def _match_topic(text: str) -> Optional[str]:
    for topic, patterns in TOPIC_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text.lower()):
                return topic
    return None
```

### Phase 2 — LLM Fallback (for unmatched questions)

When keyword matching fails, the server optionally calls an LLM API:

```python
# Priority order:  Anthropic → OpenAI → Google Gemini
# Only if API key is set in environment

prompt = (
    f"Topics: {topic_list}\n\n"
    "Classify each question. Respond ONLY with JSON: "
    "[{\"index\": 0, \"topic\": \"...\"}]"
)
```

This means:
- **Without any API key:** Pure keyword matching (works great for most questions)
- **With an API key:** Hybrid matching (even ambiguous questions get classified)

---

## PDF Generation (pdf_gen.py)

### ReportLab Document Structure

```python
SimpleDocTemplate(
    output_path,
    pagesize=A4,
    leftMargin=1.8*cm, rightMargin=1.8*cm,
    topMargin=1.5*cm,  bottomMargin=1.5*cm
)
# onFirstPage and onLaterPages both call _draw_header_footer()
# which draws the blue header bar and footer bar using canvas.rect()
```

### Key ReportLab Lessons Learned

| Issue                          | Solution                                              |
|-------------------------------|-------------------------------------------------------|
| Content bleeds under header   | Set `topMargin = 1.5*cm` (not 0) in SimpleDocTemplate |
| KeepTogether breaks pages     | Only wrap single-topic blocks, not entire sections    |
| Unicode superscripts render as ■ | Use `<super>` XML tags in Paragraph, not Unicode   |
| STDIO logs corrupt MCP stream | Use `logging` to `stderr`, never `print()`            |
| Header bar drawn on every page | Use both `onFirstPage` and `onLaterPages` callbacks  |

### Color Strategy

```
VERY_HIGH (#FFF2CC) = 5+ papers asked about this topic
HIGH      (#E2EFDA) = 3-4 papers
NORMAL_BG (#F9F9F9) = 1-2 papers
```

The same colors appear in both the summary table rows AND the topic header
badge, creating visual consistency.

---

## Database Schema

```sql
-- papers: one row per uploaded PDF
CREATE TABLE papers (
    paper_id   TEXT PRIMARY KEY,
    path       TEXT,      -- absolute path to PDF
    label      TEXT,      -- "May 2024"
    subject    TEXT,      -- "AI and DS – I"
    university TEXT,
    course     TEXT,
    year       TEXT,
    month      TEXT,
    added_at   TEXT DEFAULT (datetime('now'))
);

-- questions: extracted non-MCQ questions
CREATE TABLE questions (
    question_id TEXT PRIMARY KEY,
    paper_id    TEXT REFERENCES papers(paper_id) ON DELETE CASCADE,
    text        TEXT,     -- cleaned question text
    marks       INTEGER,  -- null if not parseable
    section     TEXT,     -- "Q2a", "Q3b"
    raw_line    TEXT      -- original first line
);

-- analyses: cached analysis results
CREATE TABLE analyses (
    analysis_id TEXT PRIMARY KEY,
    filter_key  TEXT,
    result_json TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
```

---

## Adding a New Subject / Topic

1. Open `src/exam_mcp/analyser.py`
2. Add entries to `TOPIC_KEYWORDS`:

```python
TOPIC_KEYWORDS = {
    # ... existing topics ...

    # ── Web Technology ────────────────────────────────────────────────────
    "HTTP and REST": [
        r"\bhttp\b", "rest.*api", "get.*post.*put.*delete",
        "status code", "request.*response",
    ],
    "HTML / CSS Basics": [
        r"\bhtml\b", r"\bcss\b", "dom", "selector",
        "html.*tags", "css.*properties",
    ],
}
```

No other changes needed. The server picks up the new keywords automatically.

---

## Extending for Multiple Universities

The `subject_filter` parameter in all tools lets you maintain papers from
multiple universities in the same database:

```json
// Upload
{"tool": "upload_paper", "arguments": {"subject": "DBMS - VIT University", ...}}
{"tool": "upload_paper", "arguments": {"subject": "DBMS - Mumbai University", ...}}

// Analyse separately
{"tool": "generate_pdf", "arguments": {"subject_filter": "VIT", ...}}
{"tool": "generate_pdf", "arguments": {"subject_filter": "Mumbai", ...}}
```

---

*Full setup instructions: see [SETUP.md](../SETUP.md)*
*Maintained by Yash Avsarmal · github.com/yashavsarmal30*
