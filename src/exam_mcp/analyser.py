"""
exam_mcp/analyser.py
────────────────────
Groups extracted questions by topic and ranks by frequency.

Uses keyword-based matching first, then falls back to an optional LLM API
call (any provider: OpenAI, Anthropic, Google Gemini) for fuzzy grouping of
ambiguous questions.

Author : Yash Avsarmal  (github.com/yashavsarmal30)
"""

from __future__ import annotations

import logging
import os
import re
from collections import defaultdict
from typing import Optional

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Topic taxonomy  (keyword → canonical topic name)
# Extend this dict to support new subjects.
# ─────────────────────────────────────────────────────────────────────────────

TOPIC_KEYWORDS: dict[str, list[str]] = {
    # ── AI & DS – I ──────────────────────────────────────────────────────────
    "ML Application Development": [
        "steps in developing", "developing.*ml application", "ml application",
        "machine learning application", "architecture.*ml", "ml.*architecture",
        "describe.*ml.*diagram", "building.*ml",
    ],
    "Covariance and Correlation": [
        "covariance", "correlation", "cov(", "corr(", "pearson",
        "coefficient of correlation", "scatter plot.*correlation",
    ],
    "PEAS Framework": [
        r"\bpeas\b", "performance.*environment.*actuator.*sensor",
        "actuators.*sensors", "peas.*taxi", "peas.*medical", "peas.*robot",
    ],
    "ANOVA": [
        r"\banova\b", "analysis of variance", "f.?test", "f.?statistic",
        "one way anova", "two way anova", "z.test.*t.test.*anova",
    ],
    "Hill Climbing": [
        "hill climbing", "hill.climb", "local minima", "local maxima",
        "steepest ascent", "plateau.*ridge",
    ],
    "Issues in Machine Learning": [
        "issues in ml", "issues in machine learning", "issues.*algorithm",
        "ml.*issues", "problems in ml",
    ],
    "Univariate EDA / Plots": [
        "univariate", "univariate.*plot", "histogram", "box.?plot",
        "stem.*leaf", "graphical.*eda", "eda.*graphical", "bar.?plot.*histogram",
    ],
    "Linear vs Logistic Regression": [
        "linear regression", "logistic regression", "logistics regression",
        "regression.*compare", "sigmoid function", "r.squared",
    ],
    "Data Science Lifecycle": [
        "data science.*project", "data analytics.*lifecycle", "data.*lifecycle",
        "stages.*data science", "data science.*stages",
    ],
    "A* Algorithm": [
        r"a\*\s*algorithm", r"a\*\s*search", "a.star", "admissible heuristic",
        "optimal path.*search",
    ],
    "Alpha-Beta Pruning / Min-Max": [
        "alpha.beta", "min.max", "minimax", "game tree", "alpha beta pruning",
    ],
    "SVM": [
        r"\bsvm\b", "support vector machine", "hyperplane.*svm",
        "kernel.*svm", "margin.*svm",
    ],
    "Resolution / Logical Inference": [
        "resolution", "resolve", "colonel west", "marcus.*pompeian",
        "cnf.*resolution", "clause.*resolution",
    ],
    "Overfitting and Underfitting": [
        "overfitting", "underfitting", "over.fit", "under.fit",
        "bias.*variance", "regularization",
    ],
    "Forward and Backward Chaining": [
        "forward chaining", "backward chaining", "forward.*backward",
        "data.driven", "goal.driven.*chaining",
    ],
    "Skolemization and Unification": [
        "skolem", "unification", "unify", "skolem constant", "skolem function",
        "cnf.*conversion", "predicate.*cnf",
    ],
    "Data Scientist Roles Comparison": [
        "data scientist", "big data professional", "data analyst.*compare",
        "data science.*business analytics.*big data",
    ],
    "Measures of Central Tendency": [
        "central tendenc", "mean.*median.*mode", "skewness", "kurtosis",
        "measure of spread", "variance.*standard deviation",
    ],
    "Types of Machine Learning": [
        "types of machine learning", "supervised.*unsupervised.*reinforcement",
        "semi.supervised", "types.*ml algorithm",
    ],
    "Rational Agent": [
        "rational agent", "structure.*agent", "model.based.*reflex",
        "simple reflex agent",
    ],
    "EDA Categories": [
        r"\beda\b", "exploratory data analysis", "categorization.*eda",
        "types of eda", "steps.*eda",
    ],
    "Types of Environments": [
        "types of environment", "fully observable", "partially observable",
        "deterministic.*stochastic", "vacuum world",
    ],
    "Water Jug Problem": [
        "water jug", "jug.*litre", "jug.*liter", "measure.*jug",
    ],
    "Planning Techniques": [
        "planning technique", "partial order planning", "hierarchical.*planning",
        "conditional planning", "htn",
    ],
    "Heuristic Search": [
        "heuristic function", "heuristic search", "informed.*uninformed",
        "where.*heuristic",
    ],
    "Uninformed Search Strategies": [
        "uninformed search", "bfs.*dfs", "breadth first", "depth first",
        "uniform cost search", "depth limited search",
    ],
    "Goal-Based Agent": [
        "goal.based agent", "goal based agent", "goal.*agent.*diagram",
        "utility.*agent", "utility based agent",
    ],
    "Data Visualization": [
        "data visualization", "data visualisation", "importance.*visualization",
        "visualization.*analytics",
    ],
    "Hypothesis Testing": [
        "hypothesis testing", "null hypothesis", "alternate hypothesis",
        "type i.*error", "type ii.*error", "p.value",
    ],
    "Unsupervised ML (Clustering)": [
        "k.means", "hierarchical cluster", "unsupervised.*cluster",
        "clustering algorithm",
    ],
    "Uniform Cost vs Best First Search": [
        "uniform cost search", "best first search", "ucs.*bfs", "informed.*search.*compare",
    ],
    "Knowledge Representation (FOL)": [
        "first order logic", "predicate logic", "knowledge representation",
        "propositional logic", "knowledge base",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Variant question templates  (per topic → auto-generated variant stubs)
# ─────────────────────────────────────────────────────────────────────────────

VARIANT_TEMPLATES: list[str] = [
    "Write a short note on: {topic}.",
    "Differentiate between the key concepts in {topic} with suitable examples.",
    "Compare the main approaches in {topic}.",
    "Explain {topic} with a neat diagram/example.",
    "What are the issues/challenges related to {topic}? How can they be resolved?",
    "Give a numerical/application-based example of {topic}.",
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def group_and_rank_topics(questions: list[dict]) -> list[dict]:
    """
    Group questions by topic and rank by frequency (number of distinct papers).

    Each question dict must have at least:
        { "text": str, "paper_label": str, "section": str }

    Returns a list of topic dicts sorted descending by count:
        {
            "rank": int,
            "count": int,           # number of distinct papers
            "title": str,           # canonical topic name
            "papers": str,          # "May 2022 · Dec 2023 · ..."
            "actual": list[str],    # question texts from papers
            "variants": list[str],  # auto-generated variant questions
        }
    """
    # topic_name → { paper_label → [question_text] }
    topic_map: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    unmatched: list[dict] = []

    for q in questions:
        topic = _match_topic(q["text"])
        if topic:
            topic_map[topic][q["paper_label"]].append(q["text"])
        else:
            unmatched.append(q)

    if unmatched:
        log.info("%d questions did not match any keyword topic", len(unmatched))
        # Optional: try LLM-based grouping for unmatched questions
        _llm_group_unmatched(unmatched, topic_map)

    results: list[dict] = []
    for rank, (title, papers_dict) in enumerate(
        sorted(topic_map.items(), key=lambda x: len(x[1]), reverse=True), start=1
    ):
        all_qs = []
        for qs in papers_dict.values():
            all_qs.extend(qs)
        # Deduplicate actual questions
        seen: set[str] = set()
        deduped: list[str] = []
        for q in all_qs:
            key = re.sub(r"\s+", " ", q.lower().strip())[:120]
            if key not in seen:
                seen.add(key)
                deduped.append(q)

        papers_label = " · ".join(sorted(papers_dict.keys()))

        results.append({
            "rank": rank,
            "count": len(papers_dict),
            "title": title,
            "papers": papers_label,
            "actual": deduped,
            "variants": _generate_variants(title, deduped),
        })

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _match_topic(text: str) -> Optional[str]:
    """Return the canonical topic name if the text matches any keyword pattern."""
    text_lower = text.lower()
    for topic, patterns in TOPIC_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return topic
    return None


def _generate_variants(topic: str, actual_qs: list[str]) -> list[str]:
    """Generate variant questions for a topic."""
    # Try to derive a clean short name for templates
    short = topic.split("/")[0].strip()
    variants = []
    for tmpl in VARIANT_TEMPLATES:
        variants.append(tmpl.format(topic=short))
    # Remove variants that closely duplicate actual questions
    actual_lower = {re.sub(r"\s+", " ", q.lower().strip()) for q in actual_qs}
    filtered = []
    for v in variants:
        key = re.sub(r"\s+", " ", v.lower().strip())
        if not any(key[:60] in a for a in actual_lower):
            filtered.append(v)
    return filtered[:6]  # max 6 variants


def _llm_group_unmatched(
    unmatched: list[dict],
    topic_map: dict[str, dict[str, list[str]]],
) -> None:
    """
    Optionally use an LLM API to classify unmatched questions.

    Tries providers in order: Anthropic → OpenAI → Google Gemini.
    Silently skips if no API key is found.
    """
    api_key_anthropic = os.getenv("ANTHROPIC_API_KEY")
    api_key_openai    = os.getenv("OPENAI_API_KEY")
    api_key_gemini    = os.getenv("GOOGLE_API_KEY")

    if not any([api_key_anthropic, api_key_openai, api_key_gemini]):
        log.info("No LLM API key found — skipping LLM-based grouping of %d unmatched questions", len(unmatched))
        return

    topic_list = list(TOPIC_KEYWORDS.keys())
    prompt = (
        "You are a university exam question classifier.\n"
        "Given a list of exam questions and a list of topic names, assign each "
        "question to the best matching topic from the list, or respond 'OTHER' "
        "if none fits.\n\n"
        f"Topics: {topic_list}\n\n"
        "Questions (JSON):\n"
        + _json_questions(unmatched)
        + "\n\nRespond ONLY with a JSON array: [{\"index\":0,\"topic\":\"...\"},...]\n"
        "Index matches the order of questions above."
    )

    response_text = ""

    if api_key_anthropic:
        response_text = _call_anthropic(prompt, api_key_anthropic)
    elif api_key_openai:
        response_text = _call_openai(prompt, api_key_openai)
    elif api_key_gemini:
        response_text = _call_gemini(prompt, api_key_gemini)

    if not response_text:
        return

    try:
        import json
        assignments = json.loads(response_text)
        for a in assignments:
            idx   = a.get("index", -1)
            topic = a.get("topic", "OTHER")
            if 0 <= idx < len(unmatched) and topic != "OTHER":
                q = unmatched[idx]
                topic_map[topic][q["paper_label"]].append(q["text"])
    except Exception as exc:
        log.warning("Failed to parse LLM grouping response: %s", exc)


def _json_questions(questions: list[dict]) -> str:
    import json
    return json.dumps([{"index": i, "text": q["text"][:200]} for i, q in enumerate(questions)])


def _call_anthropic(prompt: str, api_key: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as exc:
        log.warning("Anthropic LLM call failed: %s", exc)
        return ""


def _call_openai(prompt: str, api_key: str) -> str:
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        log.warning("OpenAI LLM call failed: %s", exc)
        return ""


def _call_gemini(prompt: str, api_key: str) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model  = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(prompt)
        return result.text
    except Exception as exc:
        log.warning("Gemini LLM call failed: %s", exc)
        return ""
