from datetime import date

from taxtreat.engine.layered_decision import evaluate_layered_rules
from taxtreat.engine.legal_rule_engine import LegalRule, TaxTreatment


def _rule(rule_id: str, layer: str, treatment: TaxTreatment) -> LegalRule:
    return LegalRule(
        rule_id=rule_id,
        income_type="dividend",
        source_country="CZ",
        recipient_country="DE",
        legal_instrument="domestic_law" if layer == "eu_relief" else "treaty",
        legal_layer=layer,
        rate=0.0,
        tax_treatment=treatment,
        verification_status="verified",
        dataset_release="test-release",
    )


def test_domestic_exemption_is_primary_basis_when_treaty_also_gives_zero():
    result = evaluate_layered_rules(
        [
            _rule(
                "CZ-DE-DIVIDEND-TREATY-ZERO",
                "treaty",
                TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION,
            ),
            _rule(
                "CZ-DE-DIVIDEND-SECTION19",
                "eu_relief",
                TaxTreatment.DOMESTIC_EXEMPTION,
            ),
        ],
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "DE",
        },
        as_of=date(2026, 8, 20),
    )

    assert result.status.value == "FINAL"
    assert result.selected_rule_id == "CZ-DE-DIVIDEND-SECTION19"
    assert result.tax_treatment == TaxTreatment.DOMESTIC_EXEMPTION
    assert result.rate is None
