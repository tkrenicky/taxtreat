from pathlib import Path
import re
import subprocess

from pypdf import PdfReader


GLYPH_CODE_RE = re.compile(r"/C\d+")


def _extract_with_pypdf(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def _looks_garbled(pages: list[str]) -> bool:
    sample = "\n".join(pages[:5])

    if not sample.strip():
        return True

    return len(GLYPH_CODE_RE.findall(sample)) >= 20


def _extract_with_pdftotext(path: Path) -> list[str]:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    return result.stdout.split("\f")


def extract_pdf_pages(path):
    path = Path(path)
    pages = _extract_with_pypdf(path)

    if _looks_garbled(pages):
        pages = _extract_with_pdftotext(path)

    return pages
