"""
examples/run_example.py
───────────────────────
End-to-end demo that runs without an MCP client.
Just point it at a folder of PDFs.

Usage:
    python examples/run_example.py --papers /path/to/pdf/folder --output question_bank.pdf
"""
import argparse
import sys
from pathlib import Path

# Make sure the src directory is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from exam_mcp.extractor import extract_questions_from_pdf
from exam_mcp.analyser  import group_and_rank_topics
from exam_mcp.pdf_gen   import build_question_bank_pdf


def main():
    parser = argparse.ArgumentParser(description="Exam Question Bank Demo")
    parser.add_argument("--papers",  required=True, help="Folder containing PDF exam papers")
    parser.add_argument("--output",  default="question_bank.pdf", help="Output PDF path")
    parser.add_argument("--subject", default="University Exam", help="Subject name")
    parser.add_argument("--course",  default="", help="Course/semester")
    parser.add_argument("--uni",     default="", help="University name")
    args = parser.parse_args()

    folder = Path(args.papers)
    pdfs   = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {folder}")
        sys.exit(1)

    print(f"Found {len(pdfs)} PDF(s). Extracting questions...")
    all_questions = []
    labels = []
    for pdf in pdfs:
        label = pdf.stem.replace("_", " ").title()
        labels.append(label)
        qs = extract_questions_from_pdf(str(pdf))
        for q in qs:
            q["paper_label"] = label
        all_questions.extend(qs)
        print(f"  {pdf.name}: {len(qs)} questions extracted")

    print(f"\nTotal: {len(all_questions)} questions. Grouping by topic...")
    topics = group_and_rank_topics(all_questions)
    print(f"Found {len(topics)} topic groups.")

    print(f"\nGenerating PDF → {args.output}")
    subject_info = {
        "name": args.subject,
        "course": args.course,
        "university": args.uni,
        "year_range": "–",
        "paper_count": len(pdfs),
    }
    pages = build_question_bank_pdf(args.output, subject_info, topics)
    print(f"Done! PDF has {pages} pages: {args.output}")


if __name__ == "__main__":
    main()
