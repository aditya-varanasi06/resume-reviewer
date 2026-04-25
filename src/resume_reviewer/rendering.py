from __future__ import annotations

import json

from .models import ReviewReport


def render_json(report: ReviewReport) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


def render_markdown(report: ReviewReport) -> str:
    score = report.scorecard
    lines = [
        "# Resume Review Report",
        "",
        "## Scorecard",
        "",
        f"- Overall: **{score.overall}/100**",
        f"- ATS: {score.ats}/100",
        f"- Impact: {score.impact}/100",
        f"- Clarity: {score.clarity}/100",
        f"- Role fit: {score.role_fit}/100",
        f"- Skills: {score.skills}/100",
        "",
        "## Executive Summary",
        "",
        report.summary,
        "",
        "## Strengths",
        "",
    ]
    lines.extend(f"- {item}" for item in report.strengths)
    lines.extend(["", "## Priority Findings", ""])
    for finding in report.findings:
        lines.extend([
            f"### [{finding.severity.upper()}] {finding.title}",
            "",
            f"**Category:** {finding.category}",
            "",
            finding.detail,
            "",
            f"**Fix:** {finding.suggestion}",
            "",
        ])
    if not report.findings:
        lines.extend(["No major issues detected.", ""])

    lines.extend(["## Job Keyword Match", ""])
    if report.keyword_match.matched or report.keyword_match.missing:
        lines.append(f"- Match rate: {report.keyword_match.match_rate:.0%}")
        lines.append(f"- Matched: {', '.join(report.keyword_match.matched) or 'None'}")
        lines.append(f"- Missing: {', '.join(report.keyword_match.missing[:20]) or 'None'}")
    else:
        lines.append("No job description provided.")

    lines.extend(["", "## Rewrite Starters", ""])
    if report.rewritten_bullets:
        lines.extend(f"- {bullet}" for bullet in report.rewritten_bullets)
    else:
        lines.append("Existing sample bullets are already reasonably strong.")

    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"{index}. {action}" for index, action in enumerate(report.next_actions, start=1))
    return "\n".join(lines).strip() + "\n"
