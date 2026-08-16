from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "reports" / "treaty_verified_pdf_manifest.json"
DEFAULT_REGISTRY = ROOT / "reports" / "treaty_verbatim_registry.json"
DEFAULT_OUTPUT = ROOT / "reports" / "treaty_pdf_text_audit.json"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def article_patterns(article: object) -> tuple[re.Pattern[str], ...]:
    value = re.escape(str(article))
    return (
        re.compile(rf"\bčlánek\s+{value}\b", re.IGNORECASE),
        re.compile(rf"\bclanek\s+{value}\b", re.IGNORECASE),
        re.compile(rf"\barticle\s+{value}\b", re.IGNORECASE),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    by_url = {item["source_url"]: item for item in manifest}

    instruments: list[dict[str, object]] = []
    provision_results: list[dict[str, object]] = []

    for item in manifest:
        pdf_path = Path(str(item.get("pdf_path") or ""))
        pages: list[str] = []
        if pdf_path.is_file():
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pages.append("")
        text_pages = sum(bool(normalize(page)) for page in pages)
        instruments.append(
            {
                "source_url": item["source_url"],
                "document_id": item["document_id"],
                "pdf_sha256": item.get("pdf_sha256"),
                "page_count": len(pages),
                "pages_with_extractable_text": text_pages,
                "has_usable_text_layer": bool(pages) and text_pages >= max(1, len(pages) // 2),
            }
        )

    instrument_by_url = {item["source_url"]: item for item in instruments}

    for provision in registry["provisions"]:
        source = by_url[provision["source_url"]]
        pdf_path = Path(str(source.get("pdf_path") or ""))
        located_pages: list[int] = []
        if pdf_path.is_file():
            reader = PdfReader(str(pdf_path))
            patterns = article_patterns(provision["article"])
            for index, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                if any(pattern.search(text) for pattern in patterns):
                    located_pages.append(index)

        instrument = instrument_by_url[provision["source_url"]]
        provision_results.append(
            {
                "key": provision["key"],
                "source_url": provision["source_url"],
                "document_id": source["document_id"],
                "article": provision["article"],
                "pdf_sha256": source.get("pdf_sha256"),
                "has_usable_text_layer": instrument["has_usable_text_layer"],
                "article_heading_pages": located_pages,
                "verification_route": (
                    "text_layer_candidate_comparison"
                    if located_pages
                    else "visual_pdf_verification_required"
                ),
            }
        )

    located = sum(bool(item["article_heading_pages"]) for item in provision_results)
    visual = len(provision_results) - located
    output = {
        "counts": {
            "official_instruments": len(instruments),
            "provisions": len(provision_results),
            "provisions_located_from_pdf_text_layer": located,
            "provisions_requiring_visual_pdf_verification": visual,
        },
        "instruments": instruments,
        "provisions": provision_results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"PDF text-layer audit: {located}/{len(provision_results)} provisions located; "
        f"{visual} require visual PDF verification."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
