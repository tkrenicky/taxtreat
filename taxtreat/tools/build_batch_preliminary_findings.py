from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

BELGIUM = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_preliminary_findings.json"
)

DOSSIERS = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_country_dossiers.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_preliminary_findings.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_findings() -> dict[str, Any]:
    belgium = read_json(BELGIUM)
    dossiers = read_json(DOSSIERS)

    findings = list(belgium["findings"])

    nl = next(
        country
        for country in dossiers["countries"]
        if country["recipient_country"] == "NL"
    )

    nl_interest = next(
        scope
        for scope in nl["scopes"]
        if scope["income_type"] == "interest"
    )

    findings.append(
        {
            "packet_id": nl_interest["packet_id"],
            "recipient_country": "NL",
            "income_type": "interest",
            "treaty_findings": {
                "source_state_rate": 0.0,
                "taxing_right": (
                    "Interest arising in one contracting state and paid "
                    "to a resident of the other contracting state is "
                    "taxable only in the recipient state."
                ),
                "rate_scope": "general",
                "conditions": [
                    (
                        "recipient is resident in the other contracting "
                        "state"
                    ),
                    (
                        "the debt claim is not effectively connected with "
                        "a permanent establishment in the source state"
                    ),
                ],
                "pe_exception_applies": True,
            },
            "protocol_preliminary_finding": {
                "effect": "definition_change_only",
                "rate_effect": "none identified",
                "source_ids": [
                    "CZ-MF-NL-45D279EE7770",
                    "CZ-MF-NL-7CAD483C3F1A",
                ],
            },
            "mli_preliminary_finding": {
                "effect": "Article 7(1) PPT",
                "effective_from": "2021-01-01",
                "source_id": "CZ-MF-NL-0210508FF125",
            },
            "data_quality_issues": [
                {
                    "code": "article_text_truncated",
                    "severity": "medium",
                    "detail": (
                        "Stored Article 11 paragraph 3 ends after "
                        "'V takovém případě se použije'. The complete "
                        "cross-reference must be checked against the "
                        "official instrument before final approval."
                    ),
                    "affects_general_rate_conclusion": False,
                }
            ],
            "domestic_and_eu_review_required": True,
            "human_confirmation_required": True,
            "review_outcome": None,
            "status": "preliminary_findings_only",
        }
    )

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-preliminary-findings-"
            "2026-08-05.1"
        ),
        "policy": {
            "source_derived_preliminary_findings": True,
            "not_a_completed_legal_review": True,
            "independent_approval_required": True,
            "fail_closed": True,
        },
        "summary": {
            "total_scopes": 30,
            "preliminary_findings_completed": len(findings),
            "preliminary_completion_percent": round(
                len(findings) / 30 * 100,
                1,
            ),
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

    print("Batch preliminary findings created.")
    print(
        "Preliminary findings:",
        payload["summary"]["preliminary_findings_completed"],
        "/",
        payload["summary"]["total_scopes"],
    )
    print(
        "Content progress:",
        f'{payload["summary"]["preliminary_completion_percent"]}%',
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
