from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from taxtreat.countries.registry import get_country_config
from .editorial import _date as _editorial_date, _number as _editorial_number


@dataclass(frozen=True)
class ReportCalculationContext:
    calculation_base: str
    calculation_tax: str
    net_amount: str
    fx_line: str


def _number(value: Any, decimals: int = 2) -> str:
    return _editorial_number(value, decimals)


def _date(value: Any) -> str:
    return _editorial_date(value)


def _net(gross: Any, tax: Any, explicit: Any) -> Any:
    if explicit not in (None, ""):
        return explicit
    if gross in (None, "") or tax in (None, ""):
        return None
    try:
        return float(gross) - float(tax)
    except (TypeError, ValueError):
        return None


def _czk_context(
    calculation: dict[str, Any],
    currency: str,
) -> ReportCalculationContext:
    gross = calculation.get("gross_amount_czk")
    tax = calculation.get("withholding_tax_czk")
    net = _net(
        gross,
        tax,
        calculation.get("net_amount_czk"),
    )

    fx_line = ""
    fx = calculation.get("exchange_rate") or {}
    if fx:
        fx_url = escape(str(fx.get("source_url") or ""), quote=True)
        link = (
            f'<a href="{fx_url}">Kurzovní lístek ČNB ↗</a>'
            if fx_url
            else ""
        )
        fx_line = (
            f"1 {escape(str(fx.get('currency') or currency))} = "
            f"{_number(fx.get('czk_per_unit'), 6)} Kč"
            f" · {_date(fx.get('effective_date'))} · {link}"
        )

    return ReportCalculationContext(
        calculation_base=f"{_number(gross)} Kč",
        calculation_tax=f"{_number(tax)} Kč",
        net_amount=(
            f"{_number(net)} Kč"
            if net not in (None, "")
            else "—"
        ),
        fx_line=fx_line,
    )


def _payment_currency_eur_context(
    calculation: dict[str, Any],
    currency: str,
) -> ReportCalculationContext:
    payment_currency = str(
        calculation.get("transaction_currency")
        or currency
        or "EUR"
    )

    gross = calculation.get("gross_amount")
    tax_payment = calculation.get(
        "withholding_tax_transaction_currency"
    )
    net = _net(
        gross,
        tax_payment,
        calculation.get("net_amount_transaction_currency"),
    )

    fx_line = ""
    fx = calculation.get("exchange_rate") or {}
    if fx:
        fx_url = escape(str(fx.get("source_url") or ""), quote=True)
        fx_source = escape(str(fx.get("source") or "ECB/NBS"))
        link = (
            f'<a href="{fx_url}">Kurz {fx_source} ↗</a>'
            if fx_url
            else ""
        )
        fx_line = (
            f"1 EUR = "
            f"{_number(fx.get('foreign_units_per_eur'), 6)} "
            f"{escape(str(fx.get('currency') or currency))}"
            f" · {_date(fx.get('effective_date'))} · {link}"
        )

    return ReportCalculationContext(
        calculation_base=(
            f"{_number(gross)} {escape(payment_currency)}"
        ),
        calculation_tax=(
            f"{_number(calculation.get('withholding_tax_eur'))} EUR"
        ),
        net_amount=(
            f"{_number(net)} {escape(payment_currency)}"
            if net not in (None, "")
            else "—"
        ),
        fx_line=fx_line,
    )


def build_report_calculation_context(
    *,
    source_country: str,
    calculation: dict[str, Any],
    currency: str,
) -> ReportCalculationContext:
    config = get_country_config(source_country)

    if calculation.get("status") != "CALCULATED":
        return ReportCalculationContext("—", "—", "—", "")

    strategy = config.report_calculation_strategy

    if strategy == "czk":
        return _czk_context(calculation, currency)

    if strategy == "payment_currency_eur":
        return _payment_currency_eur_context(
            calculation,
            currency,
        )

    raise ValueError(
        f"Unsupported report calculation strategy for "
        f"{config.code}: {strategy}"
    )
