from __future__ import annotations

from datetime import date

from taxtreat.engine.layered_decision import evaluate_layered_rules
from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalRule,
    TaxTreatment,
)


def _rule(**overrides):
    values = dict(
        rule_id="TEST-RULE",
        source_country="SK",
        recipient_country="CZ",
        income_type="dividend",
        legal_layer="domestic",
        legal_instrument="test",
        effect="rate",
        rate=None,
        priority=0,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        conditions=[],
        verification_status="verified",
        dataset_release="test-release",
        source_id="test-source",
        source_url="https://example.invalid",
        source_text="test",
        source_excerpt_hash="test-hash",
        article=None,
        paragraph=None,
    )
    values.update(overrides)
    return LegalRule(**values)


def test_domestic_non_rate_treatment_beats_lower_treaty_rate():
    domestic = _rule(
        rule_id="SK-DOMESTIC-OUTSIDE-SUBJECT",
        legal_layer="domestic",
        rate=None,
        tax_treatment=TaxTreatment.DOMESTIC_EXEMPTION,
    )

    treaty = _rule(
        rule_id="SK-CZ-DIV-TREATY-5",
        legal_layer="treaty",
        rate=5.0,
        tax_treatment=TaxTreatment.TAXABLE_AT_RATE,
    )

    result = evaluate_layered_rules(
        [treaty, domestic],
        {
            "source_country": "SK",
            "recipient_country": "CZ",
            "income_type": "dividend",
        },
        as_of=date(2026, 8, 21),
    )

    assert result.status == DecisionStatus.FINAL
    assert result.selected_rule_id == "SK-DOMESTIC-OUTSIDE-SUBJECT"
    assert result.tax_treatment == TaxTreatment.DOMESTIC_EXEMPTION

    # Critical semantic distinction:
    # outside subject is N/A, not a synthetic 0% WHT rate.
    assert result.rate is None
    assert result.candidate_rate is None


def test_literal_zero_percent_rate_remains_zero_percent():
    zero = _rule(
        rule_id="TEST-LITERAL-ZERO",
        legal_layer="treaty",
        rate=0.0,
        tax_treatment=TaxTreatment.TAXABLE_AT_RATE,
    )

    fallback = _rule(
        rule_id="TEST-FALLBACK",
        legal_layer="domestic",
        rate=19.0,
        tax_treatment=TaxTreatment.TAXABLE_AT_RATE,
    )

    result = evaluate_layered_rules(
        [fallback, zero],
        {
            "source_country": "SK",
            "recipient_country": "CZ",
            "income_type": "dividend",
        },
        as_of=date(2026, 8, 21),
    )

    assert result.status == DecisionStatus.FINAL
    assert result.selected_rule_id == "TEST-LITERAL-ZERO"
    assert result.tax_treatment == TaxTreatment.TAXABLE_AT_RATE
    assert result.rate == 0.0
    assert result.candidate_rate == 0.0


def test_numeric_rate_comparison_is_unchanged_when_all_candidates_are_taxable():
    domestic = _rule(
        rule_id="TEST-DOMESTIC-19",
        legal_layer="domestic",
        rate=19.0,
        tax_treatment=TaxTreatment.TAXABLE_AT_RATE,
    )

    treaty = _rule(
        rule_id="TEST-TREATY-10",
        legal_layer="treaty",
        rate=10.0,
        tax_treatment=TaxTreatment.TAXABLE_AT_RATE,
    )

    result = evaluate_layered_rules(
        [domestic, treaty],
        {
            "source_country": "SK",
            "recipient_country": "CZ",
            "income_type": "dividend",
        },
        as_of=date(2026, 8, 21),
    )

    assert result.status == DecisionStatus.FINAL
    assert result.selected_rule_id == "TEST-TREATY-10"
    assert result.rate == 10.0
