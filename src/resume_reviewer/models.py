from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Finding:
    category: str
    severity: str
    title: str
    detail: str
    suggestion: str


@dataclass(frozen=True)
class ScoreCard:
    overall: int
    ats: int
    impact: int
    clarity: int
    role_fit: int
    skills: int


@dataclass(frozen=True)
class SectionAnalysis:
    detected: list[str]
    missing: list[str]
    section_scores: dict[str, int]


@dataclass(frozen=True)
class KeywordMatch:
    matched: list[str]
    missing: list[str]
    match_rate: float


@dataclass(frozen=True)
class ReviewReport:
    scorecard: ScoreCard
    summary: str
    section_analysis: SectionAnalysis
    keyword_match: KeywordMatch
    strengths: list[str]
    findings: list[Finding]
    rewritten_bullets: list[str]
    next_actions: list[str]
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
