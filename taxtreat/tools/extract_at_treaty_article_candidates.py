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


ARTICLE_HEADING = re.compile(
    r"(?im)^\s*(?:artikel|article|art\.?)[ \t\u00a0]*(?P<number>\d{1,2})\b[^\n]*$"
)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00ad", "")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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


def extract_article_blocks(text: str) -> dict[int, str]:
    normalized = _normalize_text(text)
    headings = list(ARTICLE_HEADING.finditer(normalized))
    blocks: dict[int, str] = {}
    for index, match in enumerate(headings):
        number = int(match.group("number"))
        if number not in ARTICLE_NUMBERS or number in blocks:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(normalized)
        block = normalized[match.start():end].strip()
        if len(block) >= 40:
            blocks[number] = block
    return blocks


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
                output_path = article_dir / (
                    f"{path.stem}-article-{number}-{digest[:12]}.txt"
                )
                output_path.write_text(block + "\n", encoding="utf-8")
                candidates.append(
                    {
                        "article_number": number,
                        "text_sha256": digest,
                        "character_count": len(block),
                        "artifact_path": str(output_path),
                        "machine_text_candidate": True,
                        "legal_review_completed": False,
                    }
                )
            source_rows.append(
                {
                    "source_order": source.get("source_order"),
                    "final_url": source.get("final_url"),
                    "role_candidate": source.get("role_candidate"),
                    "source_sha256": source.get("sha256"),
                    "extracted_text_character_count": len(text),
                    "article_candidates": candidates,
                }
            )

        article_presence = {
            str(number): sum(
                candidate["article_number"] == number
                for row in source_rows
                for candidate in row["article_candidates"]
            )
            for number in ARTICLE_NUMBERS
        }
        partner_rows.append(
            {
                "partner_label": partner_label,
                "sources": source_rows,
                "article_candidate_presence": article_presence,
                "primary_text_review_completed": False,
                "rate_extraction_released": False,
            }
        )

    return {
        "schema_version": 1,
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partner_count": len(partner_rows),
        "partners": partner_rows,
        "release_constraints": [
            "Article blocks are machine-extracted text candidates only.",
            "Multiple source instruments may contain different versions of an article; source chronology and legal effect must be resolved before interpretation.",
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
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"AT article candidate extraction: {result['partner_count']} pilot partners")
    for partner in result["partners"]:
        print(partner["partner_label"], partner["article_candidate_presence"])


if __name__ == "__main__":
    main()
