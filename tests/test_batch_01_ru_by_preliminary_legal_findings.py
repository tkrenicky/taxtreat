from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "batch_01_ru_by"
    / "preliminary_legal_findings.json"
)


def _payload():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_six_scopes_are_present():
    findings = _payload()["findings"]

    assert len(findings) == 6
    assert len({
        row["packet_id"]
        for row in findings
    }) == 6


def test_dataset_remains_fail_closed():
    payload = _payload()

    assert payload["fail_closed"] is True
    assert payload["approval_eligible"] is False
    assert (
        payload["promotable_to_active_rules"]
        is False
    )
    assert (
        payload["independent_approval_status"]
        == "not_started"
    )


def test_russia_uses_domestic_fallback():
    rows = [
        row
        for row in _payload()["findings"]
        if row["recipient_country"] == "RU"
    ]

    assert len(rows) == 3

    for row in rows:
        treatment = row[
            "preliminary_treatment"
        ]

        assert (
            row["treaty_application_status"]
            == "suspended"
        )
        assert (
            treatment["treatment_type"]
            == "czech_domestic_law_fallback"
        )
        assert (
            treatment["standard_rate_candidate"]
            == 15.0
        )
        assert treatment["resolved_rate"] == 15.0
        assert (
            treatment["protective_rate_applicable"]
            is False
        )


def test_belarus_dividend_and_interest_use_fallback():
    rows = {
        row["income_type"]: row
        for row in _payload()["findings"]
        if row["recipient_country"] == "BY"
    }

    for income_type in ("dividend", "interest"):
        row = rows[income_type]
        treatment = row[
            "preliminary_treatment"
        ]

        assert (
            row["treaty_application_status"]
            == "temporarily_suspended"
        )
        assert treatment["resolved_rate"] == 15.0
        assert (
            treatment["protective_rate_applicable"]
            is False
        )


def test_belarus_royalty_retains_treaty_treatment():
    row = next(
        row
        for row in _payload()["findings"]
        if row["packet_id"]
        == "CZ-BY-ROY-LEGAL-REVIEW"
    )

    treatment = row[
        "preliminary_treatment"
    ]

    assert (
        row["treaty_application_status"]
        == "not_suspended"
    )
    assert (
        treatment["treatment_type"]
        == "treaty_rate_candidate"
    )
    assert treatment["resolved_rate"] == 5.0
    assert (
        treatment["beneficial_owner_condition"]
        is True
    )


def test_primary_questions_are_resolved():
    payload = _payload()

    assert payload["unresolved_questions"] == []
    assert len(
        payload["resolved_questions"]
    ) == 3


def test_independent_review_still_blocks_approval():
    findings = _payload()["findings"]

    assert all(
        row["primary_review_status"]
        == "completed"
        for row in findings
    )
    assert all(
        row["independent_review_status"]
        == "not_started"
        for row in findings
    )
    assert all(
        row["status"]
        == "primary_review_completed_not_approved"
        for row in findings
    )
