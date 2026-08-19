from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .country_copy import ReportCountryCopy, report_country_copy


@dataclass(frozen=True)
class LocalizedReportContext:
    source_country: str
    copy: ReportCountryCopy
    transaction_title: str
    treaty_name: str
    domestic_reference: str
    deadline_cards: tuple[tuple[str, str], ...]
    documentation_items: tuple[str, ...]
    flow_nodes: tuple[tuple[str, str], ...]


def _scope(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("scope") or {}


def _facts(report: dict[str, Any]) -> dict[str, Any]:
    return ((report.get("assumptions") or {}).get("transaction_facts") or {})


def source_country(report: dict[str, Any]) -> str:
    return str(_scope(report).get("source_country") or "CZ").upper()


def transaction_title(report: dict[str, Any], copy: ReportCountryCopy) -> str:
    scope = _scope(report)
    facts = _facts(report)
    payer = str(facts.get("report_payer_name") or copy.payer_missing_label)
    recipient = str(facts.get("report_recipient_name") or copy.recipient_missing_label)
    label = copy.transaction_labels.get(
        str(scope.get("income_type") or ""), copy.cross_border_payment_label
    )
    return f"{label}: {payer} → {recipient}"


def treaty_name(report: dict[str, Any], copy: ReportCountryCopy) -> str:
    code = str(_scope(report).get("recipient_country") or "").upper()
    if code:
        return (
            f"{copy.treaty_name_prefix} {copy.treaty_country_prefix} a štátom {code} "
            "o zamedzení dvojitého zdanenia"
            if copy.source_country == "SK"
            else f"{copy.treaty_name_prefix} {copy.treaty_country_prefix} a státem {code} o zamezení dvojího zdanění"
        )
    return "Zmluva o zamedzení dvojitého zdanenia" if copy.source_country == "SK" else "Smlouva o zamezení dvojího zdanění"


def deadline_cards(report: dict[str, Any], copy: ReportCountryCopy) -> tuple[tuple[str, str], ...]:
    schedule = ((report.get("result") or {}).get("withholding_compliance_schedule") or {})
    cards: list[tuple[str, str]] = []
    if schedule.get("remittance_deadline"):
        cards.append((copy.remittance_deadline_label, copy.remittance_deadline_note))
    if schedule.get("notification_deadline"):
        cards.append((copy.notification_deadline_label, copy.notification_deadline_note))
    return tuple(cards)


def documentation_items(report: dict[str, Any], copy: ReportCountryCopy) -> tuple[str, ...]:
    facts = _facts(report)
    income = str(_scope(report).get("income_type") or "")
    items = [copy.residence_certificate_document]
    if facts.get("beneficial_owner") is not None:
        items.append(copy.beneficial_owner_document)
    if income == "dividend" and facts.get("ownership_percent") not in (None, ""):
        items.append(copy.ownership_document)
    if income == "dividend" and facts.get("holding_period_months") not in (None, ""):
        items.append(copy.holding_period_document)
    items.append(copy.transaction_document)
    return tuple(dict.fromkeys(items))


def flow_nodes(copy: ReportCountryCopy) -> tuple[tuple[str, str], ...]:
    return (
        (copy.withholding_tax_label, copy.flow_domestic_question),
        (copy.flow_treaty_relief_title, copy.flow_treaty_relief_question),
        (copy.flow_conditions_title, copy.flow_conditions_question),
        (copy.flow_mli_title, copy.flow_mli_question),
        (copy.flow_final_rate_title, ""),
    )


def build_localized_report_context(report: dict[str, Any]) -> LocalizedReportContext:
    code = source_country(report)
    copy = report_country_copy(code)
    return LocalizedReportContext(
        source_country=code,
        copy=copy,
        transaction_title=transaction_title(report, copy),
        treaty_name=treaty_name(report, copy),
        domestic_reference=copy.domestic_law_reference,
        deadline_cards=deadline_cards(report, copy),
        documentation_items=documentation_items(report, copy),
        flow_nodes=flow_nodes(copy),
    )
