from __future__ import annotations

from datetime import date

from taxtreat.engine.layered_decision import evaluate_layered_rules
from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalRule,
    TaxTreatment,
    resolve_tax_treatment,
)


def _rule(**overrides):
    values = dict(
        rule_id="TEST-RULE",
        source_country="SK",
        recipient_country="CZ",
        income_type="dividend",
        legal_instrument="test",
        legal_layer="domestic",
        article=None,
        paragraph=None,
        rate=None,
        priority=0,
        conditions=[],
        effect="rate",
        tax_treatment=None,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        verification_status="verified",
        source_text="test",
        source_id="test",
        source_url="https://example.invalid",
        source_excerpt_hash="test",
        dataset_release="test-release",
    )
    values.update(overrides)
    return LegalRule(**values)


def test_outside_subject_is_distinct_from_domestic_exemption():
    assert (
        TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
        != TaxTreatment.DOMESTIC_EXEMPTION
    )
    assert (
        TaxTreatment.OUTSIDE_SUBJECT_OF_TAX.value
        == "outside_subject_of_tax"
    )
    assert (
        TaxTreatment.DOMESTIC_EXEMPTION.value
        == "domestic_exemption"
    )


def test_explicit_outside_subject_rule_has_no_rate():
    rule = _rule(
        rule_id="SK-OUTSIDE-SUBJECT",
        rate=None,
        tax_treatment=TaxTreatment.OUTSIDE_SUBJECT_OF_TAX,
    )

    assert (
        resolve_tax_treatment(rule)
        == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )

    result = evaluate_layered_rules(
        [rule],
        {
            "source_country": "SK",
            "recipient_country": "CZ",
            "income_type": "dividend",
        },
        as_of=date(2026, 8, 21),
    )

    assert result.status == DecisionStatus.FINAL
    assert (
        result.tax_treatment
        == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )
    assert result.rate is None
    assert result.candidate_rate is None


def test_eu_zero_rate_still_resolves_as_domestic_exemption():
    rule = _rule(
        rule_id="TEST-EU-RELIEF",
        legal_layer="eu_relief",
        rate=0.0,
        tax_treatment=None,
    )

    assert (
        resolve_tax_treatment(rule)
        == TaxTreatment.DOMESTIC_EXEMPTION
    )


def test_literal_treaty_zero_is_not_outside_subject():
    rule = _rule(
        rule_id="TEST-TREATY-ZERO",
        legal_layer="treaty",
        rate=0.0,
        tax_treatment=None,
    )

    assert (
        resolve_tax_treatment(rule)
        == TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION
    )
    assert (
        resolve_tax_treatment(rule)
        != TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )


def test_outside_subject_domestic_rule_beats_numeric_treaty_rate():
    domestic = _rule(
        rule_id="SK-DOMESTIC-OUTSIDE-SUBJECT",
        legal_layer="domestic",
        rate=None,
        tax_treatment=TaxTreatment.OUTSIDE_SUBJECT_OF_TAX,
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

    assert result.selected_rule_id == (
        "SK-DOMESTIC-OUTSIDE-SUBJECT"
    )
    assert (
        result.tax_treatment
        == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )
    assert result.rate is None
