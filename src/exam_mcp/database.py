"""
exam_mcp/database.py
────────────────────
SQLite persistence layer for the Exam Question Analyser MCP server.

Tables:
  papers    – one row per uploaded exam paper
  questions – extracted questions linked to a paper
  analyses  – cached analysis results (JSON)

Author : Yash Avsarmal  (github.com/yashavsarmal30)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Optional

log = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    paper_id   TEXT PRIMARY KEY,
    path       TEXT NOT NULL,
    label      TEXT NOT NULL,
    subject    TEXT,
    university TEXT,
    course     TEXT,
    year       TEXT,
    month      TEXT,
    added_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    paper_id    TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    marks       INTEGER,
    section     TEXT,
    raw_line    TEXT
);

CREATE TABLE IF NOT EXISTS analyses (
    analysis_id TEXT PRIMARY KEY,
    filter_key  TEXT,
    result_json TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now'))
);
"""


class PaperDatabase:
    def __init__(self, db_path: str):
        self._path = db_path
        self._init_db()

    # ── Context manager for connections ──────────────────────────────────────

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self._path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _init_db(self):
        with self._conn() as con:
            con.executescript(_SCHEMA)

    # ── Papers ────────────────────────────────────────────────────────────────

    def add_paper(
        self,
        path: str,
        label: str,
        subject: str,
        university: str,
        course: str,
        year: str,
        month: str,
        questions: list[dict],
    ) -> str:
        paper_id = str(uuid.uuid4())
        with self._conn() as con:
            con.execute(
                """INSERT INTO papers (paper_id, path, label, subject, university, course, year, month)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (paper_id, path, label, subject, university, course, year, month),
            )
            for q in questions:
                con.execute(
                    """INSERT INTO questions (question_id, paper_id, text, marks, section, raw_line)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        str(uuid.uuid4()),
                        paper_id,
                        q.get("text", ""),
                        q.get("marks"),
                        q.get("section", ""),
                        q.get("raw_line", ""),
                    ),
                )
        return paper_id

    def list_papers(self, subject_filter: Optional[str] = None) -> list[dict]:
        with self._conn() as con:
            if subject_filter:
                rows = con.execute(
                    """SELECT p.*, COUNT(q.question_id) as question_count
                       FROM papers p
                       LEFT JOIN questions q ON p.paper_id = q.paper_id
                       WHERE lower(p.subject) LIKE lower(?)
                       GROUP BY p.paper_id
                       ORDER BY p.year, p.month""",
                    (f"%{subject_filter}%",),
                ).fetchall()
            else:
                rows = con.execute(
                    """SELECT p.*, COUNT(q.question_id) as question_count
                       FROM papers p
                       LEFT JOIN questions q ON p.paper_id = q.paper_id
                       GROUP BY p.paper_id
                       ORDER BY p.year, p.month""",
                ).fetchall()
        return [dict(r) for r in rows]

    def get_questions(self, paper_id: str) -> list[dict]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT * FROM questions WHERE paper_id = ?", (paper_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def clear_papers(self, subject_filter: Optional[str] = None) -> int:
        with self._conn() as con:
            if subject_filter:
                rows = con.execute(
                    "SELECT paper_id FROM papers WHERE lower(subject) LIKE lower(?)",
                    (f"%{subject_filter}%",),
                ).fetchall()
                ids = [r["paper_id"] for r in rows]
                if ids:
                    placeholders = ",".join("?" * len(ids))
                    con.execute(f"DELETE FROM papers WHERE paper_id IN ({placeholders})", ids)
                return len(ids)
            else:
                count = con.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
                con.execute("DELETE FROM papers")
                return count

    # ── Analyses ──────────────────────────────────────────────────────────────

    def save_analysis(self, filter_key: str, topics: list[dict]):
        with self._conn() as con:
            con.execute(
                """INSERT INTO analyses (analysis_id, filter_key, result_json)
                   VALUES (?,?,?)""",
                (str(uuid.uuid4()), filter_key, json.dumps(topics)),
            )

    def get_latest_analysis(self, filter_key: str = "all") -> Optional[list[dict]]:
        with self._conn() as con:
            row = con.execute(
                """SELECT result_json FROM analyses
                   WHERE filter_key = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (filter_key,),
            ).fetchone()
        if row:
            return json.loads(row["result_json"])
        return None
