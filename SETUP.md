# Setup Guide — Exam Question Analyser MCP Server

**Author:** Yash Avsarmal · [github.com/yashavsarmal30](https://github.com/yashavsarmal30)

---

## What Is This?

An **MCP (Model Context Protocol) server** that lets any compatible AI assistant
(Claude, GPT-4, Gemini, etc.) analyse university exam question papers, group
questions by topic, rank them by frequency, and generate a professional
**ranked PDF question bank** — all from your local machine.

You drop your exam PDFs into a folder, point the server at them, and the AI
does the rest.

---

## Prerequisites

| Requirement          | Minimum Version | Notes                                          |
|----------------------|-----------------|------------------------------------------------|
| Python               | 3.10            | 3.11 or 3.12 recommended                       |
| uv (recommended)     | 0.4+            | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| pip (alternative)    | 23+             | Works if you don't use uv                      |
| Tesseract OCR        | 5.0             | Only needed for scanned PDFs                   |
| Poppler              | any             | Needed by pdf2image for OCR                    |

### Install Tesseract OCR (for scanned PDFs only)

```bash
# macOS
brew install tesseract poppler

# Ubuntu / Debian
sudo apt-get install tesseract-ocr poppler-utils

# Windows
# Download installer from https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH
```

---

## Installation

### Option A — Using uv (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/yashavsarmal30/dontpay-musa.git
cd dontpay-musa

# 2. Create virtualenv and install
uv venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uv pip install -e ".[llm,dev]"
```

### Option B — Using pip

```bash
git clone https://github.com/yashavsarmal30/dontpay-musa.git
cd dontpay-musa
python -m venv .venv
source .venv/bin/activate
pip install -e ".[llm,dev]"
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in any keys you have:

```bash
cp .env.example .env
```

```ini
# .env
# ── Database ──────────────────────────────────────────────────────────────────
# Where to store the SQLite database (default: ~/.exam_mcp/papers.db)
EXAM_DB_PATH=/path/to/your/papers.db

# ── Transport ─────────────────────────────────────────────────────────────────
# "stdio"            — for Claude Desktop / local MCP clients
# "streamable-http"  — for HTTP-based clients
MCP_TRANSPORT=stdio

# ── LLM API Keys (all optional — used for fuzzy topic grouping of edge cases) ─
# At least one is recommended for best grouping accuracy.
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

---

## Running the Server

### STDIO mode (Claude Desktop, local clients)

```bash
python -m exam_mcp.server
# or
exam-mcp
```

### HTTP mode (remote clients, Gemini, GPT-4 via HTTP)

```bash
MCP_TRANSPORT=streamable-http python -m exam_mcp.server
# Server listens on http://localhost:8000/mcp by default
```

---

## Connecting to Claude Desktop

1. Open Claude Desktop → Settings → Developer → Edit Config.
2. Add the server to `mcpServers`:

```json
{
  "mcpServers": {
    "dontpay-musa": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/dontpay-musa",
        "run",
        "python", "-m", "exam_mcp.server"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "EXAM_DB_PATH": "/Users/yash/.exam_mcp/papers.db"
      }
    }
  }
}
```

3. Restart Claude Desktop.
4. You should see the Exam Question Analyser tools in the tool picker.

---

## Connecting to Other AI Clients

### GPT-4 / OpenAI API (HTTP mode)

```python
# Start server in HTTP mode first:
# MCP_TRANSPORT=streamable-http python -m exam_mcp.server

import openai, json, httpx

client = openai.OpenAI(api_key="sk-...")

# Call a tool manually via HTTP
resp = httpx.post(
    "http://localhost:8000/mcp",
    json={
        "method": "tools/call",
        "params": {
            "name": "upload_paper",
            "arguments": {
                "pdf_path": "/path/to/paper.pdf",
                "label": "May 2024",
                "subject": "AI and DS - I"
            }
        }
    }
)
print(resp.json())
```

### Google Gemini

```python
import google.generativeai as genai
import httpx, json

genai.configure(api_key="AIza...")
model = genai.GenerativeModel("gemini-1.5-flash")

# Get analysis JSON from the MCP server
resp = httpx.get("http://localhost:8000/mcp",
    params={"method": "tools/call", "params": json.dumps({
        "name": "get_analysis", "arguments": {}
    })})
analysis_json = resp.text

# Feed to Gemini
result = model.generate_content(
    f"Here is the exam question analysis:\n{analysis_json}\n\n"
    "Summarise the top 5 most important topics a student should study."
)
print(result.text)
```

---

## Step-by-Step Usage

### 1. Upload exam papers

In Claude (or any MCP client), say:

> "Upload the exam paper at `/home/yash/papers/may_2024.pdf` with label 'May 2024' for subject 'AI and DS – I', University of Mumbai, BE IT SEM VI."

Or call the tool directly:

```json
{
  "tool": "upload_paper",
  "arguments": {
    "pdf_path": "/home/yash/papers/may_2024.pdf",
    "label": "May 2024",
    "subject": "AI and DS – I",
    "university": "University of Mumbai",
    "course": "BE IT SEM VI C Scheme",
    "year": "2024",
    "month": "May"
  }
}
```

Repeat for all papers.

### 2. Check stored papers

```json
{ "tool": "list_papers", "arguments": {} }
```

### 3. Analyse and generate PDF

```json
{
  "tool": "generate_pdf",
  "arguments": {
    "output_path": "/home/yash/question_bank.pdf",
    "subject_name": "AI and DS – I",
    "course": "BE IT SEM VI C Scheme",
    "university": "University of Mumbai"
  }
}
```

The PDF will be created at the specified path.

---

## Project Structure

```
dontpay-musa/
├── src/
│   └── exam_mcp/
│       ├── __init__.py        # package metadata
│       ├── server.py          # FastMCP server — all tools defined here
│       ├── extractor.py       # PDF text extraction + OCR + question parser
│       ├── analyser.py        # topic grouping, ranking, variant generation
│       ├── pdf_gen.py         # ReportLab PDF builder (SKILL.md design)
│       └── database.py        # SQLite persistence layer
├── skills/
│   └── SKILL.md               # Skill specification (importable into Claude)
├── tests/
│   ├── test_extractor.py
│   ├── test_analyser.py
│   └── test_pdf_gen.py
├── docs/
│   └── MCP_SERVER_GUIDE.md    # Full MCP implementation guide
├── examples/
│   └── run_example.py         # End-to-end demo without MCP client
├── .env.example
├── pyproject.toml
├── README.md
└── SETUP.md                   # ← You are here
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Troubleshooting

| Problem                                  | Fix                                                                     |
|------------------------------------------|-------------------------------------------------------------------------|
| `ModuleNotFoundError: fitz`              | `pip install pymupdf`                                                   |
| `TesseractNotFoundError`                 | Install Tesseract and ensure it's on PATH                               |
| Server not appearing in Claude Desktop   | Use absolute paths in claude_desktop_config.json                        |
| `No papers found` error                  | Run `upload_paper` tool first                                           |
| Poor question extraction from scanned PDF| Ensure dpi=300+ in OCR; check Tesseract language pack (`tesseract-ocr-eng`) |
| PDF has only 1 page                      | ReportLab KeepTogether issue — check for very long question blocks       |

---

*Maintained by Yash Avsarmal · github.com/yashavsarmal30*
