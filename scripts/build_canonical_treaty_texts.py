from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "br":
            self.parts.append("\n")


def _html_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value or "")
    return html.unescape("".join(parser.parts)).strip()


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _is_article_fragment(fragment: dict[str, Any]) -> bool:
    return str(fragment.get("typ") or "").lower() in {"clanek", "clanekms"}


def _heading_matches(value: str, article: Any) -> bool:
    normalized = _normalized(value).replace(".", "")
    return bool(
        re.fullmatch(
            rf"(článek|clanek|article|čl)\s+{re.escape(str(article))}",
            normalized,
            flags=re.IGNORECASE,
        )
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def extract_article(payload: dict[str, Any], article: Any) -> tuple[str, list[int]] | None:
    fragments = payload.get("fragmenty")
    if not isinstance(fragments, list):
        return None

    for index, fragment in enumerate(fragments):
        if not isinstance(fragment, dict) or not _is_article_fragment(fragment):
            continue
        heading = _html_text(str(fragment.get("xhtml") or ""))
        if not _heading_matches(heading, article):
            continue

        depth = int(fragment.get("hloubka") or 999)
        parts: list[str] = []
        fragment_ids: list[int] = []
        for offset, candidate in enumerate(fragments[index:]):
            if not isinstance(candidate, dict):
                continue
            if (
                offset
                and _is_article_fragment(candidate)
                and int(candidate.get("hloubka") or 999) <= depth
            ):
                break
            xhtml = candidate.get("xhtml")
            if xhtml:
                text = _html_text(str(xhtml))
                if text:
                    parts.append(text)
            fragment_id = candidate.get("fragmentId")
            if isinstance(fragment_id, int):
                fragment_ids.append(fragment_id)
        text = "\n".join(parts).strip()
        if text:
            return text, fragment_ids
    return None


def _load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_corpus(
    registry_path: Path,
    pdf_manifest_path: Path,
    structured_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = _load_registry(registry_path)
    pdf_manifest = json.loads(pdf_manifest_path.read_text(encoding="utf-8"))
    by_url = {item["source_url"]: item for item in pdf_manifest}

    corpus: dict[str, Any] = {}
    unresolved: list[dict[str, Any]] = []

    for provision in registry["provisions"]:
        key = provision["key"]
        source = by_url.get(provision["source_url"])
        if not source or not source.get("pdf_sha256"):
            unresolved.append({"key": key, "reason": "authoritative_pdf_hash_missing"})
            continue

        document_id = int(source["document_id"])
        candidates = sorted((structured_dir / str(document_id)).glob("*.json"))
        extracted: tuple[str, list[int]] | None = None
        structured_file: Path | None = None
        raw_bytes: bytes | None = None
        for path in candidates:
            raw = path.read_bytes()
            try:
                payload = json.loads(raw.decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            result = extract_article(payload, provision["article"])
            if result is not None:
                extracted = result
                structured_file = path
                raw_bytes = raw
                break

        if extracted is None or structured_file is None or raw_bytes is None:
            unresolved.append({"key": key, "reason": "article_not_found_in_official_structured_source"})
            continue

        text, fragment_ids = extracted
        corpus[key] = {
            "title": f"CZ-{provision['recipient_country']} treaty · article {provision['article']}",
            "recipient_country": provision["recipient_country"],
            "article": provision["article"],
            "income_types": provision["income_types"],
            "source_url": provision["source_url"],
            "official_pdf_document_id": document_id,
            "official_pdf_sha256": source["pdf_sha256"],
            "official_pdf_download_mode": source.get("download_mode"),
            "structured_source_format": "e-sbirka_informativni_zneni_JSON",
            "structured_source_sha256": _sha256_bytes(raw_bytes),
            "structured_fragment_ids": fragment_ids,
            "text": text,
            "verified_text_sha256": _sha256_text(text),
            "text_source_status": "official_esbirka_structured_text_pdf_anchored",
            "verification_status": "structured_text_ready_pdf_direct_check_pending",
            "verification_method": "official_esbirka_structured_json_with_authoritative_pdf_hash",
        }

    counts = {
        "expected_provisions": 302,
        "canonical_provisions": len(corpus),
        "unresolved": len(unresolved),
        "authoritative_pdf_anchored": sum(bool(item.get("official_pdf_sha256")) for item in corpus.values()),
        "direct_pdf_verified": sum(
            item.get("verification_status") == "verified_against_authoritative_pdf"
            for item in corpus.values()
        ),
    }
    report = {
        "counts": counts,
        "complete_structured_corpus": len(corpus) == 302 and not unresolved,
        "strict_direct_pdf_gate_complete": counts["direct_pdf_verified"] == 302,
        "unresolved": unresolved,
    }
    return corpus, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="reports/treaty_verbatim_registry.json")
    parser.add_argument("--pdf-manifest", default="reports/treaty_verified_pdf_manifest.json")
    parser.add_argument("--structured-dir", default="artifacts/structured_sources")
    parser.add_argument("--output", default="reports/canonical_treaty_texts_candidate.json")
    parser.add_argument("--report", default="reports/canonical_treaty_texts_candidate_report.json")
    args = parser.parse_args()

    corpus, report = build_corpus(
        Path(args.registry),
        Path(args.pdf_manifest),
        Path(args.structured_dir),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Canonical treaty text candidates: {report['counts']['canonical_provisions']}/302; "
        f"PDF anchored: {report['counts']['authoritative_pdf_anchored']}/302; "
        f"direct PDF verified: {report['counts']['direct_pdf_verified']}/302"
    )
    return 0 if report["complete_structured_corpus"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
