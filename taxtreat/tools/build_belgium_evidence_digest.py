from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

WORKSHEET = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_worksheet.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_evidence_digest.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def split_numbered_paragraphs(text: str) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", text).strip()

    parts = re.split(
        r"(?=\n?\s*\d+\.\s+)",
        normalized,
    )

    return [
        re.sub(r"\s+", " ", part).strip()
        for part in parts
        if part.strip()
    ]


def relevant_paragraphs(
    paragraphs: list[str],
    *,
    income_type: str,
) -> list[dict[str, Any]]:
    markers = {
        "dividend": (
            "procent",
            "vlastn",
            "skutecn",
            "spolecnost",
        ),
        "interest": (
            "procent",
            "osvobozen",
            "obchodn",
            "bankovn",
            "verejn",
            "vklad",
            "pujc",
            "uver",
        ),
        "royalty": (
            "procent",
            "licenc",
            "autorsk",
            "patent",
            "ochrann",
            "know-how",
            "zarizen",
            "software",
        ),
    }[income_type]

    results = []

    for index, paragraph in enumerate(paragraphs, start=1):
        lowered = paragraph.casefold()

        matched = [
            marker
            for marker in markers
            if marker in lowered
        ]

        if matched:
            results.append(
                {
                    "sequence": index,
                    "matched_markers": matched,
                    "text": paragraph,
                }
            )

    return results


def build_digest() -> dict[str, Any]:
    worksheet = read_json(WORKSHEET)

    scopes = []

    for scope in worksheet["scopes"]:
        paragraphs = split_numbered_paragraphs(
            scope["article_text"]
        )

        scope_digest = {
            "packet_id": scope["packet_id"],
            "income_type": scope["income_type"],
            "article_number": scope["article_number"],
            "article_title": scope["article_title"],
            "article_text_sha256": scope[
                "article_text_sha256"
            ],
            "candidate_rates": scope["candidate_rates"],
            "relevant_article_paragraphs": relevant_paragraphs(
                paragraphs,
                income_type=scope["income_type"],
            ),
            "protocol_scope_effects": scope[
                "protocol_scope_effects"
            ],
            "mli_effects": scope["mli_effects"],
            "review_questions": scope["review_questions"],
            "preliminary_findings": {
                "general_rate_structure": None,
                "special_exemptions_or_categories": None,
                "beneficial_owner_requirement": None,
                "protocol_effect": None,
                "mli_effect": None,
                "issues_requiring_human_confirmation": [],
            },
            "status": "awaiting_primary_review",
        }

        scopes.append(scope_digest)

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-belgium-evidence-digest-"
            "2026-08-05.1"
        ),
        "country": "BE",
        "country_name": "Belgie",
        "policy": {
            "source_excerpts_only": True,
            "no_automatic_legal_conclusion": True,
            "human_primary_review_required": True,
            "fail_closed": True,
        },
        "summary": {
            "scopes": len(scopes),
            "preliminary_findings_completed": 0,
            "approved_scopes": 0,
        },
        "scopes": scopes,
    }

    OUTPUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> None:
    payload = build_digest()

    print("Belgium evidence digest created.")
    print("Scopes:", payload["summary"]["scopes"])

    for scope in payload["scopes"]:
        print(
            scope["income_type"],
            "relevant paragraphs:",
            len(scope["relevant_article_paragraphs"]),
        )

    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
