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


def test_sk_withheld_tax_uses_section_43_11_monthly_deadline_not_czech_schedule():
    schedule = build_source_country_withholding_compliance_schedule(
        "SK",
        "2026-02-10",
        income_type="interest",
        decision_status="FINAL",
        rate_percent=10,
    )

    assert schedule["source_country"] == "SK"
    assert schedule["statutory_deadline"] == "2026-03-15"
    assert schedule["tax_remittance_deadline"] == "2026-03-16"
    assert schedule["notification_deadline"] == "2026-03-16"
    assert schedule["notification_form"] == "OZN4311v26"
    assert schedule["notification_regime"] == "monthly_withholding_section_43_11"
    assert schedule["notification_legal_basis"].startswith("§ 43 ods. 11")
    serialized = repr(schedule)
    assert "586/1992" not in serialized
    assert "§ 38d" not in serialized
    assert "annual" not in schedule["notification_regime"]


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


def test_sk_final_tax_calculation_never_inherits_cnb_czk_rounding_policy():
    result = build_source_country_withholding_tax_calculation(
        "SK",
        {"amount": "1000", "currency": "USD"},
        decision_status="FINAL",
        rate_percent=10,
    )

    assert result["source_country"] == "SK"
    assert result["status"] == "NOT_CALCULATED"
    assert result["tax_currency"] == "EUR"
    assert result["reason"] == "sk_final_calculation_rounding_and_fx_policy_not_released"
    serialized = repr(result)
    assert "CNB" not in serialized
    assert "CZK" not in serialized
    assert "whole_crown" not in serialized
