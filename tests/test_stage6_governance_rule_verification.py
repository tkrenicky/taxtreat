from __future__ import annotations

from datetime import date

from taxtreat.engine.legal_rule_engine import LegalRule
from taxtreat.engine.legal_rule_validator import (
    validate_legal_rules,
)


HASH = "a" * 64


def stage6_rule(**overrides):
    values = {
        "rule_id": "CZ-XX-DIV-TREATY-1",
        "income_type": "dividend",
        "source_country": "CZ",
        "recipient_country": "XX",
        "legal_instrument": "treaty",
        "legal_layer": "treaty",
        "article": 10,
        "rate": 10.0,
        "priority": 100,
        "effective_from": date(2000, 1, 1),
        "verification_status": "verified",
        "source_text": "Official treaty excerpt.",
        "source_id": "OFFICIAL-SOURCE",
        "source_url": "https://example.invalid/official",
        "source_excerpt_hash":
            "d5e312f81d727f886b1e98030ba027166846a8b77ed968c16c2b7476489abdec",
        "verification_authority":
            "stage6_governance_policy",
        "review_package_sha256": HASH,
        "approval_dataset_release":
            "stage6-production-approval-test",
        "approval_created_at": date(2026, 8, 11),
        "dataset_release":
            "stage6-production-rules-test",
        "evidence_source_ids": ["OFFICIAL-SOURCE"],
    }

    values.update(overrides)

    return LegalRule(**values)


def test_stage6_verified_rule_does_not_require_fake_second_human():
    rule = stage6_rule()

    issues = validate_legal_rules([rule])

    assert not any(
        "reviewer and approver must be independent"
        in issue
        for issue in issues
    )

    assert not any(
        "reviewer_id" in issue
        or "reviewed_at" in issue
        or "approved_by" in issue
        or "approved_at" in issue
        for issue in issues
    )


def test_stage6_verified_rule_requires_exact_package_hash():
    rule = stage6_rule(
        review_package_sha256="bad"
    )

    issues = validate_legal_rules([rule])

    assert any(
        "review_package_sha256 must be full SHA-256"
        in issue
        for issue in issues
    )


def test_stage6_verified_rule_requires_governance_approval_metadata():
    rule = stage6_rule(
        approval_dataset_release=None
    )

    issues = validate_legal_rules([rule])

    assert any(
        "approval_dataset_release"
        in issue
        for issue in issues
    )


def test_legacy_verified_rule_still_uses_legacy_provenance_rules():
    rule = stage6_rule(
        verification_authority=None,
        review_package_sha256=None,
        approval_dataset_release=None,
        approval_created_at=None,
        reviewer_id="human-a",
        reviewed_at=date(2026, 1, 1),
        approved_by="human-a",
        approved_at=date(2026, 1, 2),
    )

    issues = validate_legal_rules([rule])

    assert any(
        "reviewer and approver must be independent"
        in issue
        for issue in issues
    )
