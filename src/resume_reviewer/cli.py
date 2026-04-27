from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import ResumeReviewer
from .extractors import ExtractionError, extract_text
from .rendering import render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a resume for ATS, impact, clarity, and role fit.")
    parser.add_argument("resume", help="Path to resume file: txt, md, pdf, or docx.")
    parser.add_argument("--job", help="Optional path to a target job description.")
    parser.add_argument(
        "--role",
        choices=["software_engineer", "backend", "frontend", "ml", "data"],
        default="software_engineer",
        help="Target role profile for role-specific feedback.",
    )
    parser.add_argument(
        "--level",
        choices=["fresher", "experienced", "senior"],
        default="experienced",
        help="Experience level for tuning expectations.",
    )
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format.")
    parser.add_argument("--output", help="Optional output file path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        resume_text = extract_text(args.resume)
        job_text = extract_text(args.job) if args.job else ""
    except (OSError, ExtractionError) as exc:
        parser.error(str(exc))
        return 2

    report = ResumeReviewer().review(resume_text, job_text, role=args.role, experience_level=args.level)
    rendered = render_json(report) if args.format == "json" else render_markdown(report)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
