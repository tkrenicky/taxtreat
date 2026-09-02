import json
import hashlib
from datetime import date

import pytest

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalCondition,
    LegalRule,
    _evaluate_condition,
    evaluate_legal_rules,
)
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.engine.legal_rule_validator import validate_legal_rules


SCOPE = {
    "income_type": "interest",
    "source_country": "CZ",
    "recipient_country": "CH",
}


def legal_rule(rule_id="RULE", **overrides):
    values = {
        "rule_id": rule_id,
        **SCOPE,
        "legal_instrument": "treaty",
        "rate": 5.0,
        "effective_from": date(2020, 1, 1),
        "verification_status": "verified",
        "source_id": "SRC-1",
        "source_url": "https://example.test/source",
        "source_text": "excerpt",
        "source_excerpt_hash": hashlib.sha256(b"excerpt").hexdigest(),
        "reviewer_id": "reviewer-1",
        "reviewed_at": date(2026, 8, 1),
        "approved_by": "approver-2",
        "approved_at": date(2026, 8, 2),
        "dataset_release": "2026.08.1",
        "evidence_source_ids": ["SRC-1"],
    }
    values.update(overrides)
    return LegalRule(**values)


def facts(**overrides):
    values = dict(SCOPE)
    values.update(overrides)
    return values


def test_effective_interval_and_scope_fail_closed():
    future = legal_rule(effective_from=date(2030, 1, 1))
    expired = legal_rule(effective_to=date(2025, 12, 31))
    wrong_country = legal_rule(recipient_country="AT")

    for candidate in (future, expired, wrong_country):
        result = evaluate_legal_rules(
            [candidate],
            facts(),
            as_of=date(2026, 8, 3),
        )
        assert result.status == DecisionStatus.OUT_OF_SCOPE


def test_condition_type_error_and_invalid_operator_are_explicit():
    assert _evaluate_condition(
        LegalCondition("x", "in", 3),
        {"x": "value"},
        {},
    ) == (False, None)
    with pytest.raises(ValueError, match="Unsupported"):
        _evaluate_condition(
            LegalCondition("x", "contains", "value"),
            {"x": "value"},
            {},
        )


def test_ambiguity_invalid_effect_missing_rate_and_failed_conditions():
    ambiguous = evaluate_legal_rules(
        [legal_rule("A", rate=5.0), legal_rule("B", rate=10.0)],
        facts(),
        as_of=date(2026, 8, 3),
    )
    invalid_effect = evaluate_legal_rules(
        [legal_rule(effect="unknown")],
        facts(),
        as_of=date(2026, 8, 3),
    )
    missing_rate = evaluate_legal_rules(
        [legal_rule(rate=None)],
        facts(),
        as_of=date(2026, 8, 3),
    )
    failed = evaluate_legal_rules(
        [
            legal_rule(
                conditions=[LegalCondition("beneficial_owner", "==", True)]
            )
        ],
        facts(beneficial_owner=False),
        as_of=date(2026, 8, 3),
    )

    assert "different outcomes" in ambiguous.explanation[0]
    assert "Unsupported" in invalid_effect.explanation[0]
    assert "no structured rate" in missing_rate.explanation[0]
    assert failed.failed_conditions == ["beneficial_owner"]
    assert failed.requires_review is True


def test_validator_enforces_complete_schema_and_approval():
    invalid = legal_rule(
        "",
        income_type="other",
        source_country="",
        recipient_country="",
        legal_instrument="unknown",
        legal_layer="unknown",
        effect="unknown",
        verification_status="invalid",
        priority=True,
        rate="five",
        conditions=[LegalCondition("", "bad", None, "user")],
    )
    issues = validate_legal_rules([invalid, invalid])
    combined = "\n".join(issues)
    for expected in (
        "Duplicate",
        "rule_id is required",
        "unsupported income_type",
        "country scope is incomplete",
        "unsupported legal_instrument",
        "unsupported legal_layer",
        "unsupported effect",
        "unsupported verification_status",
        "priority must be an integer",
        "condition fact is required",
        "unsupported condition operator",
        "unsupported condition fact_source",
    ):
        assert expected in combined

    missing_approval = legal_rule(source_id=None)
    assert "lacks provenance/approval" in "\n".join(
        validate_legal_rules([missing_approval])
    )

    bad_approval = legal_rule(
        "BAD-APPROVAL",
        reviewer_id="same-person",
        approved_by="same-person",
        source_excerpt_hash="short",
        source_url="http://example.test/source",
    )
    approval_issues = "\n".join(validate_legal_rules([bad_approval]))
    assert "reviewer and approver must be independent" in approval_issues
    assert "source_excerpt_hash must be full SHA-256" in approval_issues
    assert "source_url must use HTTPS" in approval_issues

    extra_invalid = [
        legal_rule("NEG", priority=-1),
        legal_rule("NONNUMERIC", rate="five"),
        legal_rule("RANGE", rate=101),
        legal_rule(
            "NON-TAXING-WITH-RATE",
            rate=5,
            tax_treatment="domestic_exemption",
        ),
        legal_rule(
            "DOMESTIC-RATE-WITH-TREATY-PERCENT",
            rate=5,
            tax_treatment="domestic_rate_applies",
        ),
        legal_rule("EXCLUDE", effect="exclude", rate=1),
        legal_rule("REVIEW-GATE-RATE", effect="review_gate", rate=1),
        legal_rule(
            "GATE-RATE",
            effect="eligibility_gate",
            rate=1,
            applies_to_layers=[],
        ),
        legal_rule(
            "GATE-LAYER",
            effect="eligibility_gate",
            rate=None,
            applies_to_layers=["unsupported"],
        ),
        legal_rule("HASH", source_excerpt_hash="b" * 64),
        legal_rule(
            "DATES",
            effective_from=date(2026, 1, 2),
            effective_to=date(2026, 1, 1),
        ),
    ]
    extra_issues = "\n".join(validate_legal_rules(extra_invalid))
    assert "priority cannot be negative" in extra_issues
    assert "rate must be numeric" in extra_issues
    assert "rate must be between" in extra_issues
    assert "non-taxing treatment must use structural rate 0" in extra_issues
    assert "domestic-rate treatment must not encode a treaty percentage" in extra_issues
    assert "exclusion rule must not contain a rate" in extra_issues
    assert "review gate must not contain a rate" in extra_issues
    assert "eligibility gate must not contain a rate" in extra_issues
    assert "eligibility gate must identify affected layers" in extra_issues
    assert "eligibility gate has unsupported target layers" in extra_issues
    assert "source_excerpt_hash does not match source_text" in extra_issues
    assert "effective_to precedes" in extra_issues


def test_validator_rejects_invalid_override_relationships():
    base = legal_rule("BASE", priority=10)
    missing = legal_rule("MISSING", overrides_rule_id="NOPE")
    self_override = legal_rule("SELF", overrides_rule_id="SELF")
    wrong_scope = legal_rule(
        "WRONG",
        recipient_country="AT",
        overrides_rule_id="BASE",
        priority=20,
    )
    valid_override = legal_rule(
        "VALID", overrides_rule_id="BASE", priority=5
    )
    issues = "\n".join(
        validate_legal_rules(
            [base, missing, self_override, wrong_scope, valid_override]
        )
    )
    assert "overridden rule does not exist" in issues
    assert "rule cannot override itself" in issues
    assert "override target has different scope" in issues
    assert "overriding rule must have higher precedence" in issues


def test_loader_rejects_non_list_duplicates_scope_and_invalid_rules(tmp_path):
    def write(name, payload):
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    with pytest.raises(ValueError, match="rules"):
        load_legal_rules(write("none.json", {}))

    raw = {
        "rule_id": "R",
        **SCOPE,
        "legal_instrument": "treaty",
        "rate": 5,
        "verification_status": "needs_review",
    }
    with pytest.raises(ValueError, match="Duplicate"):
        load_legal_rules(
            write(
                "duplicate.json",
                {
                    "country_pair": {
                        "source_country": "CZ",
                        "recipient_country": "CH",
                    },
                    "rules": [raw, raw],
                },
            )
        )

    with pytest.raises(ValueError, match="country_pair"):
        load_legal_rules(
            write(
                "scope.json",
                {
                    "country_pair": {
                        "source_country": "CZ",
                        "recipient_country": "AT",
                    },
                    "rules": [raw],
                },
            )
        )

    with pytest.raises(ValueError, match="Invalid legal-rule file"):
        load_legal_rules(
            write(
                "invalid.json",
                {
                    "country_pair": {
                        "source_country": "CZ",
                        "recipient_country": "CH",
                    },
                    "rules": [{**raw, "income_type": "other"}],
                },
            )
        )


def test_stage6_governance_verified_rule_is_valid_without_second_human():
    rule = legal_rule(
        "STAGE6-VALID",
        reviewer_id=None,
        reviewed_at=None,
        approved_by=None,
        approved_at=None,
        verification_authority="stage6_governance_policy",
        review_package_sha256="a" * 64,
        approval_dataset_release="stage6-production-approval-test",
        approval_created_at=date(2026, 8, 11),
    )

    issues = validate_legal_rules([rule])

    assert issues == []


def test_stage6_governance_requires_complete_governance_provenance():
    rule = legal_rule(
        "STAGE6-MISSING",
        reviewer_id=None,
        reviewed_at=None,
        approved_by=None,
        approved_at=None,
        verification_authority="stage6_governance_policy",
        review_package_sha256=None,
        approval_dataset_release=None,
        approval_created_at=None,
    )

    issues = "\n".join(
        validate_legal_rules([rule])
    )

    assert "Stage 6 verified rule lacks governance provenance" in issues
    assert "review_package_sha256" in issues
    assert "approval_dataset_release" in issues
    assert "approval_created_at" in issues


def test_stage6_governance_rejects_malformed_package_hash():
    rule = legal_rule(
        "STAGE6-BAD-HASH",
        reviewer_id=None,
        reviewed_at=None,
        approved_by=None,
        approved_at=None,
        verification_authority="stage6_governance_policy",
        review_package_sha256="bad",
        approval_dataset_release="stage6-production-approval-test",
        approval_created_at=date(2026, 8, 11),
    )

    issues = "\n".join(
        validate_legal_rules([rule])
    )

    assert (
        "review_package_sha256 must be full SHA-256"
        in issues
    )


def test_machine_validation_requires_semantic_remediation_approval_dataset():
    rule = legal_rule(
        "MACHINE-BAD-DATASET",
        reviewer_id=None,
        reviewed_at=None,
        approved_by=None,
        approved_at=None,
        verification_authority="semantic_remediation_machine_validation",
        review_package_sha256="a" * 64,
        approval_dataset_release="wrong-release",
        approval_created_at=date(2026, 9, 1),
    )

    issues = "\n".join(validate_legal_rules([rule]))

    assert "machine-validation approval dataset" in issues


def test_machine_validation_rejects_fabricated_human_provenance():
    rule = legal_rule(
        "MACHINE-HUMAN-PROVENANCE",
        reviewer_id="invented-reviewer",
        reviewed_at=date(2026, 9, 1),
        approved_by=None,
        approved_at=None,
        verification_authority="semantic_remediation_machine_validation",
        review_package_sha256="b" * 64,
        approval_dataset_release=(
            "stage6-semantic-remediation-machine-validation-2026-09-01.1"
        ),
        approval_created_at=date(2026, 9, 1),
    )

    issues = "\n".join(validate_legal_rules([rule]))

    assert "must not fabricate human reviewer/approver provenance" in issues
