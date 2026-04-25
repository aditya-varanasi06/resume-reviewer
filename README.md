# Advanced Resume Reviewer

A local Python resume reviewer that gives practical, ATS-aware feedback without sending resume text to a third-party service.

It reviews a resume for:

- ATS structure and section coverage
- quantified impact and action verbs
- role-fit against a job description
- keyword and skill alignment
- readability and bullet quality
- red flags such as vague claims, missing dates, and repeated weak phrasing
- prioritized rewrite suggestions

## Quick Start

```powershell
python review_resume.py samples\sample_resume.txt --job samples\sample_job.txt --format markdown
```

Run the local web app:

```powershell
python run_web.py
```

Then open the printed localhost URL.

The web app includes:

- side-by-side resume and job-description workspace
- sample data loader for a quick demo
- live word counters
- overall score ring and category score tiles
- metric cards for bullets, quantified impact, action verbs, and weak phrases
- priority findings with severity labels
- matched and missing keyword chips
- ATS section coverage
- rewrite starters
- copy/export controls for Markdown and JSON reports

## Make It A Public Website

The project is now deploy-ready through the WSGI entrypoint in `app.py`.

### Easiest Option: Render

1. Push this folder to a GitHub repository.
2. Go to Render and create a new **Web Service** from that repository.
3. Use these settings:

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:application
```

4. Deploy. Render will give you a public `https://...onrender.com` URL.

### Other Hosts

Any Python host that supports WSGI can run it with:

```bash
gunicorn app:application
```

For local development, keep using:

```powershell
python run_web.py
```

## Install For Development

```powershell
python -m pip install -e .
python -m pytest
```

The engine itself uses only the Python standard library. PDF and DOCX parsing are optional: if `pypdf` or `python-docx` are installed, the CLI can read those formats too.

## CLI Examples

Markdown report:

```powershell
python review_resume.py resume.txt --job job.txt
```

JSON report:

```powershell
python review_resume.py resume.txt --job job.txt --format json --output review.json
```

Paste a job description later:

```powershell
python review_resume.py resume.txt
```

## Project Layout

```text
src/resume_reviewer/
  analyzer.py       scoring and recommendations
  cli.py            command-line interface
  extractors.py     text/PDF/DOCX extraction helpers
  models.py         dataclasses for report output
  rendering.py      markdown/JSON rendering
  web.py            dependency-free local web app
  wsgi.py           production website entrypoint
samples/
  sample_resume.txt
  sample_job.txt
tests/
  test_analyzer.py
```

## Notes

This tool is intentionally heuristic. It is designed to behave like a sharp first-pass reviewer: consistent, fast, and specific. It does not promise hiring outcomes, and it should be used alongside human judgment.
