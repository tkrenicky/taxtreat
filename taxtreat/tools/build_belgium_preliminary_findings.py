from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DIGEST = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_evidence_digest.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_preliminary_findings.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_findings() -> dict[str, Any]:
    digest = read_json(DIGEST)

    scopes = {
        item["income_type"]: item
        for item in digest["scopes"]
    }

    findings = [
        {
            "packet_id": scopes["dividend"]["packet_id"],
            "income_type": "dividend",
            "treaty_findings": {
                "general_structure": (
                    "Source-state taxation is permitted, subject to "
                    "reduced treaty ceilings where the recipient is the "
                    "beneficial owner."
                ),
                "rates": [
                    {
                        "rate": 5.0,
                        "conditions": [
                            "recipient is the beneficial owner",
                            (
                                "recipient is a company, including a "
                                "partnership, directly or indirectly "
                                "holding at least 25% of the capital of "
                                "the paying company"
                            ),
                        ],
                    },
                    {
                        "rate": 15.0,
                        "conditions": [
                            "recipient is the beneficial owner",
                            (
                                "residual rate for cases not qualifying "
                                "for the 5% participation rate"
                            ),
                        ],
                    },
                ],
                "pe_exception_applies": True,
                "excess_payment_limitation": False,
            },
            "protocol_preliminary_finding": (
                "The 2015 protocol candidate indicates no amendment "
                "to Article 10."
            ),
            "mli_preliminary_finding": (
                "Article 7(1) PPT applies to Czech-source withholding "
                "tax from 1 January 2021."
            ),
            "domestic_and_eu_review_required": True,
            "human_confirmation_required": True,
            "review_outcome": None,
            "status": "preliminary_findings_only",
        },
        {
            "packet_id": scopes["interest"]["packet_id"],
            "income_type": "interest",
            "treaty_findings": {
                "general_rate": 10.0,
                "general_rate_conditions": [
                    "recipient is the beneficial owner",
                ],
                "source_state_exemptions": [
                    (
                        "interest on trade receivables arising from "
                        "deferred payment for goods or services"
                    ),
                    (
                        "interest on loans or credits provided, "
                        "guaranteed or insured by public export-support "
                        "bodies"
                    ),
                    (
                        "interest on non-bearer loans provided by a "
                        "banking enterprise"
                    ),
                    (
                        "interest on non-bearer deposits with a banking "
                        "enterprise"
                    ),
                    (
                        "interest paid to the other contracting state, "
                        "its political subdivisions or local authorities"
                    ),
                ],
                "source_state_exemption_rate": 0.0,
                "pe_exception_applies": True,
                "excess_payment_limitation": True,
            },
            "protocol_preliminary_finding": (
                "The 2015 protocol candidate indicates no amendment "
                "to Article 11."
            ),
            "mli_preliminary_finding": (
                "Article 7(1) PPT applies to Czech-source withholding "
                "tax from 1 January 2021."
            ),
            "domestic_and_eu_review_required": True,
            "human_confirmation_required": True,
            "review_outcome": None,
            "status": "preliminary_findings_only",
        },
        {
            "packet_id": scopes["royalty"]["packet_id"],
            "income_type": "royalty",
            "treaty_findings": {
                "rates": [
                    {
                        "rate": 5.0,
                        "categories": [
                            (
                                "use of, or right to use, industrial, "
                                "commercial or scientific equipment"
                            ),
                        ],
                        "conditions": [
                            "recipient is the beneficial owner",
                        ],
                    },
                    {
                        "rate": 10.0,
                        "categories": [
                            "copyright",
                            "literary, artistic or scientific works",
                            "films and broadcasting recordings",
                            "software",
                            "patents",
                            "trademarks",
                            "designs or models",
                            "plans",
                            "secret formulas or processes",
                            "know-how",
                        ],
                        "conditions": [
                            "recipient is the beneficial owner",
                        ],
                    },
                ],
                "pe_exception_applies": True,
                "excess_payment_limitation": True,
            },
            "protocol_preliminary_finding": (
                "The 2015 protocol candidate indicates no amendment "
                "to Article 12."
            ),
            "mli_preliminary_finding": (
                "Article 7(1) PPT applies to Czech-source withholding "
                "tax from 1 January 2021."
            ),
            "domestic_and_eu_review_required": True,
            "human_confirmation_required": True,
            "review_outcome": None,
            "status": "preliminary_findings_only",
        },
    ]

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-belgium-preliminary-findings-"
            "2026-08-05.1"
        ),
        "country": "BE",
        "country_name": "Belgie",
        "policy": {
            "source_derived_preliminary_findings": True,
            "not_a_completed_legal_review": True,
            "independent_approval_required": True,
            "fail_closed": True,
        },
        "summary": {
            "scopes": 3,
            "preliminary_findings_completed": 3,
            "completed_primary_reviews": 0,
            "approved_scopes": 0,
        },
        "findings": findings,
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
    payload = build_findings()

    print("Belgium preliminary findings created.")
    print(
        "Preliminary findings:",
        payload["summary"]["preliminary_findings_completed"],
    )
    print(
        "Completed primary reviews:",
        payload["summary"]["completed_primary_reviews"],
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
