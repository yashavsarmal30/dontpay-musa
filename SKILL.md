---
name: university-question-bank-generator
description: >
  Use this skill whenever asked to analyze university exam papers from ANY subject
  and generate a professional question-bank PDF organized by topic, frequency,
  unit/module/chapter, and importance level.

  Supports all engineering, diploma, degree, commerce, science, management,
  IT, CS, electronics, mechanical, civil, AI/ML, mathematics, networking,
  operating systems, web technology, database, and theory subjects.

  Triggers:
  - "analyze question papers"
  - "make question bank"
  - "group questions by topic"
  - "which questions repeat"
  - "most asked questions"
  - "generate exam preparation PDF"
  - "important questions analysis"
  - "subject-wise question bank"
  - "module-wise question analysis"

author: Yash Avsarmal
version: 2.0.0
license: MIT
---

# Universal University Question-Bank PDF Generation Skill

## What This Skill Does

Given one or more university exam papers (PDFs/images/text files), this skill:

1. Extracts all meaningful questions from every paper
2. Removes MCQs, instructions, duplicate headers, and formatting noise
3. Detects:
   - Topic
   - Unit / Module / Chapter
   - Question Type
   - Marks Weightage
4. Groups similar questions together
5. Counts frequency across all papers
6. Ranks topics by exam importance
7. Generates a professional exam-oriented PDF question bank

---

# Core Features

## Supported Features

### Question Extraction
- Extracts descriptive questions
- Extracts numericals
- Extracts derivations
- Extracts diagrams/draw questions
- Extracts definitions
- Extracts comparison questions

### Question Classification
Detects:
- Explain
- Draw & Explain
- Compare
- Differentiate
- State
- List
- Derive
- Numerical
- Short Note
- Long Answer
- Case Study
- Algorithm
- Program
- Design Problem

### Topic Clustering
Groups:
- Similar wording
- Same concept
- Repeated topics
- Alternate phrasing
- Previous year repetitions

### Frequency Analysis
Ranks:
- Most repeated
- High frequency
- Moderate frequency
- Rare but important

---

# Recommended Tech Stack

| Layer | Tool |
|---|---|
| PDF extraction | `pdfplumber` + `pypdf` |
| OCR (scanned papers) | `pytesseract` |
| NLP grouping | `rapidfuzz` + embeddings |
| Topic classification | keyword + semantic similarity |
| PDF generation | `reportlab` |
| AI fallback | LLM semantic grouping |

---

# Frequency Badge Logic

```python
def get_badge(freq: int, total: int):
    ratio = freq / total

    if ratio >= 0.90:
        return "★ MUST PREPARE"

    if ratio >= 0.70:
        return "▲ VERY HIGH"

    if ratio >= 0.40:
        return "◆ HIGH FREQ"

    return "● MODERATE"
```

---

# Supported Question Types

```python
QUESTION_TYPES = {
    "Draw & Explain": [
        "draw",
        "illustrate",
        "neat diagram"
    ],

    "Explain": [
        "explain",
        "describe",
        "discuss"
    ],

    "Compare": [
        "compare",
        "contrast"
    ],

    "Differentiate": [
        "differentiate",
        "difference between"
    ],

    "State": [
        "state",
        "list",
        "enumerate"
    ],

    "Derivation": [
        "derive",
        "prove"
    ],

    "Numerical": [
        "calculate",
        "find",
        "compute",
        "solve"
    ],

    "Algorithm": [
        "algorithm",
        "pseudo code"
    ],

    "Program": [
        "write a program",
        "code"
    ],

    "Case Study": [
        "case study"
    ],

    "Short Note": [
        "short note",
        "brief note"
    ]
}
```

---

# Universal Topic Classification

## Engineering Subjects
- Operating Systems
- DBMS
- CN
- AI/ML
- WT
- Java
- Python
- Cloud
- Cyber Security
- Computer Graphics
- TOC
- SE
- Data Mining

## Electronics Subjects
- Microprocessors
- Embedded Systems
- Digital Electronics
- Analog Electronics
- Signals
- Communication

## Mathematics
- Probability
- Statistics
- Calculus
- Linear Algebra
- Differential Equations

## Mechanical
- Thermodynamics
- SOM
- Fluid Mechanics
- Machine Design

## Civil
- Surveying
- RCC
- Geotechnical
- Transportation

---

# Question Extraction Rules

## Skip
- MCQs
- Repeated headers
- Instructions
- Page numbers
- Footer text
- "Attempt any four"
- Time/marks metadata

## Capture
- Q1, Q2
- a), b), c)
- Numericals
- Derivations
- Definitions
- Long answers

---

# Similar Question Matching

```python
from rapidfuzz import fuzz

if fuzz.token_sort_ratio(q1, q2) > 82:
    # same topic cluster
```

---

# Exam Strategy Page

Final PDF page should include:

- Most repeated topics
- Topics likely for long answers
- Numerical-heavy areas
- Diagram-heavy areas
- Last-minute revision topics
- Most scoring chapters
- Unit-wise preparation strategy

---

# Future Upgrade Ideas

- AI answer generation
- Auto-notes generation
- Flashcard generation
- Topic summaries
- Formula sheets
- One-night-before revision PDFs
- Unit-wise MCQ generation
- Viva questions extraction

---

# Output Goal

Generate a highly readable, exam-oriented, professional question-bank PDF that helps students:

- identify repeated questions
- prioritize study topics
- prepare efficiently
- score maximum marks
- revise quickly before exams

---

*Author: Yash Avsarmal | Version: 2.0.0*
