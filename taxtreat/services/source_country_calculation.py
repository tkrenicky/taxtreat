from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from taxtreat.countries.registry import get_country_config
from taxtreat.services.calculation import (
    build_withholding_compliance_schedule,
    build_withholding_tax_calculation,
)


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _next_month_day(value: date, day: int) -> date:
    year = value.year + (1 if value.month == 12 else 0)
    month = 1 if value.month == 12 else value.month + 1
    return date(year, month, day)


def _next_weekday(value: date) -> date:
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def build_source_country_withholding_compliance_schedule(
    source_country: str,
    transaction_date: date | str,
    *,
    income_type: str,
    decision_status: str,
    rate_percent: float | Decimal | None,
    tax_treatment: str | None = None,
    gross_amount_czk: float | Decimal | None = None,
    prior_same_type_monthly_amount_czk: float | Decimal | None = None,
) -> dict[str, Any]:
    code = str(source_country or "").upper()
    get_country_config(code)

    if code == "CZ":
        return build_withholding_compliance_schedule(
            transaction_date,
            income_type=income_type,
            decision_status=decision_status,
            rate_percent=rate_percent,
            tax_treatment=tax_treatment,
            gross_amount_czk=gross_amount_czk,
            prior_same_type_monthly_amount_czk=prior_same_type_monthly_amount_czk,
        )

    if code != "SK":
        raise ValueError(f"No compliance schedule configured for source country: {code}")

    reference_date = _parse_date(transaction_date)
    statutory_deadline = _next_month_day(reference_date, 15)
    weekend_adjusted_candidate = _next_weekday(statutory_deadline)
    base = {
        "schema_version": 2,
        "source_country": "SK",
        "status": "PENDING_FINAL_TREATMENT",
        "reference_date": reference_date.isoformat(),
        "reference_date_basis": "payment_remittance_or_credit_to_taxpayer",
        "tax_remittance_deadline": None,
        "notification_deadline": None,
        "statutory_deadline": statutory_deadline.isoformat(),
        "operational_deadline_candidate": weekend_adjusted_candidate.isoformat(),
        "notification_regime": None,
        "notification_required": None,
        "notification_form": "OZN4311v26",
        "notification_legal_basis": "§ 43 ods. 11 zákona č. 595/2003 Z. z.",
        "tax_remittance_legal_basis": "§ 43 ods. 11 zákona č. 595/2003 Z. z.",
        "withholding_timing_legal_basis": "§ 43 ods. 10 zákona č. 595/2003 Z. z.",
        "deadline_rule": "15th_day_of_following_calendar_month",
        "weekend_adjustment_candidate_applied": weekend_adjusted_candidate != statutory_deadline,
        "public_holiday_adjustment_not_modelled": True,
        "deadline_candidate_only": True,
        "ordinary_annual_wht_return_configured": False,
        "dividend_timing_review_required": False,
    }
    if tax_treatment is not None:
        base["tax_treatment"] = tax_treatment

    if decision_status != "FINAL" or (
        rate_percent is None and tax_treatment is None
    ):
        return base

    non_taxing = tax_treatment in {
        "exclusive_foreign_taxation",
        "domestic_exemption",
    }
    if non_taxing:
        rate = Decimal("0")
    else:
        try:
            rate = Decimal(str(rate_percent))
        except InvalidOperation as exc:
            raise ValueError("Rate must be a decimal number.") from exc

    if rate < 0 or rate > 100:
        raise ValueError("Final withholding-tax rate must be between 0 and 100.")

    if rate > 0:
        return {
            **base,
            "status": "REVIEW_DEADLINE_CALENDAR",
            "notification_regime": "monthly_withholding_section_43_11",
            "notification_required": True,
        }

    return {
        **base,
        "status": "REVIEW_NOTIFICATION_SCOPE",
        "notification_regime": "sk_zero_withholding_notification_scope_requires_review",
        "notification_required": None,
    }


def build_source_country_withholding_tax_calculation(
    source_country: str,
    transaction_amount: Mapping[str, Any] | None,
    *,
    decision_status: str,
    rate_percent: float | Decimal | None,
    tax_treatment: str | None = None,
) -> dict[str, Any] | None:
    code = str(source_country or "").upper()
    config = get_country_config(code)

    if code == "CZ":
        return build_withholding_tax_calculation(
            transaction_amount,
            decision_status=decision_status,
            rate_percent=rate_percent,
            tax_treatment=tax_treatment,
        )

    if code != "SK":
        raise ValueError(f"No tax calculation configured for source country: {code}")
    if transaction_amount is None:
        return None

    amount = transaction_amount.get("amount")
    currency = str(transaction_amount.get("currency") or "").upper()
    base = {
        "schema_version": 1,
        "source_country": "SK",
        "status": "NOT_CALCULATED",
        "gross_amount": None if amount is None else str(amount),
        "transaction_currency": currency,
        "tax_currency": config.currency,
        "rate_percent": None,
        "withholding_tax": None,
        "net_amount": None,
        "exchange_rate": None,
        "tax_treatment": tax_treatment,
    }

    if decision_status != "FINAL" or (
        rate_percent is None and tax_treatment is None
    ):
        return {
            **base,
            "reason": "final_rate_unavailable",
        }

    # The Slovak source-country package must not inherit Czech whole-crown,
    # CNB or CZK behavior. Final EUR rounding and foreign-currency conversion
    # policy remains an explicit release prerequisite and therefore fails closed.
    return {
        **base,
        "reason": "sk_final_calculation_rounding_and_fx_policy_not_released",
    }
