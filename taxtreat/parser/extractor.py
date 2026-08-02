from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .article_parser import parse_articles
from .article_selection import select_best_article_sequence
from .normalize import normalize_pages
from taxtreat.validation.document_identity import validate_treaty_identity

GLYPH_CODE_RE = re.compile(r"/C\d+")
ARTICLE_HEADING_RE = re.compile(
    r"^Článek\s+0*(?P<number>\d{1,3})\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class ExtractionAttempt:
    method: str
    score: int
    total_characters: int
    substantive_pages: int
    article_numbers: tuple[int, ...] = ()
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["article_numbers"] = list(self.article_numbers)
        return result


@dataclass(frozen=True)
class ExtractionResult:
    pages: list[str]
    method: str
    score: int
    attempts: tuple[ExtractionAttempt, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "score": self.score,
            "page_count": len(self.pages),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


def _extract_with_pypdf(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def _extract_with_pdftotext(path: Path) -> list[str]:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    return result.stdout.split("\f")


def _extract_html(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    return [soup.get_text("\n")]


def _page_quality(text: str) -> int:
    normalized = normalize_pages([text])[0] if text else ""
    alphanumeric = sum(char.isalnum() for char in normalized)
    headings = len(ARTICLE_HEADING_RE.findall(normalized))
    garbled = len(GLYPH_CODE_RE.findall(text))
    replacement_characters = text.count("�")
    return (
        min(alphanumeric, 4000)
        + headings * 800
        - garbled * 20
        - replacement_characters * 10
    )


def _merge_page_sets(*page_sets: list[str]) -> list[str]:
    page_count = max((len(pages) for pages in page_sets), default=0)
    merged: list[str] = []
    for index in range(page_count):
        candidates = [
            pages[index]
            for pages in page_sets
            if index < len(pages)
        ]
        merged.append(max(candidates, key=_page_quality, default=""))
    return merged


def _document_metrics(pages: list[str]) -> tuple[int, int, tuple[int, ...], int]:
    normalized = normalize_pages(pages)
    text = "\n".join(normalized)
    article_numbers = tuple(
        sorted({int(match.group("number")) for match in ARTICLE_HEADING_RE.finditer(text)})
    )
    total_characters = sum(len(page.strip()) for page in normalized)
    substantive_pages = sum(len(page.strip()) >= 100 for page in normalized)
    page_count = max(len(normalized), 1)

    score = min(total_characters // 100, 250)
    score += int(200 * substantive_pages / page_count)
    score += min(len(article_numbers), 40) * 20
    if 1 in article_numbers:
        score += 250
    for number in (10, 11, 12):
        if number in article_numbers:
            score += 120
    if all(number in article_numbers for number in (1, 2, 10, 11, 12)):
        score += 400

    normalized_text = text.casefold()
    if "smlouva" in normalized_text or "agreement" in normalized_text or "convention" in normalized_text:
        score += 30

    garbled = len(GLYPH_CODE_RE.findall(text)) + text.count("�")
    score -= min(garbled, 200) * 5
    return score, total_characters, article_numbers, substantive_pages


def _attempt(method: str, pages: list[str], error: str | None = None) -> ExtractionAttempt:
    if error is not None:
        return ExtractionAttempt(
            method=method,
            score=-1,
            total_characters=0,
            substantive_pages=0,
            error=error,
        )
    score, total, numbers, substantive = _document_metrics(pages)
    return ExtractionAttempt(
        method=method,
        score=score,
        total_characters=total,
        substantive_pages=substantive,
        article_numbers=numbers,
    )


def _should_ocr(attempt: ExtractionAttempt) -> bool:
    mode = os.getenv("TAXTREAT_OCR", "auto").strip().lower()
    if mode in {"0", "false", "off", "no"}:
        return False
    if mode in {"1", "true", "on", "yes", "always"}:
        return True
    numbers = set(attempt.article_numbers)
    return 1 not in numbers or not {10, 11, 12}.issubset(numbers)


def _ocr_image(path: Path, language: str) -> str:
    result = subprocess.run(
        [
            "tesseract",
            str(path),
            "stdout",
            "-l",
            language,
            "--psm",
            "3",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return result.stdout


def _numeric_image_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"-(\d+)\.[^.]+$", path.name)
    return (int(match.group(1)) if match else 0, path.name)


def _pdf_page_count(path: Path) -> int:
    """Return the page count without extracting page text."""

    try:
        result = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        match = re.search(r"^Pages:\\s*(\\d+)\\s*$", result.stdout, re.MULTILINE)
        if match:
            return int(match.group(1))
    except (FileNotFoundError, subprocess.SubprocessError, ValueError):
        pass

    return len(PdfReader(str(path)).pages)


def _ocr_pdf_page(
    path: Path,
    page_number: int,
    *,
    dpi: int,
    language: str,
    workdir: Path,
) -> str:
    """Render and OCR one PDF page with bounded subprocess runtimes."""

    prefix = workdir / f"page-{page_number:04d}"
    subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-singlefile",
            "-png",
            "-gray",
            "-r",
            str(dpi),
            str(path),
            str(prefix),
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )
    image = prefix.with_suffix(".png")
    if not image.exists():
        raise RuntimeError(f"OCR renderer produced no image for page {page_number}")
    return _ocr_image(image, language)


def _country_start_page(pages: list[str], expected_country: str | None) -> int | None:
    if not expected_country:
        return 0

    for index, page in enumerate(pages):
        identity = validate_treaty_identity(
            expected_country=expected_country,
            text=page,
            source_title=None,
            minimum_text_length=30,
        )
        if identity.is_valid:
            return index
    return None


def _ocr_target_reached(pages: list[str], expected_country: str | None) -> bool:
    start = _country_start_page(pages, expected_country)
    if start is None:
        return False

    normalized = normalize_pages(pages[start:])
    try:
        articles = parse_articles("\n".join(normalized))
    except RuntimeError:
        return False
    return select_best_article_sequence(articles).is_complete


def _extract_with_ocr(
    path: Path,
    *,
    expected_country: str | None = None,
) -> list[str]:
    if shutil.which("pdftoppm") is None or shutil.which("tesseract") is None:
        raise RuntimeError("OCR tools pdftoppm/tesseract are not installed")

    dpi = int(os.getenv("TAXTREAT_OCR_DPI", "160"))
    workers = max(1, int(os.getenv("TAXTREAT_OCR_WORKERS", "2")))
    language = os.getenv("TAXTREAT_OCR_LANG", "ces+eng")
    document_page_count = _pdf_page_count(path)
    batch_pages = max(1, int(os.getenv("TAXTREAT_OCR_MAX_PAGES", "20")))
    batch_pages = max(
        1,
        int(os.getenv("TAXTREAT_OCR_BATCH_PAGES", str(batch_pages))),
    )
    hard_max_pages = max(
        0,
        int(os.getenv("TAXTREAT_OCR_HARD_MAX_PAGES", "0")),
    )
    page_count = (
        min(document_page_count, hard_max_pages)
        if hard_max_pages
        else document_page_count
    )

    if page_count <= 0:
        raise RuntimeError("OCR could not determine a positive PDF page count")

    with tempfile.TemporaryDirectory(prefix="taxtreat_ocr_") as tmp:
        workdir = Path(tmp)
        pages: list[str] = []
        completed = 0

        print(
            f"OCR    {path.name}: 0/{page_count} pages (dpi={dpi}, workers={workers})",
            flush=True,
        )

        for first_page in range(1, page_count + 1, batch_pages):
            last_page = min(first_page + batch_pages - 1, page_count)
            batch = [""] * (last_page - first_page + 1)

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(
                        _ocr_pdf_page,
                        path,
                        page_number,
                        dpi=dpi,
                        language=language,
                        workdir=workdir,
                    ): page_number
                    for page_number in range(first_page, last_page + 1)
                }

                for future in as_completed(futures):
                    page_number = futures[future]
                    try:
                        batch[page_number - first_page] = future.result()
                    except Exception as exc:
                        print(
                            f"OCRERR {path.name}: page {page_number}: "
                            f"{type(exc).__name__}: {exc}",
                            flush=True,
                        )

                    completed += 1
                    if completed == page_count or completed % 2 == 0:
                        print(
                            f"OCR    {path.name}: {completed}/{page_count} pages",
                            flush=True,
                        )

            pages.extend(batch)
            if _ocr_target_reached(pages, expected_country):
                print(
                    f"OCRSTOP {path.name}: treaty articles complete after "
                    f"{len(pages)}/{page_count} pages",
                    flush=True,
                )
                break

        if not any(page.strip() for page in pages):
            raise RuntimeError("OCR produced no usable page text")
        return pages


def extract_document(
    path: str | Path,
    *,
    expected_country: str | None = None,
    source_title: str | None = None,
) -> ExtractionResult:
    """Extract text through all available generic backends and select the best result.

    The selection is deterministic and based on document-wide quality, article
    sequence coverage and page density. OCR is invoked only when normal text
    backends do not expose Article 1 and Articles 10-12 (unless overridden by
    ``TAXTREAT_OCR``).
    """

    path = Path(path)
    attempts: list[ExtractionAttempt] = []
    candidates: list[tuple[str, list[str], ExtractionAttempt]] = []

    if path.suffix.lower() in {".html", ".htm"}:
        try:
            pages = _extract_html(path)
            attempt = _attempt("html", pages)
            attempts.append(attempt)
            return ExtractionResult(pages, "html", attempt.score, tuple(attempts))
        except Exception as exc:
            attempt = _attempt("html", [], f"{type(exc).__name__}: {exc}")
            return ExtractionResult([], "failed", -1, (attempt,))

    for method, extractor in (
        ("pypdf", _extract_with_pypdf),
        ("pdftotext", _extract_with_pdftotext),
    ):
        try:
            pages = extractor(path)
            attempt = _attempt(method, pages)
            attempts.append(attempt)
            candidates.append((method, pages, attempt))
        except Exception as exc:
            attempts.append(_attempt(method, [], f"{type(exc).__name__}: {exc}"))

    if len(candidates) >= 2:
        pages = _merge_page_sets(*(candidate[1] for candidate in candidates))
        attempt = _attempt("hybrid", pages)
        attempts.append(attempt)
        candidates.append(("hybrid", pages, attempt))

    if not candidates:
        return ExtractionResult([], "failed", -1, tuple(attempts))

    best_method, best_pages, best_attempt = max(candidates, key=lambda item: item[2].score)

    if _should_ocr(best_attempt):
        try:
            try:
                ocr_pages = _extract_with_ocr(
                    path,
                    expected_country=expected_country,
                )
            except TypeError as exc:
                if "unexpected keyword argument" not in str(exc):
                    raise
                ocr_pages = _extract_with_ocr(path)
            ocr_attempt = _attempt("ocr", ocr_pages)
            attempts.append(ocr_attempt)
            candidates.append(("ocr", ocr_pages, ocr_attempt))

            merged_pages = _merge_page_sets(best_pages, ocr_pages)
            merged_attempt = _attempt(f"{best_method}+ocr", merged_pages)
            attempts.append(merged_attempt)
            candidates.append((f"{best_method}+ocr", merged_pages, merged_attempt))
        except Exception as exc:
            attempts.append(_attempt("ocr", [], f"{type(exc).__name__}: {exc}"))

    best_method, best_pages, best_attempt = max(candidates, key=lambda item: item[2].score)
    return ExtractionResult(best_pages, best_method, best_attempt.score, tuple(attempts))


def extract_pdf_pages(path: str | Path) -> list[str]:
    """Backward-compatible wrapper returning only the selected page texts."""

    return extract_document(path).pages
