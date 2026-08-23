from taxtreat.services.calculation import build_withholding_compliance_schedule
from taxtreat.services.source_country_calculation import (
    build_source_country_withholding_compliance_schedule,
    build_source_country_withholding_tax_calculation,
)


def test_cz_compliance_wrapper_preserves_legacy_output_exactly():
    kwargs = dict(
        income_type="interest",
        decision_status="REVIEW_REQUIRED",
        rate_percent=None,
    )
    legacy = build_withholding_compliance_schedule("2026-02-10", **kwargs)
    routed = build_source_country_withholding_compliance_schedule(
        "CZ", "2026-02-10", **kwargs
    )
    assert routed == legacy


def test_sk_withheld_tax_uses_section_43_11_and_moves_sunday_to_next_working_day():
    schedule = build_source_country_withholding_compliance_schedule(
        "SK",
        "2026-02-10",
        income_type="interest",
        decision_status="FINAL",
        rate_percent=10,
    )

    assert schedule["source_country"] == "SK"
    assert schedule["statutory_deadline"] == "2026-03-15"
    assert schedule["operational_deadline"] == "2026-03-16"
    assert schedule["tax_remittance_deadline"] == "2026-03-16"
    assert schedule["notification_deadline"] == "2026-03-16"
    assert schedule["status"] == "READY"
    assert schedule["deadline_adjusted"] is True
    assert schedule["notification_form"] == "OZN4311v26"
    assert schedule["notification_regime"] == "monthly_withholding_section_43_11"
    assert schedule["notification_legal_basis"].startswith("§ 43 ods. 11")
    assert schedule["deadline_adjustment_legal_basis"].startswith("§ 27 ods. 4")
    serialized = repr(schedule)
    assert "586/1992" not in serialized
    assert "§ 38d" not in serialized


def test_sk_2026_september_15_is_not_day_of_rest_under_section_4b():
    schedule = build_source_country_withholding_compliance_schedule(
        "SK",
        "2026-08-10",
        income_type="royalty",
        decision_status="FINAL",
        rate_percent=10,
    )
    assert schedule["statutory_deadline"] == "2026-09-15"
    assert schedule["operational_deadline"] == "2026-09-15"
    assert schedule["deadline_adjusted"] is False


def test_sk_2027_september_15_is_day_of_rest_again():
    schedule = build_source_country_withholding_compliance_schedule(
        "SK",
        "2027-08-10",
        income_type="royalty",
        decision_status="FINAL",
        rate_percent=10,
    )
    assert schedule["statutory_deadline"] == "2027-09-15"
    assert schedule["operational_deadline"] == "2027-09-16"
    assert schedule["deadline_adjusted"] is True


def test_sk_zero_withholding_scope_fails_closed_instead_of_reusing_czech_annual_notice():
    schedule = build_source_country_withholding_compliance_schedule(
        "SK",
        "2026-02-10",
        income_type="royalty",
        decision_status="FINAL",
        rate_percent=0,
    )

    assert schedule["status"] == "REVIEW_NOTIFICATION_SCOPE"
    assert schedule["notification_required"] is None
    assert schedule["notification_deadline"] is None
    assert schedule["notification_regime"] == (
        "sk_zero_withholding_notification_scope_requires_review"
    )
    serialized = repr(schedule)
    assert "§ 38da" not in serialized
    assert "586/1992" not in serialized


def test_sk_eur_withholding_is_calculated_directly_and_rounded_half_up():
    result = build_source_country_withholding_tax_calculation(
        "SK",
        {"amount": "1000", "currency": "EUR"},
        decision_status="FINAL",
        rate_percent=10,
        transaction_date="2026-08-19",
    )

    assert result["status"] == "CALCULATED"
    assert result["withholding_tax_transaction_currency"] == "100.00"
    assert result["withholding_tax_eur"] == "100.00"
    assert result["exchange_rate"] is None
    assert result["rounding_policy"] == "section_47_two_decimal_half_up"


def test_sk_foreign_currency_calculates_tax_first_then_converts_withheld_tax_to_eur():
    result = build_source_country_withholding_tax_calculation(
        "SK",
        {
            "amount": "1000",
            "currency": "USD",
            "exchange_rate": {
                "source": "ECB",
                "currency": "USD",
                "foreign_units_per_eur": "1.1591",
                "effective_date": "2026-08-19",
                "source_url": "https://nbs.sk/",
            },
        },
        decision_status="FINAL",
        rate_percent=10,
        transaction_date="2026-08-19",
    )

    assert result["status"] == "CALCULATED"
    assert result["calculation_sequence"] == (
        "calculate_withholding_in_payment_currency_then_convert_withheld_tax_to_eur"
    )
    assert result["withholding_tax_transaction_currency"] == "100.00"
    assert result["withholding_tax_eur"] == "86.27"
    assert result["exchange_rate"]["foreign_units_per_eur"] == "1.1591"
    assert result["exchange_rate"]["quotation"] == "foreign_currency_units_per_1_eur"
    assert "gross_amount_eur" not in result


def test_sk_foreign_currency_rejects_cnb_and_wrong_effective_date():
    cnb = build_source_country_withholding_tax_calculation(
        "SK",
        {
            "amount": "1000",
            "currency": "USD",
            "exchange_rate": {
                "source": "CNB",
                "currency": "USD",
                "foreign_units_per_eur": "1.1591",
                "effective_date": "2026-08-19",
            },
        },
        decision_status="FINAL",
        rate_percent=10,
        transaction_date="2026-08-19",
    )
    assert cnb["status"] == "NOT_CALCULATED"
    assert cnb["reason"] == "sk_exchange_rate_source_not_ecb_or_nbs"

    wrong_date = build_source_country_withholding_tax_calculation(
        "SK",
        {
            "amount": "1000",
            "currency": "USD",
            "exchange_rate": {
                "source": "NBS",
                "currency": "USD",
                "foreign_units_per_eur": "1.1591",
                "effective_date": "2026-08-18",
            },
        },
        decision_status="FINAL",
        rate_percent=10,
        transaction_date="2026-08-19",
    )
    assert wrong_date["reason"] == "sk_exchange_rate_date_mismatch"


def test_sk_missing_fx_evidence_fails_closed_without_czk_or_cnb_fallback():
    result = build_source_country_withholding_tax_calculation(
        "SK",
        {"amount": "1000", "currency": "USD"},
        decision_status="FINAL",
        rate_percent=10,
        transaction_date="2026-08-19",
    )

    assert result["source_country"] == "SK"
    assert result["status"] == "NOT_CALCULATED"
    assert result["tax_currency"] == "EUR"
    assert result["reason"] == "sk_ecb_nbs_exchange_rate_evidence_missing"
    serialized = repr(result)
    assert "CNB" not in serialized
    assert "CZK" not in serialized
    assert "whole_crown" not in serialized
