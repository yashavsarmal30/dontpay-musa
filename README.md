# 📚 Exam Question Analyser — MCP Server 

(Dont Pay Musa For Question Banks Pay Me Instead)😉 UPI Id : yashavsarmal30@okaxis

> Analyse university exam papers · Group by topic · Rank by frequency · Generate professional PDF question banks
**Author:** Yash Avsarmal · [github.com/yashavsarmal30](https://github.com/yashavsarmal30)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://www.python.org)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Works with Claude](https://img.shields.io/badge/Works%20with-Claude-orange?style=flat-square)](https://claude.ai)
[![Works with GPT-4](https://img.shields.io/badge/Works%20with-GPT--4-74aa9c?style=flat-square)](https://openai.com)
[![Works with Gemini](https://img.shields.io/badge/Works%20with-Gemini-4285F4?style=flat-square)](https://ai.google.dev)

---

## What It Does

```
PDF papers  →  Extract questions  →  Group by topic  →  Rank by frequency  →  PDF Question Bank
```

1. **Upload** any number of university exam papers (born-digital or scanned PDFs).
2. **Extract** all non-MCQ questions automatically (OCR for scanned papers).
3. **Group** questions that share the same topic, even if worded differently.
4. **Rank** topic groups by frequency across all papers.
5. **Generate** a beautifully formatted PDF with:
   - Color-coded summary table (yellow = very high priority, green = high priority)
   - Full question bank per topic: exact past-paper questions + AI-generated variant questions
     (Write a short note on / Differentiate / Compare / Numerical forms)

---

## Demo Output

The generated PDF has two sections:

| Section | Content |
|---------|---------|
| **Page 1** | Cover page + color-coded summary table ranked by frequency |
| **Pages 2+** | Full question bank — exact questions from papers + related variants |

---

## Quick Start

```bash
git clone https://github.com/yashavsarmal30/dontpay-musa.git
cd dontpay-musa
uv venv && source .venv/bin/activate
uv pip install -e ".[llm]"
```

See **[SETUP.md](SETUP.md)** for full installation, Claude Desktop config, and usage guide.

---

## Available MCP Tools

| Tool             | Description                                                    |
|------------------|----------------------------------------------------------------|
| `upload_paper`   | Register a local PDF exam paper and extract its questions       |
| `list_papers`    | List all stored papers                                         |
| `analyse_papers` | Group questions by topic and rank by frequency                 |
| `generate_pdf`   | Build the ranked question-bank PDF                             |
| `get_analysis`   | Return analysis as JSON (for external LLMs)                    |
| `clear_papers`   | Remove papers from the database                                |

---

## AI Compatibility

| AI Assistant     | Transport   | How                                           |
|------------------|-------------|-----------------------------------------------|
| **Claude**       | STDIO       | Add to `claude_desktop_config.json`            |
| **GPT-4**        | HTTP        | Run in HTTP mode, call via OpenAI client       |
| **Gemini**       | HTTP        | Run in HTTP mode, feed JSON via Gemini API     |
| **Any MCP client** | STDIO/HTTP | Standard MCP protocol                        |

---

## Project Structure

```
dontpay-musa/
├── src/exam_mcp/
│   ├── server.py      # FastMCP server
│   ├── extractor.py   # PDF extraction + OCR
│   ├── analyser.py    # Topic grouping + ranking
│   ├── pdf_gen.py     # ReportLab PDF builder
│   └── database.py    # SQLite persistence
├── skills/SKILL.md    # Importable skill specification
├── docs/              # Extended documentation
├── tests/             # Test suite
├── SETUP.md           # Full setup guide
└── pyproject.toml
```

---

## License

MIT — see [LICENSE](LICENSE).

---

![Visitors](https://visitor-badge.laobi.icu/badge?page_id=yashavsarmal30.dontpay-musa)
![Stars](https://img.shields.io/github/stars/yashavsarmal30/dontpay-musa)
![Forks](https://img.shields.io/github/forks/yashavsarmal30/dontpay-musa)
![Issues](https://img.shields.io/github/issues/yashavsarmal30/dontpay-musa)

*Author : Yash Avsarmal*
