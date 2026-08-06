from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

MATRIX = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_review_matrix.json"
)

WORKSHEET = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_worksheet.json"
)

OUTPUT_JSON = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_be_dividend_primary_review_pack.json"
)

OUTPUT_MD = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_be_dividend_primary_review_pack.md"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_scope(
    rows: list[dict[str, Any]],
    *,
    country: str,
    income_type: str,
) -> dict[str, Any]:
    matches = [
        row
        for row in rows
        if row.get("recipient_country") == country
        and row.get("income_type") == income_type
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one {country}/{income_type} scope, "
            f"found {len(matches)}."
        )

    return matches[0]


def build_review_pack() -> dict[str, Any]:
    matrix = read_json(MATRIX)
    worksheet = read_json(WORKSHEET)

    matrix_row = find_scope(
        matrix["rows"],
        country="BE",
        income_type="dividend",
    )

    worksheet_scope = next(
        scope
        for scope in worksheet["scopes"]
        if scope["income_type"] == "dividend"
    )

    base_treaty = matrix_row["base_treaty"]
    domestic_and_eu = matrix_row["domestic_and_eu"]
    protocols = matrix_row["protocols"]
    mli_effects = matrix_row["mli_effects"]

    return {
        "schema_version": 1,
        "dataset_release": (
            "batch-01-be-dividend-primary-review-pack-2026-08-06.1"
        ),
        "packet_id": matrix_row["packet_id"],
        "recipient_country": "BE",
        "recipient_country_name": "Belgie",
        "income_type": "dividend",
        "review_row_sha256": matrix_row["review_row_sha256"],
        "policy": {
            "human_primary_review_required": True,
            "independent_approval_required": True,
            "automatic_legal_conclusion_prohibited": True,
            "fail_closed": True,
        },
        "treaty": {
            "publication": base_treaty.get("publication"),
            "article_number": base_treaty.get("article_number"),
            "article_title": base_treaty.get("article_title"),
            "candidate_status": base_treaty.get(
                "candidate_status"
            ),
            "rate_candidates": base_treaty.get(
                "rate_candidates",
                [],
            ),
            "discarded_rate_candidates": base_treaty.get(
                "discarded_rate_candidates",
                [],
            ),
            "risk_flags": base_treaty.get("risk_flags", []),
            "source_id": base_treaty.get("source_id"),
            "verification_status": base_treaty.get(
                "verification_status"
            ),
        },
        "domestic_and_eu": {
            "domestic_rate_candidate": domestic_and_eu.get(
                "domestic_rate_candidate"
            ),
            "relief_candidate": domestic_and_eu.get(
                "relief_candidate"
            ),
            "relief_eligible_by_jurisdiction": (
                domestic_and_eu.get(
                    "relief_eligible_by_jurisdiction"
                )
            ),
            "consolidation_blockers": domestic_and_eu.get(
                "consolidation_blockers",
                [],
            ),
            "verification_status": domestic_and_eu.get(
                "verification_status"
            ),
        },
        "protocols": protocols,
        "mli_effects": mli_effects,
        "review_questions": worksheet_scope[
            "review_questions"
        ],
        "review_fields": {
            "treaty_rate_candidates_confirmed": None,
            "beneficial_owner_requirement_confirmed": None,
            "protocol_effects_confirmed": None,
            "mli_effects_confirmed": None,
            "domestic_rate_confirmed": None,
            "eu_relief_confirmed": None,
            "effective_date_confirmed": None,
            "anti_abuse_review_completed": None,
            "supporting_source_ids": [],
            "reviewer_notes": None,
            "proposed_rule_snapshot": None,
            "review_outcome": None,
        },
        "status": "awaiting_primary_review",
        "promotable_to_active_rules": False,
    }


def rate_lines(
    candidates: list[dict[str, Any]],
) -> list[str]:
    lines: list[str] = []

    for candidate in candidates:
        conditions = candidate.get("conditions", [])
        condition_text = "; ".join(
            f"{item.get('condition_type')} "
            f"{item.get('operator')} "
            f"{item.get('value')}"
            for item in conditions
        )

        lines.append(
            f"- **{candidate.get('rate')} %**"
            f" — {candidate.get('legal_basis')}"
            f" — {condition_text or 'bez strukturované podmínky'}"
        )

    return lines or ["- Nebyly nalezeny žádné kandidátní sazby."]


def build_markdown(payload: dict[str, Any]) -> str:
    treaty = payload["treaty"]
    domestic = payload["domestic_and_eu"]
    protocol_docs = payload["protocols"].get(
        "documents",
        [],
    )

    lines = [
        "# Primary legal review – CZ → BE / dividendy",
        "",
        f"**Packet:** `{payload['packet_id']}`",
        "",
        f"**Review hash:** `{payload['review_row_sha256']}`",
        "",
        "## 1. Základní smlouva",
        "",
        f"- Publikace: {treaty.get('publication')}",
        f"- Článek: {treaty.get('article_number')} "
        f"– {treaty.get('article_title')}",
        f"- Source ID: `{treaty.get('source_id')}`",
        f"- Stav: `{treaty.get('verification_status')}`",
        "",
        "### Kandidátní smluvní sazby",
        "",
        *rate_lines(treaty["rate_candidates"]),
        "",
        "## 2. České domácí právo",
        "",
        "```json",
        json.dumps(
            domestic["domestic_rate_candidate"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 3. EU osvobození",
        "",
        "```json",
        json.dumps(
            domestic["relief_candidate"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 4. Protokoly",
        "",
    ]

    if protocol_docs:
        for document in protocol_docs:
            lines.extend(
                [
                    f"- {document.get('label')}",
                    f"  - Source ID: "
                    f"`{document.get('source_id')}`",
                    f"  - Účinnost kandidáta: "
                    f"{document.get('candidate_effective_from')}",
                    f"  - Stav: "
                    f"`{document.get('verification_status')}`",
                ]
            )
    else:
        lines.append("- Nebyl nalezen žádný protokol.")

    lines.extend(
        [
            "",
            "## 5. MLI",
            "",
            "```json",
            json.dumps(
                payload["mli_effects"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## 6. Otázky pro primary review",
            "",
        ]
    )

    for index, question in enumerate(
        payload["review_questions"],
        start=1,
    ):
        lines.extend(
            [
                f"### {index}. {question}",
                "",
                "- Odpověď: `[ANO / NE]`",
                "- Právní odůvodnění:",
                "- Supporting source IDs:",
                "",
            ]
        )

    lines.extend(
        [
            "## 7. Výsledek primary review",
            "",
            "- Treaty rates confirmed:",
            "- Beneficial owner requirement confirmed:",
            "- Protocol effects confirmed:",
            "- MLI effects confirmed:",
            "- Czech domestic rate confirmed:",
            "- EU relief confirmed:",
            "- Effective dates confirmed:",
            "- Anti-abuse review completed:",
            "- Proposed rule snapshot:",
            "- Reviewer ID:",
            "- Reviewed at:",
            "- Review outcome:",
            "",
            "> Tento dokument nepředstavuje schválené právní "
            "pravidlo. Packet zůstává fail-closed až do "
            "nezávislého schválení.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    payload = build_review_pack()

    OUTPUT_JSON.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    OUTPUT_MD.write_text(
        build_markdown(payload),
        encoding="utf-8",
    )

    print("Belgium dividend primary-review pack created.")
    print("JSON:", OUTPUT_JSON.relative_to(ROOT))
    print("Markdown:", OUTPUT_MD.relative_to(ROOT))
    print("Status:", payload["status"])
    print(
        "Promotable:",
        payload["promotable_to_active_rules"],
    )


if __name__ == "__main__":
    main()
