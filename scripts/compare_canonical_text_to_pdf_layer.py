from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def _norm(value: str) -> str:
    value = value.lower().replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _tokens(value: str) -> list[str]:
    return re.findall(r"\w+", _norm(value), flags=re.UNICODE)


def _similarity(left: str, right: str) -> float:
    a = " ".join(_tokens(left))
    b = " ".join(_tokens(right))
    if not a or not b:
        return 0.0
    # Restrict the PDF window around the candidate article so duplicate language
    # versions elsewhere in the publication do not dilute the comparison.
    if len(b) > len(a) * 2:
        words_a = a.split()
        words_b = b.split()
        window = max(len(words_a) + 80, int(len(words_a) * 1.25))
        best = 0.0
        step = max(20, len(words_a) // 8)
        for start in range(0, max(1, len(words_b) - window + 1), step):
            candidate = " ".join(words_b[start:start + window])
            best = max(best, SequenceMatcher(None, a, candidate, autojunk=False).ratio())
        return best
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _article_heading(article: Any) -> re.Pattern[str]:
    value = re.escape(str(article))
    return re.compile(
        rf"(?im)^\s*(?:článek|clanek|article|čl\.?)\s+{value}\s*$"
    )


def _next_article_heading(article: Any) -> re.Pattern[str]:
    try:
        next_value = int(article) + 1
    except (TypeError, ValueError):
        next_value = article
    value = re.escape(str(next_value))
    return re.compile(
        rf"(?im)^\s*(?:článek|clanek|article|čl\.?)\s+{value}\s*$"
    )


def _page_texts(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    texts: list[str] = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            texts.append("")
    return texts


def _candidate_segments(pages: list[str], article: Any) -> list[tuple[list[int], str]]:
    heading = _article_heading(article)
    next_heading = _next_article_heading(article)
    starts = [index for index, text in enumerate(pages) if heading.search(text)]
    segments: list[tuple[list[int], str]] = []
    for start in starts:
        pieces: list[str] = []
        page_numbers: list[int] = []
        for index in range(start, min(len(pages), start + 5)):
            text = pages[index]
            if index > start:
                match = next_heading.search(text)
                if match:
                    pieces.append(text[:match.start()])
                    page_numbers.append(index + 1)
                    break
            pieces.append(text)
            page_numbers.append(index + 1)
        segments.append((page_numbers, "\n".join(pieces)))
    return segments


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="reports/canonical_treaty_texts_candidate.json")
    parser.add_argument("--pdf-manifest", default="reports/treaty_verified_pdf_manifest.json")
    parser.add_argument("--output", default="reports/treaty_pdf_layer_comparison.json")
    parser.add_argument("--upgrade-output", default="reports/canonical_treaty_texts_pdf_checked.json")
    args = parser.parse_args()

    corpus: dict[str, dict[str, Any]] = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.pdf_manifest).read_text(encoding="utf-8"))
    by_document = {int(item["document_id"]): item for item in manifest}
    page_cache: dict[int, list[str]] = {}
    results: list[dict[str, Any]] = []
    upgraded = json.loads(json.dumps(corpus))

    for key, record in sorted(corpus.items()):
        document_id = int(record["official_pdf_document_id"])
        source = by_document[document_id]
        pdf_path = Path(str(source.get("pdf_path") or ""))
        if not pdf_path.is_file():
            results.append({"key": key, "status": "pdf_missing_from_runner"})
            continue
        if document_id not in page_cache:
            page_cache[document_id] = _page_texts(pdf_path)
        pages = page_cache[document_id]
        segments = _candidate_segments(pages, record["article"])
        if not segments:
            results.append({"key": key, "status": "no_pdf_text_layer_article_locator"})
            continue

        scored = [
            (pages_used, _similarity(record["text"], segment), segment)
            for pages_used, segment in segments
        ]
        pages_used, score, _ = max(scored, key=lambda item: item[1])
        # 0.985 is deliberately strict while tolerating layout artefacts from
        # PDF text extraction (line breaks, page headers and split words).
        direct = score >= 0.985
        result = {
            "key": key,
            "status": "direct_pdf_text_layer_match" if direct else "pdf_text_layer_requires_review",
            "similarity": round(score, 6),
            "pdf_pages": pages_used,
            "official_pdf_sha256": record["official_pdf_sha256"],
            "verified_text_sha256": record["verified_text_sha256"],
        }
        results.append(result)
        if direct:
            upgraded[key]["verification_status"] = "verified_against_authoritative_pdf"
            upgraded[key]["verification_method"] = "authoritative_pdf_text_layer_comparison"
            upgraded[key]["official_pdf_pages"] = pages_used
            upgraded[key]["pdf_text_similarity"] = round(score, 6)

    direct_count = sum(item.get("status") == "direct_pdf_text_layer_match" for item in results)
    review_count = sum(item.get("status") == "pdf_text_layer_requires_review" for item in results)
    no_layer_count = sum(item.get("status") == "no_pdf_text_layer_article_locator" for item in results)
    output = {
        "counts": {
            "provisions": len(results),
            "direct_pdf_text_layer_matches": direct_count,
            "pdf_text_layer_requires_review": review_count,
            "no_pdf_text_layer_article_locator": no_layer_count,
        },
        "comparisons": results,
    }
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.upgrade_output).write_text(json.dumps(upgraded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Direct PDF text-layer verification: {direct_count}/302; "
        f"layer review: {review_count}; scan/no locator: {no_layer_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
