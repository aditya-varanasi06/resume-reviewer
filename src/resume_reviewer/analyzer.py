from __future__ import annotations

import math
import re
from collections import Counter

from .models import Finding, KeywordMatch, ReviewReport, ScoreCard, SectionAnalysis

SECTION_ALIASES = {
    "summary": ["summary", "profile", "professional summary", "career summary"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
    "education": ["education", "academic background"],
    "projects": ["projects", "selected projects", "portfolio"],
    "certifications": ["certifications", "certificates", "licenses"],
}

ACTION_VERBS = {
    "accelerated", "achieved", "architected", "automated", "built", "created",
    "delivered", "designed", "drove", "enabled", "engineered", "improved",
    "increased", "launched", "led", "migrated", "optimized", "owned",
    "reduced", "shipped", "spearheaded", "streamlined", "transformed",
}

WEAK_PHRASES = {
    "responsible for", "helped with", "worked on", "assisted with", "various",
    "etc", "hard worker", "team player", "detail oriented", "self motivated",
}

COMMON_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "into", "is", "it", "of", "on", "or", "our", "the", "to", "with", "you",
    "your", "we", "will", "this", "that", "using", "use", "role", "team",
}

SKILL_HINTS = {
    "python", "java", "javascript", "typescript", "sql", "aws", "azure", "gcp",
    "docker", "kubernetes", "terraform", "react", "node", "django", "flask",
    "fastapi", "pandas", "numpy", "spark", "airflow", "postgresql", "mysql",
    "mongodb", "redis", "linux", "git", "ci/cd", "machine learning", "llm",
    "nlp", "data analysis", "tableau", "power bi", "excel", "leadership",
    "stakeholder", "agile", "scrum", "api", "microservices",
}

ROLE_PROFILES = {
    "software_engineer": {
        "label": "Software Engineer",
        "keywords": ["python", "java", "javascript", "api", "sql", "git", "testing", "system design"],
        "sections": ["summary", "skills", "experience", "projects", "education"],
    },
    "backend": {
        "label": "Backend Engineer",
        "keywords": ["python", "java", "api", "microservices", "postgresql", "redis", "aws", "docker", "kubernetes", "ci/cd"],
        "sections": ["summary", "skills", "experience", "projects", "education"],
    },
    "frontend": {
        "label": "Frontend Engineer",
        "keywords": ["javascript", "typescript", "react", "api", "testing", "accessibility", "performance", "css"],
        "sections": ["summary", "skills", "experience", "projects", "education"],
    },
    "ml": {
        "label": "ML Engineer",
        "keywords": ["python", "machine learning", "nlp", "pandas", "numpy", "spark", "model", "data pipelines", "aws"],
        "sections": ["summary", "skills", "experience", "projects", "education"],
    },
    "data": {
        "label": "Data Analyst",
        "keywords": ["sql", "python", "excel", "tableau", "power bi", "data analysis", "stakeholder", "dashboard"],
        "sections": ["summary", "skills", "experience", "projects", "education"],
    },
}

LEVEL_EXPECTATIONS = {
    "fresher": {
        "label": "Fresher",
        "required_sections": ["skills", "education", "projects"],
        "minimum_quantified_rate": 0.25,
        "minimum_bullets": 4,
    },
    "experienced": {
        "label": "Experienced",
        "required_sections": ["summary", "skills", "experience", "education"],
        "minimum_quantified_rate": 0.35,
        "minimum_bullets": 6,
    },
    "senior": {
        "label": "Senior",
        "required_sections": ["summary", "skills", "experience", "education"],
        "minimum_quantified_rate": 0.45,
        "minimum_bullets": 8,
    },
}


class ResumeReviewer:
    """Heuristic resume reviewer tuned for practical hiring feedback."""

    def review(
        self,
        resume_text: str,
        job_text: str = "",
        role: str = "software_engineer",
        experience_level: str = "experienced",
    ) -> ReviewReport:
        cleaned = normalize_text(resume_text)
        job_cleaned = normalize_text(job_text)
        role = role if role in ROLE_PROFILES else "software_engineer"
        experience_level = experience_level if experience_level in LEVEL_EXPECTATIONS else "experienced"
        sections = detect_sections(cleaned)
        bullets = extract_bullets(cleaned)
        words = tokenize(cleaned)
        role_keywords = ROLE_PROFILES[role]["keywords"]
        job_keywords = extract_keywords(job_cleaned) if job_cleaned else []
        target_keywords = list(dict.fromkeys(job_keywords + role_keywords))
        resume_keywords = set(extract_keywords(cleaned, include_skills=True))

        section_analysis = self._analyze_sections(sections, role, experience_level)
        keyword_match = self._keyword_match(resume_keywords, target_keywords)
        metrics = self._metrics(cleaned, bullets, words)
        findings = self._findings(cleaned, bullets, section_analysis, keyword_match, metrics, role, experience_level)
        strengths = self._strengths(sections, bullets, keyword_match, metrics, role, experience_level)
        rewritten = self._rewrite_examples(bullets, role)
        scorecard = self._score(section_analysis, keyword_match, metrics, findings, bool(job_cleaned), role, experience_level)
        next_actions = self._next_actions(findings, keyword_match)

        return ReviewReport(
            scorecard=scorecard,
            summary=self._summary(scorecard, metrics, keyword_match, bool(job_cleaned), role, experience_level),
            role=ROLE_PROFILES[role]["label"],
            experience_level=LEVEL_EXPECTATIONS[experience_level]["label"],
            section_analysis=section_analysis,
            keyword_match=keyword_match,
            strengths=strengths,
            findings=findings,
            rewritten_bullets=rewritten,
            next_actions=next_actions,
            metrics=metrics,
        )

    def _analyze_sections(self, sections: set[str], role: str, experience_level: str) -> SectionAnalysis:
        important = LEVEL_EXPECTATIONS[experience_level]["required_sections"]
        missing = [name for name in important if name not in sections]
        scores = {name: (100 if name in sections else 0) for name in SECTION_ALIASES}
        feedback = {}
        for name in SECTION_ALIASES:
            if name in sections:
                feedback[name] = f"{name.title()} section is present and ATS-readable."
            elif name in important:
                feedback[name] = f"Add a clear {name.title()} section for the {LEVEL_EXPECTATIONS[experience_level]['label']} {ROLE_PROFILES[role]['label']} target."
            else:
                feedback[name] = f"Optional section. Add it only if it strengthens your evidence."
        return SectionAnalysis(detected=sorted(sections), missing=missing, section_scores=scores, section_feedback=feedback)

    def _keyword_match(self, resume_keywords: set[str], job_keywords: list[str]) -> KeywordMatch:
        if not job_keywords:
            return KeywordMatch(matched=[], missing=[], match_rate=0.0)
        job_unique = list(dict.fromkeys(job_keywords))
        matched = sorted([word for word in job_unique if word in resume_keywords])
        missing = sorted([word for word in job_unique if word not in resume_keywords])
        return KeywordMatch(matched=matched, missing=missing, match_rate=len(matched) / max(len(job_unique), 1))

    def _metrics(self, text: str, bullets: list[str], words: list[str]) -> dict[str, object]:
        sentence_count = max(len(re.findall(r"[.!?]+", text)), 1)
        quantified = [bullet for bullet in bullets if has_metric(bullet)]
        action_led = [bullet for bullet in bullets if starts_with_action_verb(bullet)]
        weak_hits = sum(text.lower().count(phrase) for phrase in WEAK_PHRASES)
        weak_phrases = sorted([phrase for phrase in WEAK_PHRASES if phrase in text.lower()])
        avg_sentence = len(words) / sentence_count
        return {
            "word_count": len(words),
            "bullet_count": len(bullets),
            "quantified_bullet_count": len(quantified),
            "quantified_bullet_rate": len(quantified) / max(len(bullets), 1),
            "action_led_bullet_rate": len(action_led) / max(len(bullets), 1),
            "weak_phrase_count": weak_hits,
            "weak_phrases": weak_phrases,
            "avg_sentence_words": round(avg_sentence, 1),
        }

    def _findings(
        self,
        text: str,
        bullets: list[str],
        section_analysis: SectionAnalysis,
        keyword_match: KeywordMatch,
        metrics: dict[str, object],
        role: str,
        experience_level: str,
    ) -> list[Finding]:
        findings: list[Finding] = []
        level = LEVEL_EXPECTATIONS[experience_level]
        for missing in section_analysis.missing:
            findings.append(Finding(
                "ATS",
                "high",
                f"Missing {missing} section",
                f"Recruiters and ATS systems expect a clear {missing} section.",
                f"Add a plainly labeled '{missing.title()}' heading with concise, scannable content.",
            ))

        if metrics["quantified_bullet_rate"] < level["minimum_quantified_rate"] and bullets:
            findings.append(Finding(
                "Impact",
                "high",
                "Too few quantified results",
                f"This is below the expected quantified-result rate for a {level['label']} resume.",
                "Add numbers such as revenue, latency, volume, team size, cost, time saved, accuracy, or adoption.",
            ))

        if metrics["action_led_bullet_rate"] < 0.55 and bullets:
            findings.append(Finding(
                "Clarity",
                "medium",
                "Bullets need stronger opening verbs",
                "Several bullets do not begin with decisive ownership or impact verbs.",
                "Start bullets with verbs like 'Built', 'Led', 'Reduced', 'Automated', 'Launched', or 'Optimized'.",
            ))

        if metrics["weak_phrase_count"] > 0:
            findings.append(Finding(
                "Language",
                "medium",
                "Weak or generic phrasing detected",
                "Generic phrasing can make senior work sound junior or passive.",
                "Replace phrases like 'responsible for' and 'worked on' with direct ownership and outcomes.",
            ))

        if keyword_match.missing and keyword_match.match_rate < 0.55:
            findings.append(Finding(
                "Role fit",
                "high",
                f"{ROLE_PROFILES[role]['label']} keyword coverage is low",
                "The resume does not yet mirror enough of the target role and job-description language.",
                "Work missing keywords into truthful experience bullets, skills, and project descriptions.",
            ))

        if metrics["bullet_count"] < level["minimum_bullets"]:
            findings.append(Finding(
                "Depth",
                "medium",
                "Not enough evidence bullets",
                f"A {level['label']} resume needs more proof points than this to feel complete.",
                "Add concise bullets that show scope, action, technical choices, and measurable result.",
            ))

        if role in {"software_engineer", "backend", "frontend", "ml", "data"} and "projects" not in section_analysis.detected:
            severity = "high" if experience_level == "fresher" else "medium"
            findings.append(Finding(
                "Projects",
                severity,
                "Projects section could strengthen credibility",
                "Projects help prove hands-on ability, especially when experience is limited or role-specific skills need evidence.",
                "Add 2-3 projects with tech stack, problem, implementation, and measurable outcome.",
            ))

        if not re.search(r"\b(20\d{2}|19\d{2})\b", text):
            findings.append(Finding(
                "ATS",
                "medium",
                "Dates are hard to detect",
                "Experience entries should include years or date ranges so reviewers can understand progression.",
                "Add consistent date ranges such as 'Jan 2023 - Present' for each role or project.",
            ))

        if metrics["word_count"] < 300:
            findings.append(Finding(
                "Depth",
                "medium",
                "Resume may be too thin",
                "The document appears short for an advanced resume unless it is a highly condensed one-page version.",
                "Add achievement-rich bullets for recent roles, selected projects, leadership, and technical depth.",
            ))
        elif metrics["word_count"] > 1100:
            findings.append(Finding(
                "Focus",
                "medium",
                "Resume may be too long",
                "Long resumes dilute the strongest evidence and can be harder to scan.",
                "Cut older or repetitive bullets and keep the strongest role-relevant achievements.",
            ))

        return findings

    def _strengths(
        self,
        sections: set[str],
        bullets: list[str],
        keyword_match: KeywordMatch,
        metrics: dict[str, object],
        role: str,
        experience_level: str,
    ) -> list[str]:
        strengths: list[str] = []
        if {"experience", "skills", "education"}.issubset(sections):
            strengths.append("Core ATS sections are present and easy to identify.")
        if metrics["quantified_bullet_rate"] >= 0.5:
            strengths.append("A strong share of bullets include measurable outcomes.")
        if metrics["action_led_bullet_rate"] >= 0.7:
            strengths.append("Bullets often open with clear action and ownership.")
        if keyword_match.matched:
            strengths.append(f"Matches target-role language such as {', '.join(keyword_match.matched[:6])}.")
        if role and experience_level:
            strengths.append(f"Review is tuned for a {LEVEL_EXPECTATIONS[experience_level]['label']} {ROLE_PROFILES[role]['label']} target.")
        if not strengths:
            strengths.append("The resume has enough raw material to improve quickly with tighter structure and stronger evidence.")
        return strengths

    def _rewrite_examples(self, bullets: list[str], role: str) -> list[str]:
        rewrites = []
        for bullet in bullets[:8]:
            if has_metric(bullet) and starts_with_action_verb(bullet):
                continue
            cleaned = re.sub(r"^[\-*•\s]+", "", bullet).strip()
            cleaned = re.sub(r"\b(responsible for|worked on|helped with|assisted with)\b", "Owned", cleaned, flags=re.I)
            if not starts_with_action_verb(cleaned):
                cleaned = "Delivered " + cleaned[:1].lower() + cleaned[1:]
            rewrites.append(
                f"{cleaned.rstrip('.')} by applying [role-relevant skill] to improve [business metric] by [X%] across [scope/users/systems]."
            )
            if len(rewrites) == 3:
                break
        return rewrites

    def _score(
        self,
        sections: SectionAnalysis,
        keywords: KeywordMatch,
        metrics: dict[str, object],
        findings: list[Finding],
        has_job: bool,
        role: str,
        experience_level: str,
    ) -> ScoreCard:
        ats = clamp(100 - len(sections.missing) * 16 - missing_date_penalty(findings))
        impact = clamp(35 + metrics["quantified_bullet_rate"] * 45 + metrics["action_led_bullet_rate"] * 20)
        clarity = clamp(88 - metrics["weak_phrase_count"] * 8 - max(metrics["avg_sentence_words"] - 24, 0) * 2)
        role_fit = clamp(45 + keywords.match_rate * 55) if has_job else clamp(55 + keywords.match_rate * 45)
        role_skill_hits = len([word for word in ROLE_PROFILES[role]["keywords"] if word in keywords.matched])
        skills = clamp(45 + min(role_skill_hits * 8, 45))
        severity_penalty = sum({"high": 5, "medium": 3, "low": 1}.get(f.severity, 1) for f in findings)
        overall = clamp((ats * 0.25) + (impact * 0.25) + (clarity * 0.15) + (role_fit * 0.25) + (skills * 0.10) - severity_penalty)
        return ScoreCard(int(overall), int(ats), int(impact), int(clarity), int(role_fit), int(skills))

    def _summary(
        self,
        score: ScoreCard,
        metrics: dict[str, object],
        keywords: KeywordMatch,
        has_job: bool,
        role: str,
        experience_level: str,
    ) -> str:
        fit = f" Role keyword match is {keywords.match_rate:.0%}." if has_job else " Add a job description for sharper role-fit scoring."
        return (
            f"Overall score: {score.overall}/100 for a {LEVEL_EXPECTATIONS[experience_level]['label']} {ROLE_PROFILES[role]['label']} target. "
            f"The resume has {metrics['word_count']} words, "
            f"{metrics['bullet_count']} bullets, and {metrics['quantified_bullet_rate']:.0%} quantified bullets."
            f"{fit}"
        )

    def _next_actions(self, findings: list[Finding], keywords: KeywordMatch) -> list[str]:
        actions = [finding.suggestion for finding in findings[:4]]
        if keywords.missing:
            actions.append("Prioritize these missing target keywords: " + ", ".join(keywords.missing[:10]) + ".")
        return list(dict.fromkeys(actions))[:6]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", text).strip()


def detect_sections(text: str) -> set[str]:
    detected = set()
    lines = [line.strip().lower().strip(":") for line in text.splitlines()]
    for canonical, aliases in SECTION_ALIASES.items():
        if any(line in aliases for line in lines):
            detected.add(canonical)
            continue
        heading_pattern = r"(?im)^\s*(?:" + "|".join(re.escape(alias) for alias in aliases) + r")\s*:?\s*$"
        if re.search(heading_pattern, text):
            detected.add(canonical)
    return detected


def extract_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^([-*•]|\d+[.)])\s+", stripped):
            bullets.append(stripped)
    return bullets


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+/#.-]*", text.lower())


def extract_keywords(text: str, include_skills: bool = False) -> list[str]:
    tokens = tokenize(text)
    counts = Counter(token for token in tokens if token not in COMMON_STOPWORDS and len(token) > 2)
    keywords = [word for word, count in counts.most_common(35) if count >= 1]
    lowered = text.lower()
    skill_matches = [skill for skill in SKILL_HINTS if skill in lowered]
    merged = skill_matches + keywords if include_skills else keywords + skill_matches
    return list(dict.fromkeys(merged))[:35]


def has_metric(text: str) -> bool:
    return bool(re.search(r"(\b\d+[%+$kKmM]?\b|\b\d+x\b|\b\d+\.\d+\b)", text))


def starts_with_action_verb(text: str) -> bool:
    words = tokenize(re.sub(r"^[\-*•\d.)\s]+", "", text))
    return bool(words and words[0] in ACTION_VERBS)


def missing_date_penalty(findings: list[Finding]) -> int:
    return 10 if any(f.title == "Dates are hard to detect" for f in findings) else 0


def clamp(value: float, lower: int = 0, upper: int = 100) -> int:
    if math.isnan(value):
        return lower
    return max(lower, min(upper, round(value)))
