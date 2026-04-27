# ATS Resume Score Analyzer

A Python resume optimization tool for software resumes. It gives structured ATS, role-fit, keyword, and bullet-quality feedback without sending resume text to a third-party service.

It reviews a resume for:

- ATS structure and section coverage
- quantified impact and action verbs
- role-fit against a job description
- keyword and skill alignment
- role-specific analysis for software, backend, frontend, ML, and data roles
- experience-level tuning for fresher, experienced, and senior resumes
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
- TXT/MD resume upload in the browser
- target role and experience-level selectors
- sample data loader for a quick demo
- live word counters
- overall score ring and category score tiles
- metric cards for bullets, quantified impact, action verbs, and weak phrases
- priority findings with severity labels
- matched and missing keyword chips
- ATS section coverage
- section-wise feedback
- before/after rewrite starters
- copy/export controls for Markdown and JSON reports

## Make It A Public Website

The project is now deploy-ready through the WSGI entrypoint in `app.py`.

## Vercel
Follow these steps to deploy this project using Vercel:

### 1. Install Vercel CLI (optional)

```bash
npm install -g vercel
```

### 2. Push your project to GitHub

Make sure your project is in a Git repository and pushed:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

### 3. Deploy via Vercel Dashboard (recommended)

1. Go to [https://vercel.com](https://vercel.com)
2. Sign in with your GitHub / GitLab / Bitbucket account
3. Click **"New Project"**
4. Import your repository
5. Configure project settings (if needed):

   * Framework preset (Next.js, React, etc.)
   * Environment variables
6. Click **Deploy**

### 4. Deploy via CLI (alternative)

Run the following inside your project folder:

```bash
vercel
```

Then follow the prompts:

* Link to existing project or create new
* Select scope
* Confirm settings

### 5. Production Deployment

To deploy to production:

```bash
vercel --prod
```

Once deployed, Vercel will provide a live URL like:

```
https://your-project-name.vercel.app
```
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

Target a specific role and experience level:

```powershell
python review_resume.py resume.txt --job job.txt --role backend --level senior
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

```

## Notes

This tool is intentionally heuristic. It is designed to behave like a sharp first-pass reviewer: consistent, fast, and specific. It does not promise hiring outcomes, and it should be used alongside human judgment.
