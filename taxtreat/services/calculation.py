from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP
from typing import Any, Mapping


MONEY_QUANTUM = Decimal("0.01")
WHOLE_CROWN = Decimal("1")
CALCULATION_VERSION = 2


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


def _not_calculated(
    base: Mapping[str, Any],
    reason: str,
) -> dict[str, Any]:
    return {
        **base,
        "status": "NOT_CALCULATED",
        "reason": reason,
    }


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def build_withholding_tax_calculation(
    transaction_amount: Mapping[str, Any] | None,
    *,
    decision_status: str,
    rate_percent: float | Decimal | None,
) -> dict[str, Any] | None:
    """Calculate CZK WHT only from a final rate and complete FX evidence."""

    if transaction_amount is None:
        return None

    try:
        amount = Decimal(str(transaction_amount["amount"]))
    except (InvalidOperation, KeyError) as exc:
        raise ValueError("Transaction amount must be a decimal number.") from exc
    if amount <= 0:
        raise ValueError("Transaction amount must be greater than zero.")

    currency = str(transaction_amount["currency"]).upper()
    base = {
        "schema_version": CALCULATION_VERSION,
        "gross_amount": _decimal_string(amount),
        "transaction_currency": currency,
        "gross_amount_czk": None,
        "tax_currency": "CZK",
        "rate_percent": None,
        "withholding_tax_czk": None,
        "net_amount_czk": None,
        "rounding_policy": "section_36_3_whole_crown_down",
        "exchange_rate": None,
    }

    if decision_status != "FINAL" or rate_percent is None:
        return _not_calculated(base, "final_rate_unavailable")

    try:
        rate = Decimal(str(rate_percent))
    except InvalidOperation as exc:
        raise ValueError("Rate must be a decimal number.") from exc
    if rate < 0 or rate > 100:
        raise ValueError("Final withholding-tax rate must be between 0 and 100.")

    gross_czk = amount
    exchange_output = None

    if currency != "CZK":
        payment_date = _parse_date(transaction_amount.get("payment_date"))
        accounting_date = _parse_date(
            transaction_amount.get("accounting_date")
        )
        if payment_date is None or accounting_date is None:
            return _not_calculated(
                base,
                "exchange_rate_reference_dates_incomplete",
            )

        required_rate_date = min(payment_date, accounting_date)
        evidence = transaction_amount.get("exchange_rate")
        if not isinstance(evidence, Mapping):
            return _not_calculated(base, "exchange_rate_evidence_missing")

        effective_date = _parse_date(evidence.get("effective_date"))
        if effective_date != required_rate_date:
            return _not_calculated(base, "exchange_rate_date_mismatch")
        if str(evidence.get("source", "")).upper() != "CNB":
            return _not_calculated(base, "exchange_rate_source_not_cnb")
        if str(evidence.get("currency", "")).upper() != currency:
            return _not_calculated(
                base,
                "exchange_rate_currency_mismatch",
            )

        try:
            czk_per_unit = Decimal(str(evidence["czk_per_unit"]))
        except (InvalidOperation, KeyError) as exc:
            raise ValueError(
                "CNB exchange rate must be a decimal number."
            ) from exc
        if czk_per_unit <= 0:
            raise ValueError("CNB exchange rate must be greater than zero.")

        gross_czk = amount * czk_per_unit
        exchange_output = {
            "source": "CNB",
            "currency": currency,
            "czk_per_unit": _decimal_string(czk_per_unit),
            "effective_date": effective_date.isoformat(),
            "payment_date": payment_date.isoformat(),
            "accounting_date": accounting_date.isoformat(),
            "date_selection": "earlier_of_payment_or_accounting",
            "source_url": evidence.get("source_url"),
        }

    tax = (gross_czk * rate / Decimal("100")).quantize(
        WHOLE_CROWN,
        rounding=ROUND_DOWN,
    )
    net_czk = (gross_czk - tax).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    return {
        **base,
        "status": "CALCULATED",
        "reason": None,
        "gross_amount_czk": _decimal_string(gross_czk),
        "rate_percent": _decimal_string(rate),
        "withholding_tax_czk": _decimal_string(tax),
        "net_amount_czk": _decimal_string(net_czk),
        "exchange_rate": exchange_output,
    }
