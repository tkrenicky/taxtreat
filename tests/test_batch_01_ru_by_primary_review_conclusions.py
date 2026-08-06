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


def test_primary_review_is_complete_but_not_approved():
    payload = _payload()

    assert (
        payload["primary_legal_review_status"]
        == "completed"
    )
    assert (
        payload["independent_approval_status"]
        == "not_started"
    )
    assert payload["approval_eligible"] is False
    assert (
        payload["promotable_to_active_rules"]
        is False
    )
    assert payload["fail_closed"] is True


def test_all_six_primary_reviews_are_complete():
    findings = _payload()["findings"]

    assert len(findings) == 6
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


def test_five_suspended_scopes_resolve_to_fifteen():
    rows = [
        row
        for row in _payload()["findings"]
        if row["preliminary_treatment"]
        ["treatment_type"]
        == "czech_domestic_law_fallback"
    ]

    assert len(rows) == 5

    for row in rows:
        treatment = row["preliminary_treatment"]

        assert treatment["resolved_rate"] == 15.0
        assert (
            treatment["protective_rate_applicable"]
            is False
        )
        assert (
            treatment["protective_rate_candidate"]
            is None
        )


def test_belarus_royalty_resolves_to_five():
    row = next(
        row
        for row in _payload()["findings"]
        if row["packet_id"]
        == "CZ-BY-ROY-LEGAL-REVIEW"
    )
    treatment = row["preliminary_treatment"]

    assert treatment["resolved_rate"] == 5.0
    assert treatment["rate_candidate"] is None
    assert (
        treatment["beneficial_owner_condition"]
        is True
    )
    assert (
        treatment[
            "article_12_classification_required"
        ]
        is True
    )


def test_all_questions_are_resolved():
    payload = _payload()

    assert payload["unresolved_questions"] == []
    assert len(payload["resolved_questions"]) == 3


def test_evidence_covers_all_legal_layers():
    evidence = _payload()["primary_review_evidence"]

    assert set(evidence) == {
        "czech_income_tax_act",
        "russia_status_notice",
        "belarus_status_notice",
        "belarus_protocol",
    }


def test_status_still_blocks_promotion():
    for row in _payload()["findings"]:
        assert (
            row["status"]
            == "primary_review_completed_not_approved"
        )
