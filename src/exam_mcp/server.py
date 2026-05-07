"""
exam_mcp/server.py
──────────────────
FastMCP server for the Exam Question Analyser.

Tools exposed:
  • upload_paper        – register a local PDF path into the database
  • analyse_papers      – extract topics + frequencies from all stored papers
  • generate_pdf        – produce the ranked question-bank PDF
  • list_papers         – list all papers currently stored
  • clear_papers        – remove all papers from the database
  • get_analysis        – return the last analysis as JSON (for external LLMs)

Author : Yash Avsarmal  (github.com/yashavsarmal30)
License: MIT
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ── Local imports ─────────────────────────────────────────────────────────────
from exam_mcp.extractor import extract_questions_from_pdf
from exam_mcp.analyser  import group_and_rank_topics
from exam_mcp.pdf_gen   import build_question_bank_pdf
from exam_mcp.database  import PaperDatabase

# ── Logging (stderr so STDIO transport stays clean) ──────────────────────────
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("exam_mcp.server")

# ── FastMCP app ───────────────────────────────────────────────────────────────
mcp = FastMCP(
    "Exam Question Analyser",
    version="1.0.0",
    description=(
        "Analyse university exam papers, group questions by topic, rank by "
        "frequency, and generate a professional PDF question bank. "
        "Compatible with Claude, GPT-4, Gemini, and any MCP client."
    ),
)

# Singleton database (SQLite, stored beside the server)
_DB_PATH = Path(os.getenv("EXAM_DB_PATH", Path.home() / ".exam_mcp" / "papers.db"))
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
db = PaperDatabase(str(_DB_PATH))

# ─────────────────────────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────────────────────────


@mcp.tool()
def upload_paper(
    pdf_path: str,
    label: str,
    subject: str = "Unknown Subject",
    university: str = "Unknown University",
    course: str = "",
    year: str = "",
    month: str = "",
) -> dict:
    """
    Register a local PDF exam paper into the database and extract its questions.

    Args:
        pdf_path:   Absolute path to the PDF file on the local machine.
        label:      Human-readable label, e.g. "May 2024".
        subject:    Subject name, e.g. "AI and DS – I".
        university: University name.
        course:     Degree/branch/semester string, e.g. "BE IT SEM VI C Scheme".
        year:       4-digit year string, e.g. "2024".
        month:      "May" or "December".

    Returns:
        dict with keys: paper_id, label, questions_found, status
    """
    path = Path(pdf_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {pdf_path}"}
    if path.suffix.lower() != ".pdf":
        return {"status": "error", "message": "Only PDF files are supported."}

    log.info("Extracting questions from %s", path.name)
    questions = extract_questions_from_pdf(str(path))

    paper_id = db.add_paper(
        path=str(path),
        label=label,
        subject=subject,
        university=university,
        course=course,
        year=year,
        month=month,
        questions=questions,
    )

    log.info("Stored %d questions for paper %s (id=%s)", len(questions), label, paper_id)
    return {
        "status": "ok",
        "paper_id": paper_id,
        "label": label,
        "questions_found": len(questions),
    }


@mcp.tool()
def list_papers() -> dict:
    """
    List all exam papers currently stored in the database.

    Returns:
        dict with key 'papers': list of {paper_id, label, subject, year, month, question_count}
    """
    papers = db.list_papers()
    return {"papers": papers, "total": len(papers)}


@mcp.tool()
def analyse_papers(subject_filter: Optional[str] = None) -> dict:
    """
    Analyse all stored papers (optionally filtered by subject), group questions
    by topic, and rank by frequency.

    Args:
        subject_filter: If provided, only analyse papers whose subject matches
                        this string (case-insensitive substring match).

    Returns:
        dict with keys: topics (ranked list), total_papers, total_questions
    """
    papers = db.list_papers(subject_filter=subject_filter)
    if not papers:
        return {"status": "error", "message": "No papers found. Upload papers first using upload_paper."}

    all_questions = []
    paper_labels  = []
    for p in papers:
        qs = db.get_questions(p["paper_id"])
        for q in qs:
            q["paper_label"] = p["label"]
        all_questions.extend(qs)
        paper_labels.append(p["label"])

    log.info("Analysing %d questions from %d papers", len(all_questions), len(papers))
    topics = group_and_rank_topics(all_questions)

    # Cache analysis in DB
    db.save_analysis(subject_filter or "all", topics)

    return {
        "status": "ok",
        "total_papers": len(papers),
        "total_questions": len(all_questions),
        "paper_labels": paper_labels,
        "topics": topics,
    }


@mcp.tool()
def generate_pdf(
    output_path: str,
    subject_name: str,
    course: str = "",
    university: str = "",
    subject_filter: Optional[str] = None,
) -> dict:
    """
    Generate the ranked question-bank PDF from the last (or current) analysis.

    Args:
        output_path:    Where to write the PDF, e.g. "/home/user/question_bank.pdf".
        subject_name:   Subject name for the cover page.
        course:         Degree/branch/semester for the cover page.
        university:     University name for the cover page.
        subject_filter: If provided, filter papers by subject before analysis.

    Returns:
        dict with keys: status, output_path, page_count, topic_count
    """
    # Run or re-use analysis
    analysis = analyse_papers(subject_filter=subject_filter)
    if analysis.get("status") == "error":
        return analysis

    subject_info = {
        "name": subject_name,
        "course": course,
        "university": university,
        "year_range": _infer_year_range(analysis["paper_labels"]),
        "paper_count": analysis["total_papers"],
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    log.info("Generating PDF → %s", out)
    page_count = build_question_bank_pdf(
        output_path=str(out),
        subject_info=subject_info,
        topics=analysis["topics"],
    )

    return {
        "status": "ok",
        "output_path": str(out),
        "page_count": page_count,
        "topic_count": len(analysis["topics"]),
    }


@mcp.tool()
def get_analysis(subject_filter: Optional[str] = None) -> str:
    """
    Return the full analysis as a JSON string (useful for passing to external
    LLMs like Gemini or GPT-4 that do not natively call Python tools).

    Args:
        subject_filter: Optional subject filter (case-insensitive).

    Returns:
        JSON string with the ranked topic list.
    """
    result = analyse_papers(subject_filter=subject_filter)
    return json.dumps(result, indent=2)


@mcp.tool()
def clear_papers(subject_filter: Optional[str] = None) -> dict:
    """
    Remove papers from the database.

    Args:
        subject_filter: If provided, only remove papers whose subject matches.
                        If omitted, ALL papers are removed.

    Returns:
        dict with keys: status, removed_count
    """
    count = db.clear_papers(subject_filter=subject_filter)
    return {"status": "ok", "removed_count": count}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _infer_year_range(labels: list[str]) -> str:
    """Extract year range from labels like ['May 2022', 'Dec 2024']."""
    years = []
    for lbl in labels:
        parts = lbl.split()
        for p in parts:
            if p.isdigit() and len(p) == 4:
                years.append(int(p))
    if not years:
        return "Year Unknown"
    return f"{min(years)}–{max(years)}" if min(years) != max(years) else str(min(years))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    log.info("Starting Exam Question Analyser MCP server (transport=%s)", transport)
    mcp.run(transport=transport)
