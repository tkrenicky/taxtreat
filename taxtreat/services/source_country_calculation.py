from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping

from taxtreat.countries.registry import get_country_config
from taxtreat.services.calculation import (
    build_withholding_compliance_schedule,
    build_withholding_tax_calculation,
)


EUR_CENT = Decimal("0.01")


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _next_month_day(value: date, day: int) -> date:
    year = value.year + (1 if value.month == 12 else 0)
    month = 1 if value.month == 12 else value.month + 1
    return date(year, month, day)


def _easter_sunday(year: int) -> date:
    """Gregorian Easter date, used only to derive Slovak movable holidays."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _sk_non_working_holidays(year: int) -> set[date]:
    easter = _easter_sunday(year)
    holidays = {
        date(year, 1, 1),
        date(year, 1, 6),
        easter - timedelta(days=2),
        easter + timedelta(days=1),
        date(year, 5, 1),
        date(year, 7, 5),
        date(year, 8, 29),
        date(year, 11, 1),
        date(year, 12, 24),
        date(year, 12, 25),
        date(year, 12, 26),
    }
    # Transitional rule in Act No. 241/1993 Coll.: in 2026, 8 May and
    # 15 September are not days of rest. Outside 2026 they are included.
    if year != 2026:
        holidays.update({date(year, 5, 8), date(year, 9, 15)})
    return holidays


def _next_sk_business_day(value: date) -> date:
    holidays = _sk_non_working_holidays(value.year)
    while value.weekday() >= 5 or value in holidays:
        value += timedelta(days=1)
        if value.year != next(iter(holidays)).year:
            holidays = _sk_non_working_holidays(value.year)
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
    operational_deadline = _next_sk_business_day(statutory_deadline)
    base = {
        "schema_version": 3,
        "source_country": "SK",
        "status": "PENDING_FINAL_TREATMENT",
        "reference_date": reference_date.isoformat(),
        "reference_date_basis": "payment_remittance_or_credit_to_taxpayer",
        "tax_remittance_deadline": None,
        "notification_deadline": None,
        "statutory_deadline": statutory_deadline.isoformat(),
        "operational_deadline": operational_deadline.isoformat(),
        "notification_regime": None,
        "notification_required": None,
        "notification_form": "OZN4311v26",
        "notification_legal_basis": "§ 43 ods. 11 zákona č. 595/2003 Z. z.",
        "tax_remittance_legal_basis": "§ 43 ods. 11 zákona č. 595/2003 Z. z.",
        "withholding_timing_legal_basis": "§ 43 ods. 10 zákona č. 595/2003 Z. z.",
        "deadline_adjustment_legal_basis": "§ 27 ods. 4 zákona č. 563/2009 Z. z.",
        "holiday_calendar_legal_basis": "zákon č. 241/1993 Z. z., vrátane § 4b pre rok 2026",
        "deadline_rule": "15th_day_of_following_calendar_month_adjusted_to_next_working_day",
        "deadline_adjusted": operational_deadline != statutory_deadline,
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
        deadline = operational_deadline.isoformat()
        return {
            **base,
            "status": "READY",
            "tax_remittance_deadline": deadline,
            "notification_deadline": deadline,
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
    transaction_date: date | str | None = None,
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

    try:
        amount = Decimal(str(transaction_amount["amount"]))
    except (InvalidOperation, KeyError) as exc:
        raise ValueError("Transaction amount must be a decimal number.") from exc
    if amount <= 0:
        raise ValueError("Transaction amount must be greater than zero.")

    currency = str(transaction_amount.get("currency") or "").upper()
    base = {
        "schema_version": 2,
        "source_country": "SK",
        "status": "NOT_CALCULATED",
        "gross_amount": str(amount),
        "transaction_currency": currency,
        "tax_currency": config.currency,
        "gross_amount_eur": None,
        "rate_percent": None,
        "withholding_tax_eur": None,
        "net_amount_eur": None,
        "exchange_rate": None,
        "tax_treatment": tax_treatment,
        "rounding_policy": "section_47_two_decimal_half_up",
        "rounding_legal_basis": "§ 47 zákona č. 595/2003 Z. z.",
        "fx_legal_basis": "§ 31 ods. 3 zákona č. 595/2003 Z. z.",
    }

    if decision_status != "FINAL" or (
        rate_percent is None and tax_treatment is None
    ):
        return {
            **base,
            "reason": "final_rate_unavailable",
        }

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

    gross_eur = amount
    exchange_output = None
    if currency != "EUR":
        if transaction_date is None:
            return {**base, "reason": "sk_withholding_date_required_for_fx"}
        withholding_date = _parse_date(transaction_date)
        evidence = transaction_amount.get("exchange_rate")
        if not isinstance(evidence, Mapping):
            return {**base, "reason": "sk_ecb_nbs_exchange_rate_evidence_missing"}
        source = str(evidence.get("source") or "").upper()
        if source not in {"ECB", "NBS"}:
            return {**base, "reason": "sk_exchange_rate_source_not_ecb_or_nbs"}
        if str(evidence.get("currency") or "").upper() != currency:
            return {**base, "reason": "sk_exchange_rate_currency_mismatch"}
        try:
            effective_date = _parse_date(evidence.get("effective_date"))
        except (TypeError, ValueError):
            return {**base, "reason": "sk_exchange_rate_effective_date_invalid"}
        if effective_date != withholding_date:
            return {**base, "reason": "sk_exchange_rate_date_mismatch"}
        try:
            eur_per_unit = Decimal(str(evidence["eur_per_unit"]))
        except (InvalidOperation, KeyError) as exc:
            raise ValueError("ECB/NBS EUR-per-unit rate must be a decimal number.") from exc
        if eur_per_unit <= 0:
            raise ValueError("ECB/NBS EUR-per-unit rate must be greater than zero.")
        gross_eur = amount * eur_per_unit
        exchange_output = {
            "source": source,
            "currency": currency,
            "eur_per_unit": str(eur_per_unit),
            "effective_date": effective_date.isoformat(),
            "source_url": evidence.get("source_url"),
            "date_selection": "withholding_date_section_31_3",
        }

    gross_eur = gross_eur.quantize(EUR_CENT, rounding=ROUND_HALF_UP)
    tax = (gross_eur * rate / Decimal("100")).quantize(
        EUR_CENT,
        rounding=ROUND_HALF_UP,
    )
    net = (gross_eur - tax).quantize(EUR_CENT, rounding=ROUND_HALF_UP)

    return {
        **base,
        "status": "CALCULATED",
        "reason": None,
        "gross_amount_eur": str(gross_eur),
        "rate_percent": None if non_taxing else str(rate),
        "withholding_tax_eur": str(tax),
        "net_amount_eur": str(net),
        "exchange_rate": exchange_output,
    }
