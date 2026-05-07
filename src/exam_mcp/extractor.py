"""
exam_mcp/extractor.py
─────────────────────
Extracts non-MCQ questions from university exam paper PDFs.

Strategy:
  1. Try PyMuPDF (fitz) for native text extraction (fast, accurate for born-digital PDFs).
  2. Fall back to OCR via pdf2image + pytesseract for scanned / image-based PDFs.
  3. Parse extracted text to identify and filter non-MCQ questions.

Author : Yash Avsarmal  (github.com/yashavsarmal30)
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# ── Optional imports (graceful degradation) ──────────────────────────────────
try:
    import fitz  # PyMuPDF
    _PYMUPDF = True
except ImportError:
    _PYMUPDF = False
    log.warning("PyMuPDF not installed. OCR-only mode active.")

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    _OCR = True
except ImportError:
    _OCR = False
    log.warning("pytesseract / pdf2image not installed. OCR disabled.")

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def extract_questions_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract all non-MCQ questions from a PDF exam paper.

    Returns a list of dicts:
        {
            "text": str,          # full question text
            "marks": int | None,  # marks if parseable
            "section": str,       # "Q2a", "Q3b", etc.
            "raw_line": str       # original line for debugging
        }
    """
    text = _extract_text(pdf_path)
    if not text or len(text.strip()) < 100:
        log.warning("Low text yield from %s — attempting OCR", pdf_path)
        text = _ocr_pdf(pdf_path) if _OCR else ""

    if not text:
        log.error("Could not extract any text from %s", pdf_path)
        return []

    questions = _parse_questions(text)
    log.info("Extracted %d questions from %s", len(questions), Path(pdf_path).name)
    return questions


# ─────────────────────────────────────────────────────────────────────────────
# Text extraction
# ─────────────────────────────────────────────────────────────────────────────


def _extract_text(pdf_path: str) -> str:
    """Use PyMuPDF for fast native-text extraction."""
    if not _PYMUPDF:
        return ""
    try:
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()
        return "\n".join(pages)
    except Exception as exc:
        log.warning("PyMuPDF extraction failed: %s", exc)
        return ""


def _ocr_pdf(pdf_path: str, dpi: int = 300) -> str:
    """Convert PDF pages to images and OCR them with Tesseract."""
    if not _OCR:
        return ""
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        texts = []
        for i, img in enumerate(images):
            log.debug("OCR page %d/%d", i + 1, len(images))
            t = pytesseract.image_to_string(img, lang="eng")
            texts.append(t)
        return "\n".join(texts)
    except Exception as exc:
        log.error("OCR failed: %s", exc)
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Question parsing
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that indicate MCQ option lines — SKIP these
_MCQ_LINE = re.compile(
    r"^\s*(Option\s+[A-D]|[A-D]\)|[A-D]\s*[\.\-\:]\s)\s*",
    re.IGNORECASE,
)

# Patterns that mark the START of a numbered question / sub-question
_Q_START = re.compile(
    r"""
    ^\s*
    (
        Q\s*\d+\s*[a-f]?\.?   |   # Q1 / Q1a / Q1.
        \d+\s*[a-f]\s*[\.\)]\s |   # 1a. / 2b)
        \d+\s*[\.\)]\s+        |   # 1. / 2)
        [a-f]\s*[\.\)]\s+          # a. / b)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Marks indicator at end of line: [10] or 10M or (10 marks)
_MARKS = re.compile(r"\[(\d+)\]|(\d+)\s*M\b|\((\d+)\s*marks?\)", re.IGNORECASE)

# Lines that are clearly header/footer/date noise — skip
_NOISE = re.compile(
    r"(Page\s+\d+\s+of\s+\d+|QP\s*CODE|DATE:|Time:|Max\.\s*Marks|N\.B\.|"
    r"^\s*\*+\s*$|University\s+of\s+Mumbai|Examinations?\s+\w+\s+\d{4}|"
    r"^\s*[A-F0-9]{32,}\s*$)",  # hash strings on watermarked PDFs
    re.IGNORECASE,
)

# Lines that are compulsory/attempt instructions — skip
_INSTRUCTION = re.compile(
    r"(Attempt\s+any\s+\w+|Question\s+No\.?\s*1\s+is\s+compulsory|"
    r"All\s+questions\s+carry\s+equal\s+marks|Assume\s+suitable\s+data|"
    r"Figures\s+to\s+the\s+right|Use\s+of\s+Statistical\s+Tables)",
    re.IGNORECASE,
)


def _parse_questions(raw_text: str) -> list[dict]:
    """
    Split raw text into individual question records, skipping MCQ lines,
    noise, and instructions.
    """
    lines = raw_text.splitlines()
    questions: list[dict] = []
    current: list[str] = []
    current_section: str = ""
    current_marks: Optional[int] = None

    def flush():
        nonlocal current, current_section, current_marks
        text = " ".join(current).strip()
        text = re.sub(r"\s{2,}", " ", text)
        if len(text) > 20 and not _is_mcq_block(text):
            m = _extract_marks(text)
            questions.append({
                "text": _clean_question(text),
                "marks": m,
                "section": current_section,
                "raw_line": current[0] if current else "",
            })
        current = []
        current_section = ""
        current_marks = None

    for line in lines:
        line_s = line.strip()

        # Skip noise / blank / MCQ option / instruction lines
        if not line_s:
            continue
        if _NOISE.search(line_s):
            continue
        if _INSTRUCTION.search(line_s):
            continue
        if _MCQ_LINE.match(line_s):
            continue

        # Check if this line starts a new question
        m = _Q_START.match(line_s)
        if m:
            flush()
            current_section = m.group(0).strip().rstrip(".)")
            remainder = line_s[m.end():].strip()
            if remainder:
                current.append(remainder)
        else:
            # Continuation of current question
            if current:
                current.append(line_s)
            # else: orphan line before any question marker — skip

    flush()  # final question
    return questions


def _is_mcq_block(text: str) -> bool:
    """Return True if the text looks like it's part of an MCQ block."""
    option_count = len(re.findall(r"\bOption\s+[A-D]\b", text, re.IGNORECASE))
    return option_count >= 2


def _extract_marks(text: str) -> Optional[int]:
    m = _MARKS.search(text)
    if m:
        for g in m.groups():
            if g:
                return int(g)
    return None


def _clean_question(text: str) -> str:
    """Remove marks indicators and trailing noise from question text."""
    text = re.sub(r"\[(\d+)\]", "", text)
    text = re.sub(r"\b(\d+)\s*M\b", "", text)
    text = re.sub(r"\((\d+)\s*marks?\)", "", text, flags=re.IGNORECASE)
    return text.strip()
