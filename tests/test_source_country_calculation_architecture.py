from datetime import date

from taxtreat.countries.registry import get_country_config
from taxtreat.services.source_country_calculation import (
    build_source_country_withholding_tax_calculation,
    build_source_country_withholding_compliance_schedule,
)


def test_country_configs_select_calculation_strategy():
    assert (
        get_country_config("CZ").calculation_strategy
        == "czk_domestic"
    )
    assert (
        get_country_config("SK").calculation_strategy
        == "payment_currency_then_eur"
    )


def test_unregistered_source_direction_preserves_legacy_out_of_scope_helpers():
    calculation = build_source_country_withholding_tax_calculation(
        "AT",
        None,
        decision_status="OUT_OF_SCOPE",
        rate_percent=None,
    )
    schedule = build_source_country_withholding_compliance_schedule(
        "AT",
        date(2026, 8, 12),
        income_type="dividend",
        decision_status="OUT_OF_SCOPE",
        rate_percent=None,
    )

    assert calculation is None
    assert schedule["status"] == "PENDING_FINAL_TREATMENT"


def test_sk_outside_subject_has_no_zero_rate_calculation():
    result = build_source_country_withholding_tax_calculation(
        "SK",
        {"amount": "1000", "currency": "EUR"},
        decision_status="FINAL",
        rate_percent=None,
        tax_treatment="outside_subject_of_tax",
        transaction_date=date(2026, 8, 21),
    )

    assert result["status"] == "NOT_APPLICABLE"
    assert result["reason"] == "outside_subject_of_tax"
    assert result["rate_percent"] is None
    assert result["withholding_tax_transaction_currency"] is None
    assert result["withholding_tax_eur"] is None


def test_sk_outside_subject_has_no_remittance_or_notification_deadline():
    result = build_source_country_withholding_compliance_schedule(
        "SK",
        date(2026, 8, 21),
        income_type="dividend",
        decision_status="FINAL",
        rate_percent=None,
        tax_treatment="outside_subject_of_tax",
    )

    assert result["status"] == "NOT_APPLICABLE"
    assert result["notification_required"] is False
    assert result["tax_remittance_deadline"] is None
    assert result["notification_deadline"] is None


def test_domestic_exemption_remains_distinct_from_outside_subject():
    result = build_source_country_withholding_tax_calculation(
        "SK",
        {"amount": "1000", "currency": "EUR"},
        decision_status="FINAL",
        rate_percent=None,
        tax_treatment="domestic_exemption",
        transaction_date=date(2026, 8, 21),
    )

    assert result["status"] == "CALCULATED"
    assert result["rate_percent"] is None
    assert result["withholding_tax_eur"] == "0.00"


def test_literal_taxable_zero_rate_is_still_calculated_zero():
    result = build_source_country_withholding_tax_calculation(
        "SK",
        {"amount": "1000", "currency": "EUR"},
        decision_status="FINAL",
        rate_percent=0,
        tax_treatment="taxable_at_rate",
        transaction_date=date(2026, 8, 21),
    )

    assert result["status"] == "CALCULATED"
    assert result["rate_percent"] == "0"
    assert result["withholding_tax_eur"] == "0.00"


def test_core_calculation_dispatch_has_no_country_code_branching():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "taxtreat"
        / "services"
        / "source_country_calculation.py"
    ).read_text(encoding="utf-8")

    assert 'code == "CZ"' not in source
    assert 'code != "CZ"' not in source
    assert 'code == "SK"' not in source
    assert 'code != "SK"' not in source


def test_compliance_strategy_is_country_configured():
    assert get_country_config("CZ").compliance_strategy == "cz"
    assert (
        get_country_config("SK").compliance_strategy
        == "sk_monthly_section_43_11"
    )
