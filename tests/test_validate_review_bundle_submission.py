from __future__ import annotations

import copy

import pytest

from taxtreat.tools.validate_review_bundle_submission import validate_review_bundle_submission


BUNDLE = "sha256:" + "a" * 64


def _pack() -> dict:
    return {
        "source_country": "AT",
        "review_bundle_id": BUNDLE,
        "rows": [{
            "review_bundle_id": BUNDLE,
            "partner_label": "Partner A",
            "income_type": "royalty",
            "review_ready": True,
            "review_blockers": [],
            "reviewer_decision": "approve",
            "reviewer_corrected_conclusion": None,
            "reviewer_evidence_references": [],
            "reviewer_name": "Reviewer",
            "reviewed_at": "2026-08-25T12:00:00Z",
            "independent_approval_status": "approved",
        }],
    }


def test_review_bundle_submission_accepts_fully_bound_approved_scope():
    result = validate_review_bundle_submission(_pack(), expected_review_bundle_id=BUNDLE)
    assert result["all_scopes_eligible"] is True
    assert result["eligible_scope_count"] == 1
    assert result["blocked_scope_count"] == 0
    assert result["policy"]["validation_does_not_release_country"] is True


def test_review_bundle_submission_rejects_wrong_bundle_identity():
    with pytest.raises(ValueError, match="identity does not match"):
        validate_review_bundle_submission(_pack(), expected_review_bundle_id="sha256:" + "b" * 64)
    with pytest.raises(ValueError, match="must be a sha256 identity"):
        validate_review_bundle_submission(_pack(), expected_review_bundle_id="legacy")


def test_review_bundle_submission_fails_closed_on_row_identity_or_approval_gaps():
    pack = _pack()
    row = pack["rows"][0]
    row["review_bundle_id"] = "sha256:" + "c" * 64
    row["review_ready"] = False
    row["review_blockers"] = ["chronology_unresolved"]
    row["reviewer_decision"] = "not_reviewed"
    row["reviewer_name"] = ""
    row["reviewed_at"] = None
    row["independent_approval_status"] = "not_started"
    result = validate_review_bundle_submission(pack, expected_review_bundle_id=BUNDLE)
    blockers = set(result["rows"][0]["promotion_blockers"])
    assert blockers >= {
        "row_review_bundle_identity_mismatch",
        "machine_review_scope_not_ready",
        "primary_review_not_approved",
        "reviewer_name_missing",
        "reviewed_at_missing",
        "independent_approval_missing",
    }
    assert result["all_scopes_eligible"] is False


def test_corrected_review_requires_conclusion_and_evidence_reference():
    pack = _pack()
    row = pack["rows"][0]
    row["reviewer_decision"] = "correct"
    row["reviewer_corrected_conclusion"] = ""
    row["reviewer_evidence_references"] = []
    result = validate_review_bundle_submission(pack, expected_review_bundle_id=BUNDLE)
    assert set(result["rows"][0]["promotion_blockers"]) >= {
        "corrected_conclusion_missing",
        "correction_evidence_reference_missing",
    }

    fixed = copy.deepcopy(pack)
    fixed["rows"][0]["reviewer_corrected_conclusion"] = "5% for qualifying branch"
    fixed["rows"][0]["reviewer_evidence_references"] = ["official-source:article-12"]
    result = validate_review_bundle_submission(fixed, expected_review_bundle_id=BUNDLE)
    assert result["all_scopes_eligible"] is True


def test_multi_variant_or_status_scope_requires_controlling_evidence_reference():
    for field, value in (
        ("unique_text_variant_count_machine", 2),
        ("machine_status_instrument_flag", True),
        ("nonstandard_article_number_machine", True),
    ):
        pack = _pack()
        pack["rows"][0][field] = value
        result = validate_review_bundle_submission(pack, expected_review_bundle_id=BUNDLE)
        row = result["rows"][0]
        assert row["controlling_evidence_selection_required"] is True
        assert "controlling_evidence_reference_missing" in row["promotion_blockers"]

        pack["rows"][0]["reviewer_evidence_references"] = ["official-source:controlling-text"]
        result = validate_review_bundle_submission(pack, expected_review_bundle_id=BUNDLE)
        assert result["all_scopes_eligible"] is True


def test_review_bundle_submission_requires_rows():
    pack = _pack()
    pack["rows"] = []
    with pytest.raises(ValueError, match="contains no rows"):
        validate_review_bundle_submission(pack, expected_review_bundle_id=BUNDLE)
