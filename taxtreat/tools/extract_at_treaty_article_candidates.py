from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from pypdf import PdfReader


DEFAULT_INPUT = Path("artifacts/at/instrument_chain_pilot.json")
DEFAULT_OUTPUT = Path("artifacts/at/article_candidate_inventory.json")
DEFAULT_ARTICLE_DIR = Path("artifacts/at/article_candidates")
ARTICLE_NUMBERS = (10, 11, 12)
MIN_SUBSTANTIVE_CHARACTERS = 180
MIN_SUBSTANTIVE_SENTENCES = 2
ROMAN_ARTICLE_NUMBERS = {"X": 10, "XI": 11, "XII": 12}
ROYALTY_TEXT_RE = re.compile(r"(?:lizenzgebühr|royalt)", flags=re.IGNORECASE)

ARTICLE_HEADING = re.compile(
    r"(?im)^\s*(?:artikel|article|art\.?)[ \t\u00a0]*(?P<number>\d{1,2}|XII|XI|X)\b[^\n]*$"
)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00ad", "")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _article_number(token: str) -> int:
    normalized = token.strip().upper()
    if normalized.isdigit():
        return int(normalized)
    if normalized in ROMAN_ARTICLE_NUMBERS:
        return ROMAN_ARTICLE_NUMBERS[normalized]
    raise ValueError(f"Unsupported treaty article number token: {token}")


def extract_text(path: Path, content_type: str) -> str:
    data = path.read_bytes()
    if not data:
        raise ValueError(f"Empty source file: {path}")
    lower_type = (content_type or "").lower()
    if "pdf" in lower_type or path.suffix.lower() == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        pages = [(page.extract_text() or "") for page in reader.pages]
        return _normalize_text("\n".join(pages))
    if "html" in lower_type or path.suffix.lower() in {".html", ".htm"}:
        soup = BeautifulSoup(data, "lxml")
        return _normalize_text(soup.get_text("\n", strip=True))
    try:
        return _normalize_text(data.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError(f"Unsupported source text format: {path}") from exc


def _article_quality(block: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    body = ARTICLE_HEADING.sub("", block, count=1).strip()
    if len(body) < MIN_SUBSTANTIVE_CHARACTERS:
        reasons.append("article_body_too_short")
    sentence_like = len(re.findall(r"(?:\.|;|:)\s", body))
    numbered_paragraphs = len(re.findall(r"(?m)^\s*\d+[\.)]\s+", body))
    if sentence_like < MIN_SUBSTANTIVE_SENTENCES and numbered_paragraphs < 2:
        reasons.append("insufficient_substantive_structure")
    cross_refs = len(
        re.findall(
            r"(?i)\b(?:artikel|article|art\.)\s*(?:\d{1,2}|XII|XI|X)\b",
            body,
        )
    )
    if cross_refs and len(body) < 320 and numbered_paragraphs == 0:
        reasons.append("possible_cross_reference_only")
    return (not reasons, reasons)


def _royalty_semantic_candidate(text: str) -> bool:
    return bool(ROYALTY_TEXT_RE.search(text))


def _all_article_blocks(text: str) -> list[tuple[int, str]]:
    normalized = _normalize_text(text)
    headings = list(ARTICLE_HEADING.finditer(normalized))
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(headings):
        number = _article_number(match.group("number"))
        end = headings[index + 1].start() if index + 1 < len(headings) else len(normalized)
        block = normalized[match.start():end].strip()
        if block:
            blocks.append((number, block))
    return blocks


def extract_article_blocks(text: str) -> dict[int, str]:
    grouped: dict[int, list[str]] = {}
    for number, block in _all_article_blocks(text):
        if number in ARTICLE_NUMBERS:
            grouped.setdefault(number, []).append(block)

    selected: dict[int, str] = {}
    for number, candidates in grouped.items():
        selected[number] = max(
            candidates,
            key=lambda block: (_article_quality(block)[0], len(block)),
        )
    return selected


def extract_nonstandard_royalty_blocks(text: str) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    seen: set[tuple[int, str]] = set()
    for number, block in _all_article_blocks(text):
        if number in ARTICLE_NUMBERS or not _royalty_semantic_candidate(block):
            continue
        digest = hashlib.sha256(block.encode("utf-8")).hexdigest()
        key = (number, digest)
        if key in seen:
            continue
        seen.add(key)
        candidates.append((number, block))
    return candidates


def build_article_candidate_inventory(
    pilot: dict[str, Any],
    *,
    article_dir: Path,
) -> dict[str, Any]:
    if pilot.get("source_country") != "AT":
        raise ValueError("Expected Austrian instrument-chain pilot")
    if pilot.get("status") != "instrument_chain_pilot_acquired_not_reviewed":
        raise ValueError("Austrian instrument-chain pilot is not in acquisition state")

    article_dir.mkdir(parents=True, exist_ok=True)
    partner_rows: list[dict[str, Any]] = []
    for partner in pilot.get("partners", []):
        partner_label = str(partner.get("partner_label") or "")
        if not partner_label:
            raise ValueError("Instrument-chain record without partner label")
        source_rows: list[dict[str, Any]] = []
        for source in partner.get("sources", []):
            path = Path(str(source.get("artifact_path") or ""))
            if not path.is_file():
                raise ValueError(f"Missing acquired treaty source: {path}")
            text = extract_text(path, str(source.get("content_type") or ""))
            blocks = extract_article_blocks(text)
            candidates: list[dict[str, Any]] = []
            for number in ARTICLE_NUMBERS:
                block = blocks.get(number)
                if block is None:
                    continue
                digest = hashlib.sha256(block.encode("utf-8")).hexdigest()
                substantive, quality_flags = _article_quality(block)
                output_path = article_dir / f"{path.stem}-article-{number}-{digest[:12]}.txt"
                output_path.write_text(block + "\n", encoding="utf-8")
                candidates.append({
                    "article_number": number,
                    "text_sha256": digest,
                    "character_count": len(block),
                    "artifact_path": str(output_path),
                    "machine_text_candidate": True,
                    "substantive_article_candidate": substantive,
                    "semantic_income_candidate": None,
                    "quality_flags": quality_flags,
                    "legal_review_completed": False,
                })
            for number, block in extract_nonstandard_royalty_blocks(text):
                digest = hashlib.sha256(block.encode("utf-8")).hexdigest()
                substantive, quality_flags = _article_quality(block)
                output_path = article_dir / f"{path.stem}-article-{number}-royalty-{digest[:12]}.txt"
                output_path.write_text(block + "\n", encoding="utf-8")
                candidates.append({
                    "article_number": number,
                    "text_sha256": digest,
                    "character_count": len(block),
                    "artifact_path": str(output_path),
                    "machine_text_candidate": True,
                    "substantive_article_candidate": substantive,
                    "semantic_income_candidate": "royalty",
                    "quality_flags": quality_flags,
                    "legal_review_completed": False,
                })
            source_rows.append({
                "source_order": source.get("source_order"),
                "final_url": source.get("final_url"),
                "role_candidate": source.get("role_candidate"),
                "source_sha256": source.get("sha256"),
                "extracted_text_character_count": len(text),
                "article_candidates": candidates,
            })

        article_presence = {
            str(number): sum(
                candidate["article_number"] == number
                and candidate["substantive_article_candidate"] is True
                and candidate.get("semantic_income_candidate") is None
                for row in source_rows
                for candidate in row["article_candidates"]
            )
            for number in ARTICLE_NUMBERS
        }
        rejected_presence = {
            str(number): sum(
                candidate["article_number"] == number
                and candidate["substantive_article_candidate"] is False
                and candidate.get("semantic_income_candidate") is None
                for row in source_rows
                for candidate in row["article_candidates"]
            )
            for number in ARTICLE_NUMBERS
        }
        partner_rows.append({
            "partner_label": partner_label,
            "sources": source_rows,
            "article_candidate_presence": article_presence,
            "rejected_article_candidate_presence": rejected_presence,
            "primary_text_review_completed": False,
            "rate_extraction_released": False,
        })

    return {
        "schema_version": 4,
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partner_count": len(partner_rows),
        "partners": partner_rows,
        "release_constraints": [
            "Article 10/11/12 blocks are machine-extracted text candidates only; Arabic and Roman X/XI/XII headings are normalized to article numbers 10/11/12.",
            "Other numeric article headings may be retained only as semantic royalty candidates where royalty terminology is detected; they never become standard Article 12 candidates automatically.",
            "When RIS exposes duplicate headings for the same article number, the most substantive machine block is selected; this remains a candidate and not a legal conclusion.",
            "Short or cross-reference-only headings are retained for audit but excluded from substantive candidate counts.",
            "Multiple source instruments may contain different versions of an article; source chronology and legal effect must be resolved before interpretation.",
            "Article number alone does not establish income type; older treaties may place royalties outside Article 12.",
            "No rate, ownership threshold, beneficial-owner condition or other treaty condition is released by this output.",
            "MLI synthesized text is evidence of a candidate consolidated reading, not a substitute for bilateral matching and effective-date adjudication."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--article-dir", type=Path, default=DEFAULT_ARTICLE_DIR)
    args = parser.parse_args()

    pilot = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_article_candidate_inventory(pilot, article_dir=args.article_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AT article candidate extraction: {result['partner_count']} partners")
    for partner in result["partners"]:
        print(partner["partner_label"], partner["article_candidate_presence"], "rejected=", partner["rejected_article_candidate_presence"])


if __name__ == "__main__":
    main()
