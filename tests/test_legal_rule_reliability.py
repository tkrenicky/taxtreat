import json
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
        "source_excerpt_hash": "a" * 64,
        "reviewer_id": "reviewer-1",
        "reviewed_at": date(2026, 8, 1),
        "approved_by": "approver-2",
        "approved_at": date(2026, 8, 2),
        "dataset_release": "2026.08.1",
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
        legal_rule("EXCLUDE", effect="exclude", rate=1),
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
    assert "exclusion rule must not contain a rate" in extra_issues
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
    issues = "\n".join(
        validate_legal_rules([base, missing, self_override, wrong_scope])
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
