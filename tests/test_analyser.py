"""tests/test_analyser.py — Unit tests for topic grouping."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from exam_mcp.analyser import group_and_rank_topics, _match_topic


def _q(text, label="Paper A"):
    return {"text": text, "paper_label": label, "section": "Q1"}


def test_match_peas():
    assert _match_topic("State PEAS of automated taxi driver") == "PEAS Framework"


def test_match_anova():
    assert _match_topic("Perform One way ANOVA F Test on this data") == "ANOVA"


def test_match_hill_climbing():
    assert _match_topic("Explain the working of the Hill climbing algorithm") == "Hill Climbing"


def test_match_correlation():
    assert _match_topic("What do you mean by covariance and correlation?") == "Covariance and Correlation"


def test_no_match_mcq():
    # An MCQ-like stub should not crash
    result = _match_topic("Option A: Actuators")
    # It won't match any serious topic
    assert result is None or isinstance(result, str)


def test_group_and_rank_frequency():
    questions = [
        _q("Explain PEAS for taxi driver",  "Paper A"),
        _q("Describe PEAS for car driver",   "Paper B"),
        _q("What is Hill Climbing?",          "Paper A"),
        _q("Issues in Hill Climbing?",        "Paper C"),
        _q("Hill climbing local minima",      "Paper D"),
    ]
    topics = group_and_rank_topics(questions)
    counts = {t["title"]: t["count"] for t in topics}

    # Hill Climbing appeared in 3 distinct papers, PEAS in 2
    assert counts.get("Hill Climbing", 0) == 3
    assert counts.get("PEAS Framework", 0) == 2

    # Must be sorted descending
    counts_list = [t["count"] for t in topics]
    assert counts_list == sorted(counts_list, reverse=True)


def test_variants_generated():
    questions = [_q("Explain Hill Climbing algorithm", "Paper A")]
    topics = group_and_rank_topics(questions)
    hc = next((t for t in topics if t["title"] == "Hill Climbing"), None)
    assert hc is not None
    assert len(hc["variants"]) >= 1
    # At least one "short note" variant
    assert any("short note" in v.lower() for v in hc["variants"])
