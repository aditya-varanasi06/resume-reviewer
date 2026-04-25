from __future__ import annotations

import html
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from .analyzer import ResumeReviewer
from .rendering import render_markdown

HOST = "127.0.0.1"
PORT = 8765
ROOT = Path(__file__).resolve().parents[2]


class ResumeReviewHandler(BaseHTTPRequestHandler):
    server_version = "ResumeReviewer/0.2"

    def do_GET(self) -> None:
        self._send_html(render_page())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)
        resume = data.get("resume", [""])[0]
        job = data.get("job", [""])[0]
        report = ResumeReviewer().review(resume, job)
        self._send_html(render_page(resume, job, report))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_html(self, content: str) -> None:
        encoded = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def render_page(resume: str = "", job: str = "", report=None) -> str:
    sample_resume = _read_sample("sample_resume.txt")
    sample_job = _read_sample("sample_job.txt")
    report_html = render_report(report) if report else render_empty_state()
    template = page_template()
    return (
        template
        .replace("__RESUME__", html.escape(resume))
        .replace("__JOB__", html.escape(job))
        .replace("__REPORT__", report_html)
        .replace("__SAMPLE_RESUME__", json.dumps(sample_resume))
        .replace("__SAMPLE_JOB__", json.dumps(sample_job))
    )


def render_report(report) -> str:
    score = report.scorecard
    markdown = render_markdown(report)
    report_json = json.dumps(report.to_dict(), indent=2)
    matched = chip_list(report.keyword_match.matched, "match")
    missing = chip_list(report.keyword_match.missing[:18], "miss")
    detected = chip_list(report.section_analysis.detected, "match")
    missing_sections = chip_list(report.section_analysis.missing, "miss")
    strengths = list_items(report.strengths)
    actions = ordered_items(report.next_actions)
    findings = "".join(render_finding(finding) for finding in report.findings)
    rewrites = list_items(report.rewritten_bullets)
    metrics = report.metrics
    score_style = f"--score:{score.overall * 3.6}deg"

    return f"""
    <section class="results" aria-live="polite">
      <div class="result-header">
        <div class="score-ring" style="{score_style}">
          <span>{score.overall}</span>
          <small>Overall</small>
        </div>
        <div>
          <p class="eyebrow">Resume intelligence report</p>
          <h2>{score_label(score.overall)}</h2>
          <p class="summary">{html.escape(report.summary)}</p>
        </div>
      </div>

      <div class="score-grid">
        {score_tile("ATS", score.ats, "Structure, headings, dates")}
        {score_tile("Impact", score.impact, "Metrics and outcomes")}
        {score_tile("Clarity", score.clarity, "Readable, direct language")}
        {score_tile("Role Fit", score.role_fit, "Target job alignment")}
        {score_tile("Skills", score.skills, "Relevant capabilities")}
      </div>

      <div class="metrics-strip">
        {metric_tile("Words", metrics.get("word_count", 0))}
        {metric_tile("Bullets", metrics.get("bullet_count", 0))}
        {metric_tile("Quantified", percent(metrics.get("quantified_bullet_rate", 0)))}
        {metric_tile("Action-led", percent(metrics.get("action_led_bullet_rate", 0)))}
        {metric_tile("Weak phrases", metrics.get("weak_phrase_count", 0))}
      </div>

      <div class="result-layout">
        <section class="panel priority-panel">
          <div class="panel-title">
            <h3>Priority Fixes</h3>
            <span>{len(report.findings)} found</span>
          </div>
          <div class="finding-list">{findings or '<p class="quiet">No major issues detected.</p>'}</div>
        </section>

        <aside class="panel">
          <h3>Strengths</h3>
          <ul>{strengths}</ul>
          <h3>Next Actions</h3>
          <ol>{actions}</ol>
        </aside>
      </div>

      <div class="result-layout lower">
        <section class="panel">
          <div class="panel-title">
            <h3>Target Keywords</h3>
            <span>{report.keyword_match.match_rate:.0%} match</span>
          </div>
          <h4>Matched</h4>
          <div class="chips">{matched or '<span class="empty-chip">None yet</span>'}</div>
          <h4>Missing</h4>
          <div class="chips">{missing or '<span class="empty-chip">None</span>'}</div>
        </section>

        <section class="panel">
          <h3>ATS Sections</h3>
          <h4>Detected</h4>
          <div class="chips">{detected or '<span class="empty-chip">None detected</span>'}</div>
          <h4>Missing</h4>
          <div class="chips">{missing_sections or '<span class="empty-chip">No core gaps</span>'}</div>
        </section>
      </div>

      <section class="panel">
        <div class="panel-title">
          <h3>Rewrite Starters</h3>
          <span>Make bullets sharper</span>
        </div>
        <ul>{rewrites or '<li>Existing sample bullets are already reasonably strong.</li>'}</ul>
      </section>

      <section class="panel exports">
        <div class="panel-title">
          <h3>Export</h3>
          <span>Markdown or JSON</span>
        </div>
        <div class="export-actions">
          <button class="secondary" type="button" data-copy-target="markdown-report">Copy Markdown</button>
          <button class="secondary" type="button" data-copy-target="json-report">Copy JSON</button>
          <button class="secondary" type="button" id="download-markdown">Download Markdown</button>
        </div>
        <details>
          <summary>Markdown report</summary>
          <pre id="markdown-report">{html.escape(markdown)}</pre>
        </details>
        <details>
          <summary>JSON data</summary>
          <pre id="json-report">{html.escape(report_json)}</pre>
        </details>
      </section>
    </section>
    """


def render_empty_state() -> str:
    return """
    <section class="empty-state">
      <div>
        <p class="eyebrow">Ready when you are</p>
        <h2>Paste a resume to generate a full review.</h2>
        <p>The reviewer scores structure, impact, clarity, role fit, skills, and gives concrete rewrite moves.</p>
      </div>
      <div class="empty-grid">
        <span>ATS scan</span>
        <span>Keyword fit</span>
        <span>Impact checks</span>
        <span>Rewrite starters</span>
      </div>
    </section>
    """


def render_finding(finding) -> str:
    return f"""
    <article class="finding {html.escape(finding.severity)}">
      <div>
        <span class="severity">{html.escape(finding.severity.upper())}</span>
        <strong>{html.escape(finding.title)}</strong>
      </div>
      <p>{html.escape(finding.detail)}</p>
      <em>{html.escape(finding.suggestion)}</em>
    </article>
    """


def score_tile(label: str, value: int, detail: str) -> str:
    return f"""
    <div class="score-tile">
      <b>{value}</b>
      <span>{html.escape(label)}</span>
      <small>{html.escape(detail)}</small>
    </div>
    """


def metric_tile(label: str, value: object) -> str:
    return f"""
    <div>
      <b>{html.escape(str(value))}</b>
      <span>{html.escape(label)}</span>
    </div>
    """


def chip_list(items: list[str], kind: str) -> str:
    return "".join(f'<span class="chip {kind}">{html.escape(item)}</span>' for item in items)


def list_items(items: list[str]) -> str:
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def ordered_items(items: list[str]) -> str:
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def percent(value: object) -> str:
    try:
        return f"{float(value):.0%}"
    except (TypeError, ValueError):
        return "0%"


def score_label(value: int) -> str:
    if value >= 85:
        return "Strong resume with targeted polish"
    if value >= 70:
        return "Solid resume with clear upgrade paths"
    if value >= 55:
        return "Promising resume that needs sharper evidence"
    return "Resume needs structure and impact work"


def _read_sample(filename: str) -> str:
    path = ROOT / "samples" / filename
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def page_template() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Advanced Resume Reviewer</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #19212b;
      --muted: #647080;
      --line: #d8e0e8;
      --paper: #eef3f6;
      --panel: #ffffff;
      --panel-soft: #f8fafb;
      --accent: #0b7661;
      --accent-dark: #075143;
      --amber: #9d6a05;
      --danger: #b13a2e;
      --blue: #255f85;
      --shadow: 0 18px 50px rgba(30, 45, 60, 0.10);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--paper);
      color: var(--ink);
    }
    button, textarea { font: inherit; }
    header {
      background:
        linear-gradient(90deg, rgba(11, 118, 97, 0.12), rgba(37, 95, 133, 0.10)),
        #ffffff;
      border-bottom: 1px solid var(--line);
    }
    .topbar {
      width: min(1280px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 22px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 24px;
      align-items: end;
    }
    h1, h2, h3, h4, p { margin-top: 0; }
    h1 {
      margin-bottom: 8px;
      font-size: clamp(30px, 5vw, 56px);
      line-height: 1;
      letter-spacing: 0;
    }
    h2 { font-size: clamp(24px, 3vw, 34px); letter-spacing: 0; margin-bottom: 8px; }
    h3 { font-size: 17px; letter-spacing: 0; margin-bottom: 12px; }
    h4 { margin: 16px 0 8px; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
    p { color: var(--muted); line-height: 1.55; }
    .eyebrow {
      margin-bottom: 8px;
      color: var(--accent-dark);
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .header-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    main {
      width: min(1280px, calc(100% - 32px));
      margin: 24px auto 56px;
      display: grid;
      gap: 24px;
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.05fr);
      gap: 18px;
      align-items: start;
    }
    .composer, .results, .empty-state, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .composer { padding: 18px; position: sticky; top: 16px; }
    .input-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }
    .input-tools {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }
    form { display: grid; gap: 14px; }
    label { display: grid; gap: 8px; font-weight: 800; }
    label span { color: var(--muted); font-weight: 600; font-size: 12px; }
    textarea {
      width: 100%;
      min-height: 270px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      font: 13px/1.55 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      color: var(--ink);
      background: #fbfcfd;
      outline: none;
      transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
    }
    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(11, 118, 97, 0.12);
      background: #ffffff;
    }
    .counter {
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 12px;
      margin-top: -4px;
    }
    button {
      border: 0;
      border-radius: 8px;
      padding: 11px 14px;
      background: var(--accent);
      color: #fff;
      font-weight: 900;
      cursor: pointer;
      min-height: 42px;
    }
    button:hover { background: var(--accent-dark); }
    button.secondary {
      background: #ffffff;
      color: var(--ink);
      border: 1px solid var(--line);
    }
    button.secondary:hover { border-color: var(--accent); color: var(--accent-dark); background: #f5fbf9; }
    .submit-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .submit-row button[type="submit"] { min-width: 178px; }
    .privacy-note { margin: 0; font-size: 12px; color: var(--muted); }
    .empty-state {
      padding: clamp(24px, 5vw, 48px);
      min-height: 430px;
      display: grid;
      align-content: center;
      gap: 26px;
    }
    .empty-state h2 { max-width: 680px; }
    .empty-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(110px, 1fr));
      gap: 10px;
    }
    .empty-grid span {
      border: 1px solid var(--line);
      background: var(--panel-soft);
      border-radius: 8px;
      padding: 14px;
      font-weight: 800;
      color: var(--muted);
    }
    .results { padding: 18px; display: grid; gap: 16px; }
    .result-header {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 18px;
      align-items: center;
      padding: 8px 4px 2px;
    }
    .score-ring {
      width: 132px;
      aspect-ratio: 1;
      border-radius: 50%;
      background:
        radial-gradient(circle at center, #fff 0 58%, transparent 59%),
        conic-gradient(var(--accent) var(--score), #dfe7ed 0);
      display: grid;
      place-items: center;
      align-content: center;
      box-shadow: inset 0 0 0 1px var(--line);
    }
    .score-ring span { display: block; font-size: 42px; line-height: 1; font-weight: 950; color: var(--accent-dark); }
    .score-ring small { color: var(--muted); font-weight: 800; }
    .summary { margin-bottom: 0; }
    .score-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 10px;
    }
    .score-tile, .metrics-strip div {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-soft);
      padding: 13px;
      min-width: 0;
    }
    .score-tile b { display: block; font-size: 30px; line-height: 1; color: var(--accent-dark); }
    .score-tile span, .metrics-strip span { display: block; margin-top: 6px; font-weight: 900; }
    .score-tile small { display: block; margin-top: 5px; color: var(--muted); line-height: 1.35; }
    .metrics-strip {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 10px;
    }
    .metrics-strip b { font-size: 22px; color: var(--blue); }
    .result-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
      gap: 16px;
      align-items: start;
    }
    .result-layout.lower { grid-template-columns: 1fr 1fr; }
    .panel { padding: 18px; box-shadow: none; }
    .panel-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }
    .panel-title span {
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    ul, ol { margin: 0; padding-left: 20px; }
    li { margin: 8px 0; line-height: 1.45; }
    .finding-list { display: grid; gap: 10px; }
    .finding {
      border: 1px solid var(--line);
      border-left: 5px solid var(--amber);
      border-radius: 8px;
      padding: 14px;
      background: #fff;
    }
    .finding.high { border-left-color: var(--danger); }
    .finding.low { border-left-color: var(--blue); }
    .finding div { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .severity {
      border-radius: 999px;
      padding: 4px 8px;
      background: #f3ead9;
      color: var(--amber);
      font-size: 11px;
      font-weight: 950;
    }
    .finding.high .severity { background: #f8e7e4; color: var(--danger); }
    .finding.low .severity { background: #e6f0f6; color: var(--blue); }
    .finding p { margin: 8px 0 6px; }
    .finding em { color: var(--accent-dark); font-style: normal; font-weight: 750; line-height: 1.45; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip, .empty-chip {
      border-radius: 999px;
      padding: 7px 10px;
      font-size: 12px;
      font-weight: 850;
      border: 1px solid var(--line);
      background: #fff;
    }
    .chip.match { color: var(--accent-dark); background: #edf8f4; border-color: #c7e7dd; }
    .chip.miss { color: var(--danger); background: #fbefed; border-color: #efcac5; }
    .empty-chip { color: var(--muted); }
    .exports { display: grid; gap: 12px; }
    .export-actions { display: flex; gap: 10px; flex-wrap: wrap; }
    details {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-soft);
      overflow: hidden;
    }
    summary {
      cursor: pointer;
      padding: 12px 14px;
      font-weight: 900;
    }
    pre {
      margin: 0;
      max-height: 380px;
      overflow: auto;
      background: #111922;
      color: #edf6f2;
      padding: 14px;
      font: 12px/1.55 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    }
    .quiet { color: var(--muted); }
    @media (max-width: 1080px) {
      .workspace, .result-layout, .result-layout.lower { grid-template-columns: 1fr; }
      .composer { position: static; }
    }
    @media (max-width: 760px) {
      .topbar { grid-template-columns: 1fr; align-items: start; }
      .header-actions, .input-header, .submit-row { justify-content: stretch; }
      .header-actions button, .input-tools button, .submit-row button { width: 100%; }
      .input-header { display: grid; }
      .score-grid, .metrics-strip, .empty-grid { grid-template-columns: repeat(2, 1fr); }
      .result-header { grid-template-columns: 1fr; }
      .score-ring { width: 120px; }
      textarea { min-height: 220px; }
    }
    @media (max-width: 460px) {
      main, .topbar { width: min(100% - 22px, 1280px); }
      .score-grid, .metrics-strip, .empty-grid { grid-template-columns: 1fr; }
      .composer, .results, .panel, .empty-state { padding: 14px; }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <p class="eyebrow">Private local review system</p>
        <h1>Advanced Resume Reviewer</h1>
        <p>Paste a resume and optional job description to get ATS, impact, clarity, skills, and role-fit feedback on your machine.</p>
      </div>
      <div class="header-actions">
        <button class="secondary" type="button" id="load-sample">Load Sample</button>
        <button class="secondary" type="button" id="clear-inputs">Clear</button>
      </div>
    </div>
  </header>
  <main>
    <div class="workspace">
      <section class="composer">
        <div class="input-header">
          <div>
            <p class="eyebrow">Review inputs</p>
            <h2>Resume workspace</h2>
          </div>
          <div class="input-tools">
            <button class="secondary" type="button" data-copy-target="resume-input">Copy Resume</button>
            <button class="secondary" type="button" data-copy-target="job-input">Copy Job</button>
          </div>
        </div>
        <form method="post">
          <label for="resume-input">Resume text
            <span>Plain text works best. PDF and DOCX are supported through the CLI.</span>
          </label>
          <textarea id="resume-input" name="resume" required placeholder="Paste resume text here...">__RESUME__</textarea>
          <div class="counter"><span id="resume-count">0 words</span><span>Required</span></div>

          <label for="job-input">Target job description
            <span>Optional, but unlocks keyword and role-fit scoring.</span>
          </label>
          <textarea id="job-input" name="job" placeholder="Paste the job description here...">__JOB__</textarea>
          <div class="counter"><span id="job-count">0 words</span><span>Optional</span></div>

          <div class="submit-row">
            <button type="submit">Review Resume</button>
            <p class="privacy-note">Runs locally through this Python server. No external API calls.</p>
          </div>
        </form>
      </section>
      <div>
        __REPORT__
      </div>
    </div>
  </main>
  <script>
    const sampleResume = __SAMPLE_RESUME__;
    const sampleJob = __SAMPLE_JOB__;
    const resumeInput = document.getElementById("resume-input");
    const jobInput = document.getElementById("job-input");

    function wordCount(text) {
      const matches = text.trim().match(/[A-Za-z0-9+#./-]+/g);
      return matches ? matches.length : 0;
    }

    function updateCounters() {
      document.getElementById("resume-count").textContent = `${wordCount(resumeInput.value)} words`;
      document.getElementById("job-count").textContent = `${wordCount(jobInput.value)} words`;
    }

    function copyElementText(id) {
      const element = document.getElementById(id);
      if (!element) return;
      const text = "value" in element ? element.value : element.innerText;
      navigator.clipboard?.writeText(text);
    }

    document.querySelectorAll("[data-copy-target]").forEach((button) => {
      button.addEventListener("click", () => copyElementText(button.dataset.copyTarget));
    });

    document.getElementById("load-sample").addEventListener("click", () => {
      resumeInput.value = sampleResume;
      jobInput.value = sampleJob;
      updateCounters();
      resumeInput.focus();
    });

    document.getElementById("clear-inputs").addEventListener("click", () => {
      resumeInput.value = "";
      jobInput.value = "";
      updateCounters();
      resumeInput.focus();
    });

    const downloadButton = document.getElementById("download-markdown");
    if (downloadButton) {
      downloadButton.addEventListener("click", () => {
        const report = document.getElementById("markdown-report")?.innerText || "";
        const blob = new Blob([report], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "resume-review.md";
        link.click();
        URL.revokeObjectURL(url);
      });
    }

    resumeInput.addEventListener("input", updateCounters);
    jobInput.addEventListener("input", updateCounters);
    updateCounters();
  </script>
</body>
</html>"""


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ResumeReviewHandler)
    print(f"Advanced Resume Reviewer running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
