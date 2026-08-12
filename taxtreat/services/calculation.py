from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping


MONEY_QUANTUM = Decimal("0.01")
CALCULATION_VERSION = 1


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


def build_withholding_tax_calculation(
    transaction_amount: Mapping[str, Any] | None,
    *,
    decision_status: str,
    rate_percent: float | Decimal | None,
) -> dict[str, Any] | None:
    """Calculate indicative WHT only from a final released rate."""

    if transaction_amount is None:
        return None

    amount = Decimal(str(transaction_amount["amount"]))
    currency = str(transaction_amount["currency"]).upper()
    base = {
        "schema_version": CALCULATION_VERSION,
        "gross_amount": _decimal_string(amount),
        "currency": currency,
        "rate_percent": None,
        "estimated_tax_amount": None,
        "estimated_net_amount": None,
        "rounding_policy": "2_decimal_half_up",
    }

    if decision_status != "FINAL" or rate_percent is None:
        return {
            **base,
            "status": "NOT_CALCULATED",
            "reason": "final_rate_unavailable",
        }

    try:
        rate = Decimal(str(rate_percent))
    except InvalidOperation as exc:
        raise ValueError("Rate must be a decimal number.") from exc

    if rate < 0 or rate > 100:
        raise ValueError("Final withholding-tax rate must be between 0 and 100.")

    tax = (amount * rate / Decimal("100")).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    net = (amount - tax).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    return {
        **base,
        "status": "CALCULATED",
        "reason": None,
        "rate_percent": _decimal_string(rate),
        "estimated_tax_amount": _decimal_string(tax),
        "estimated_net_amount": _decimal_string(net),
    }
