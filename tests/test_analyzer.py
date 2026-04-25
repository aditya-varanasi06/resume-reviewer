from resume_reviewer import ResumeReviewer


def test_review_scores_strong_resume_with_job_description() -> None:
    resume = """
    Alex Rivera

    Summary
    Senior Python engineer building APIs and data platforms.

    Skills
    Python, FastAPI, PostgreSQL, AWS, Docker, Terraform, Airflow

    Experience
    Senior Engineer | Example Co | 2021 - Present
    - Built FastAPI service processing 20M events daily and reduced latency by 42%.
    - Led AWS migration for 12 services and cut infrastructure cost by 18%.

    Education
    B.S. Computer Science, 2017
    """
    job = "Python FastAPI PostgreSQL AWS Docker Terraform Airflow APIs data pipelines"

    report = ResumeReviewer().review(resume, job)

    assert report.scorecard.overall >= 70
    assert "experience" in report.section_analysis.detected
    assert report.keyword_match.match_rate > 0.5
    assert report.metrics["quantified_bullet_count"] == 2


def test_review_flags_missing_sections_and_weak_bullets() -> None:
    resume = """
    Taylor Smith
    Responsible for various tasks.
    - Worked on reports.
    """

    report = ResumeReviewer().review(resume, "Python SQL AWS")

    titles = {finding.title for finding in report.findings}
    assert "Missing experience section" in titles
    assert "Weak or generic phrasing detected" in titles
    assert report.scorecard.overall < 70
