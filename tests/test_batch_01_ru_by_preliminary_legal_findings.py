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
    payload = _payload()
    findings = payload["findings"]

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

    assert all(
        row["status"]
        == "preliminary_not_approved"
        for row in payload["findings"]
    )


def test_russia_uses_domestic_fallback():
    rows = [
        row
        for row in _payload()["findings"]
        if row["recipient_country"] == "RU"
    ]

    assert len(rows) == 3

    for row in rows:
        assert (
            row["treaty_application_status"]
            == "suspended"
        )
        assert (
            row["preliminary_treatment"]
            ["treatment_type"]
            == "czech_domestic_law_fallback"
        )
        assert (
            row["preliminary_treatment"]
            ["standard_rate_candidate"]
            == 15.0
        )
        assert (
            row["preliminary_treatment"]
            ["protective_rate_automatically_applied"]
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

        assert (
            row["treaty_application_status"]
            == "temporarily_suspended"
        )
        assert (
            row["preliminary_treatment"]
            ["standard_rate_candidate"]
            == 15.0
        )


def test_belarus_royalty_retains_treaty_candidate():
    row = next(
        row
        for row in _payload()["findings"]
        if row["packet_id"]
        == "CZ-BY-ROY-LEGAL-REVIEW"
    )

    assert (
        row["treaty_application_status"]
        == "not_suspended"
    )
    assert (
        row["preliminary_treatment"]
        ["treatment_type"]
        == "treaty_rate_candidate"
    )
    assert (
        row["preliminary_treatment"]
        ["rate_candidate"]
        == 5.0
    )


def test_protective_rate_never_applied_automatically():
    domestic_rows = [
        row
        for row in _payload()["findings"]
        if (
            row["preliminary_treatment"]
            ["treatment_type"]
            == "czech_domestic_law_fallback"
        )
    ]

    assert len(domestic_rows) == 5

    for row in domestic_rows:
        treatment = row[
            "preliminary_treatment"
        ]

        assert (
            treatment["protective_rate_candidate"]
            == 35.0
        )
        assert (
            treatment[
                "protective_rate_automatically_applied"
            ]
            is False
        )


def test_open_questions_block_approval():
    questions = _payload()[
        "unresolved_questions"
    ]

    assert len(questions) == 3
    assert all(
        row["required_before_approval"]
        is True
        for row in questions
    )
