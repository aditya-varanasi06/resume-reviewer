from __future__ import annotations

from pathlib import Path


class ExtractionError(RuntimeError):
    pass


def extract_text(path: str | Path) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        return file_path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _extract_pdf(file_path)
    if suffix == ".docx":
        return _extract_docx(file_path)
    raise ExtractionError(f"Unsupported file type: {suffix or '<none>'}. Use txt, md, pdf, or docx.")


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise ExtractionError("PDF support requires optional package 'pypdf'. Install it with: python -m pip install pypdf") from exc
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except ImportError as exc:
        raise ExtractionError("DOCX support requires optional package 'python-docx'. Install it with: python -m pip install python-docx") from exc
    document = docx.Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
