from __future__ import annotations

from urllib.parse import parse_qs

from .analyzer import ResumeReviewer
from .web import render_page


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")

    if path not in {"/", ""}:
        body = b"Not found"
        start_response("404 Not Found", [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ])
        return [body]

    if method == "GET":
        html = render_page()
        return html_response(start_response, html)

    if method == "POST":
        length = int(environ.get("CONTENT_LENGTH") or "0")
        body_stream = environ["wsgi.input"]
        body = body_stream.read(length).decode("utf-8")
        data = parse_qs(body)
        resume = data.get("resume", [""])[0]
        job = data.get("job", [""])[0]
        report = ResumeReviewer().review(resume, job)
        html = render_page(resume, job, report)
        return html_response(start_response, html)

    body = b"Method not allowed"
    start_response("405 Method Not Allowed", [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Allow", "GET, POST"),
    ])
    return [body]


def html_response(start_response, html: str):
    body = html.encode("utf-8")
    start_response("200 OK", [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ])
    return [body]
