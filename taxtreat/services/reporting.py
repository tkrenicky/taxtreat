from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html import escape
from typing import Any, Mapping

from taxtreat.services.report_locales import english_excerpt_for_citation


REPORT_SCHEMA_VERSION = 4
LEGAL_DATA_CUTOFF = "2026-08-12"
SECTION19_SOURCE_URL = "https://e-sbirka.gov.cz/sb/1992/586"

_DISCLAIMERS = {
    "cs": (
        "TaxTreat je informační nástroj. Automatizovaně zobrazuje informace "
        "odvozené z uvedených právních zdrojů a z údajů zadaných uživatelem. "
        "Neprovádí individuální právní ani daňové posouzení, neposkytuje "
        "doporučení ani právní či daňové poradenství a neurčuje postup uživatele. "
        "Uživatel odpovídá za správnost vstupních údajů a za vlastní posouzení "
        "použitelnosti zobrazených informací."
    ),
    "en": (
        "TaxTreat is an information tool. It automatically presents information "
        "derived from the legal sources shown and from facts entered by the user. "
        "It does not perform an individual legal or tax assessment, provide legal "
        "or tax advice, or determine the user's course of action. The user remains "
        "responsible for the accuracy of the input data and for assessing whether "
        "the displayed information is applicable."
    ),
}

_FACT_LABELS = {
    "cs": {
        "beneficial_owner": "Skutečné vlastnictví příjmu",
        "recipient_is_treaty_resident": "Daňová rezidence pro účely smlouvy",
        "permanent_establishment_connection": "Vazba příjmu ke stálé provozovně v ČR",
        "ownership_percent": "Podíl na základním kapitálu plátce",
        "holding_period_months": "Doba držby podílu",
        "direct_ownership": "Přímé držení podílu",
        "recipient_is_qualifying_company_form": "Právní forma příjemce pro účely § 19 ZDP",
        "recipient_subject_to_qualifying_corporate_tax": "Daňové postavení příjemce pro účely § 19 ZDP",
        "recipient_has_no_tax_exemption_or_zero_rate_option": "Absence osvobození nebo nulového režimu u příjemce",
    },
    "en": {
        "beneficial_owner": "Beneficial ownership of the income",
        "recipient_is_treaty_resident": "Tax residence for treaty purposes",
        "permanent_establishment_connection": "Connection of the income to a Czech permanent establishment",
        "ownership_percent": "Ownership in the payer's share capital",
        "holding_period_months": "Holding period",
        "direct_ownership": "Direct ownership",
        "recipient_is_qualifying_company_form": "Recipient legal form for Section 19 purposes",
        "recipient_subject_to_qualifying_corporate_tax": "Recipient tax status for Section 19 purposes",
        "recipient_has_no_tax_exemption_or_zero_rate_option": "No recipient exemption or zero-rate regime",
    },
}

_REQUIRED_DOCUMENTATION = {
    "cs": [
        "Smluvní dokumentace a doklad o platbě nebo zaúčtování závazku",
        "Potvrzení daňové rezidence a podklady ke skutečnému vlastnictví",
        "Podklady ke každému skutkovému údaji použitému ve výpočtu",
        "Doklady vyžadované pro případné vnitrostátní osvobození",
    ],
    "en": [
        "Contract documentation and evidence of payment or recognition of the liability",
        "Tax residence certificate and beneficial ownership documentation",
        "Documentation supporting each factual item used in the calculation",
        "Documentation required for any domestic exemption",
    ],
}


def _language(value: Any) -> str:
    return "en" if str(value or "").lower() == "en" else "cs"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def stable_report_id(request: Mapping[str, Any], analysis: Mapping[str, Any]) -> str:
    fingerprint = {
        "request": dict(request),
        "result": {
            "status": analysis.get("status"),
            "rate": analysis.get("rate"),
            "candidate_rate": analysis.get("candidate_rate"),
            "tax_treatment": analysis.get("tax_treatment"),
            "candidate_tax_treatment": analysis.get("candidate_tax_treatment"),
            "selected_rule_id": analysis.get("selected_rule_id"),
            "candidate_rule_id": analysis.get("candidate_rule_id"),
            "missing_facts": analysis.get("missing_facts", []),
            "legal_dataset_release": analysis.get("legal_dataset_release"),
            "source_release": analysis.get("dataset_version"),
            "withholding_tax_calculation": analysis.get("withholding_tax_calculation"),
            "citation_hashes": sorted(
                citation.get("excerpt_sha256")
                for citation in analysis.get("citations", [])
                if citation.get("excerpt_sha256")
            ),
        },
    }
    digest = hashlib.sha256(_canonical_json(fingerprint).encode("utf-8")).hexdigest()
    return f"TAXTREAT-{digest[:20].upper()}"


def build_professional_report(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
    *,
    generated_at: datetime | None = None,
    language: str = "cs",
) -> dict[str, Any]:
    language = _language(language)
    generated_at = generated_at or datetime.now(timezone.utc)
    status = str(analysis.get("status"))
    treatment = analysis.get("tax_treatment")

    if language == "en":
        if status == "FINAL" and treatment == "exclusive_foreign_taxation":
            risk = "Under the applied treaty rule, the income is taxable only in the recipient's state of tax residence."
        elif status == "FINAL" and treatment == "domestic_exemption":
            risk = "The income is exempt under the applied Czech domestic rule."
        elif status == "FINAL":
            risk = "TaxTreat matched a legal rule to the facts entered by the user."
        elif status == "OUT_OF_SCOPE":
            risk = "The transaction is outside the currently supported scope."
        else:
            risk = "Open factual items or identified legal conditions must be resolved before the result can be finalised."
    else:
        if status == "FINAL" and treatment == "exclusive_foreign_taxation":
            risk = "Podle použitého smluvního pravidla se příjem zdaňuje pouze ve státě daňové rezidence příjemce."
        elif status == "FINAL" and treatment == "domestic_exemption":
            risk = "Příjem je podle použitého vnitrostátního pravidla osvobozen."
        elif status == "FINAL":
            risk = "TaxTreat přiřadil právní pravidlo k údajům zadaným uživatelem."
        elif status == "OUT_OF_SCOPE":
            risk = "Transakce je mimo aktuálně podporovaný rozsah."
        else:
            risk = "Před použitím výsledku je potřeba doplnit otevřené skutkové údaje nebo uzavřít označené podmínky."

    source_path = analysis.get("legal_path") or analysis.get("citations", [])
    citations = [
        {
            "rule_id": citation.get("rule_id"),
            "source_id": citation.get("source_id"),
            "source_url": citation.get("source_url"),
            "article": citation.get("article"),
            "paragraph": citation.get("paragraph"),
            "legal_layer": citation.get("legal_layer"),
            "legal_instrument": citation.get("legal_instrument"),
            "rate": citation.get("rate"),
            "tax_treatment": citation.get("tax_treatment"),
            "path_role": citation.get("path_role"),
            "excerpt": citation.get("excerpt") if citation.get("legal_layer") in {"treaty", "protocol", "mli"} else None,
            "excerpt_sha256": citation.get("excerpt_sha256") if citation.get("legal_layer") in {"treaty", "protocol", "mli"} else None,
        }
        for citation in source_path
    ]
    if language == "en":
        recipient_country = str(request.get("recipient_country") or "")
        for citation in citations:
            if citation.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            locale = english_excerpt_for_citation(citation, recipient_country)
            citation["canonical_source_url"] = citation.get("source_url")
            if locale:
                citation.update(locale)
                if locale.get("excerpt_source_url"):
                    citation["source_url"] = locale["excerpt_source_url"]
            else:
                citation["excerpt"] = None
                citation["excerpt_language"] = None
                citation["excerpt_status"] = "english_excerpt_unavailable"
                citation["excerpt_status_label"] = "English excerpt unavailable"


    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": stable_report_id(request, analysis),
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "language": language,
        "legal_data_cutoff": LEGAL_DATA_CUTOFF,
        "legal_dataset_release": analysis.get("legal_dataset_release"),
        "source_release": analysis.get("dataset_version"),
        "scope": {
            "source_country": request.get("source_country"),
            "recipient_country": request.get("recipient_country"),
            "income_type": request.get("income_type"),
            "transaction_date": request.get("transaction_date"),
            "transaction_amount": request.get("transaction_amount"),
        },
        "result": {
            "status": analysis.get("status"),
            "rate": analysis.get("rate"),
            "candidate_rate": analysis.get("candidate_rate"),
            "tax_treatment": analysis.get("tax_treatment"),
            "candidate_tax_treatment": analysis.get("candidate_tax_treatment"),
            "eligible": analysis.get("eligible"),
            "requires_review": analysis.get("requires_review"),
            "selected_rule_id": analysis.get("selected_rule_id"),
            "candidate_rule_id": analysis.get("candidate_rule_id"),
            "applied_rule_ids": analysis.get("applied_rule_ids", []),
            "withholding_tax_calculation": analysis.get("withholding_tax_calculation"),
            "withholding_compliance_schedule": analysis.get("withholding_compliance_schedule"),
        },
        "assumptions": {
            "transaction_facts": request.get("facts", {}),
            "user_determinations": request.get("determinations", {}),
        },
        "missing_facts": analysis.get("missing_facts", []),
        "missing_legal_layers": analysis.get("missing_legal_layers", []),
        "failed_conditions": analysis.get("failed_conditions", []),
        "decision_path": analysis.get("layer_results", []),
        "explanation": analysis.get("explanation", []),
        "official_sources": citations,
        "risk_assessment": risk,
        "required_documentation": list(_REQUIRED_DOCUMENTATION[language]),
        "disclaimer": _DISCLAIMERS[language],
    }
    return report


def _source_title(source: Mapping[str, Any], language: str) -> str:
    article = escape(str(source.get("article") or "—"))
    paragraph = source.get("paragraph")
    suffix = f", {escape(str(paragraph))}" if paragraph else ""
    if source.get("legal_layer") in {"treaty", "protocol", "mli"}:
        return f"Double Tax Treaty · Article {article}{suffix}" if language == "en" else f"Smlouva o zamezení dvojího zdanění · článek {article}{suffix}"
    return f"Czech Income Taxes Act · Section {article}{suffix}" if language == "en" else f"Zákon č. 586/1992 Sb., o daních z příjmů · § {article}{suffix}"


def _report_date(value: Any, language: str) -> str:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if language == "en":
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return f"{parsed.day} {months[parsed.month - 1]} {parsed.year}"
        return f"{parsed.day}. {parsed.month}. {parsed.year}"
    except ValueError:
        return text or "—"


def _income_type_label(value: Any, language: str) -> str:
    if language == "en":
        return {"dividend": "Dividends", "interest": "Interest", "royalty": "Royalties"}.get(str(value), str(value or "—"))
    return {"dividend": "Dividendy", "interest": "Úroky", "royalty": "Licenční poplatky"}.get(str(value), str(value or "—"))


def _format_number(value: Any, *, maximum_decimals: int = 2) -> str:
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if number.is_integer():
        rendered = f"{int(number):,}"
    else:
        rendered = f"{number:,.{maximum_decimals}f}".rstrip("0").rstrip(".")
    return rendered.replace(",", " ")


def _format_rate(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return f"{_format_number(value)} %"


def _result_copy(result: Mapping[str, Any], source_title: str | None, language: str) -> tuple[str, str]:
    if language == "en":
        reference = source_title or "the applied legal rule"
        treatment = result.get("tax_treatment")
        if treatment == "exclusive_foreign_taxation":
            return (f"Under {reference}, the entered facts result in no Czech taxation", "TaxTreat automatically matched a legal rule to the facts entered by the user; this is not an individual tax assessment.")
        if treatment == "domestic_exemption":
            return (f"Under {reference}, the entered facts qualify for a domestic exemption", "TaxTreat automatically matched a legal rule to the facts entered by the user; this is not an individual tax assessment.")
        if result.get("status") == "FINAL" and result.get("rate") is not None:
            return (f"Under {reference}, the rate assigned to the entered facts is {_format_rate(result['rate'])}", "The rate is shown as an automated matching of a rule to the entered facts, not as tax advice or a tax opinion.")
        return ("The entered facts do not yet allow a specific rule to be assigned", "After the open facts are completed, TaxTreat will reassess the rules matching the entered circumstances.")

    reference = source_title or "použité právní pravidlo"
    treatment = result.get("tax_treatment")
    if treatment == "exclusive_foreign_taxation":
        return (f"Podle {reference} je při zadaných údajích přiřazeno pravidlo bez českého zdanění", "TaxTreat automatizovaně přiřadil právní pravidlo k údajům zadaným uživatelem; nejde o individuální daňové posouzení.")
    if treatment == "domestic_exemption":
        return (f"Podle {reference} je při zadaných údajích přiřazeno pravidlo osvobození", "TaxTreat automatizovaně přiřadil právní pravidlo k údajům zadaným uživatelem; nejde o individuální daňové posouzení.")
    if result.get("status") == "FINAL" and result.get("rate") is not None:
        return (f"Podle {reference} je při zadaných údajích přiřazena sazba {_format_rate(result['rate'])}", "Sazba je zobrazena jako automatizované přiřazení pravidla k zadaným údajům, nikoli jako daňové doporučení nebo stanovisko.")
    return ("Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo", "Po doplnění otevřených údajů TaxTreat znovu zobrazí pravidla odpovídající zadaným skutečnostem.")


def _section19_assessment(report: Mapping[str, Any], language: str) -> str:
    scope = report.get("scope", {})
    if str(scope.get("source_country") or "").upper() != "CZ" or scope.get("income_type") != "dividend":
        return ""
    layers = [item for item in report.get("decision_path", []) if item.get("layer") == "eu_relief" and "DIVIDEND" in str(item.get("rule_id") or "")]
    if not layers:
        return ""
    treatment = report.get("result", {}).get("tax_treatment")
    applicable = any(item.get("outcome") == "applicable" for item in layers)
    unresolved = any(item.get("outcome") == "unresolved" for item in layers)
    all_not = bool(layers) and all(item.get("outcome") in {"not_applicable", "failed"} for item in layers)
    if language == "en":
        if treatment == "domestic_exemption" or applicable:
            copy = "<strong>Applicable – Czech withholding tax is not due.</strong> The domestic exemption under Section 19 of the Czech Income Taxes Act is the primary legal basis; treaty treatment is supplementary."
        elif all_not:
            copy = "The domestic exemption under Section 19 was assessed first and is not available based on the entered facts. The treaty analysis therefore determines the withholding tax treatment."
        elif unresolved:
            copy = "The domestic exemption under Section 19 is assessed before treaty relief but cannot yet be finalised because one or more factual conditions remain open."
        else:
            copy = "Section 19 was assessed before treaty relief."
        return f'<section><h2>Domestic exemption under Section 19</h2><div class="summary-box"><p>{copy}</p><p><a href="{SECTION19_SOURCE_URL}">Czech Income Taxes Act · Section 19 ↗</a></p></div></section>'
    if treatment == "domestic_exemption" or applicable:
        copy = "<strong>Osvobození se použije – česká srážková daň se neodvádí.</strong> Primárním právním titulem je § 19 ZDP; smluvní režim je pouze doplňkový."
    elif all_not:
        copy = "Osvobození podle § 19 ZDP bylo posouzeno jako první a podle zadaných údajů se neuplatní. Daňové zacházení proto určuje smluvní analýza."
    elif unresolved:
        copy = "Osvobození podle § 19 ZDP se posuzuje před smluvní úlevou, ale zatím jej nelze uzavřít, protože zůstávají otevřené skutkové podmínky."
    else:
        copy = "§ 19 ZDP byl posouzen před smluvní úlevou."
    return f'<section><h2>Vnitrostátní osvobození podle § 19 ZDP</h2><div class="summary-box"><p>{copy}</p><p><a href="{SECTION19_SOURCE_URL}">Zákon č. 586/1992 Sb. · § 19 ↗</a></p></div></section>'


def _ir_exemption_section(report: Mapping[str, Any], language: str) -> str:
    scope = report.get("scope", {})
    if str(scope.get("source_country") or "").upper() != "CZ" or scope.get("income_type") not in {"interest", "royalty"}:
        return ""
    if language == "en":
        return f'''<section><h2>Potential Czech domestic exemption</h2><div class="summary-box"><p>Irrespective of the treaty rate shown above, interest or royalties may be exempt from Czech withholding tax if the statutory conditions of Section 19 are met. Non-application of WHT requires an effective Czech tax authority decision under Section 38nb.</p><p><strong>Key conditions:</strong> qualifying company and jurisdiction; qualifying 25% direct relationship; 24-month holding period; beneficial ownership; qualifying tax/legal status; no disqualifying permanent-establishment attribution; and the Section 38nb decision.</p><p><a href="{SECTION19_SOURCE_URL}">Czech Income Taxes Act · Sections 19 and 38nb ↗</a></p></div></section>'''
    return f'''<section><h2>Možné vnitrostátní osvobození</h2><div class="summary-box"><p>Bez ohledu na výše uvedenou smluvní sazbu mohou být úroky nebo licenční poplatky při splnění podmínek § 19 ZDP osvobozeny od české srážkové daně. Pro neuplatnění WHT je nutné účinné rozhodnutí správce daně podle § 38nb ZDP.</p><p><strong>Základní podmínky:</strong> kvalifikovaná společnost a jurisdikce; kvalifikované přímé 25% propojení; doba držby 24 měsíců; skutečné vlastnictví; příslušné daňové/právní postavení; žádná diskvalifikující vazba ke stálé provozovně; a rozhodnutí podle § 38nb ZDP.</p><p><a href="{SECTION19_SOURCE_URL}">Zákon č. 586/1992 Sb. · § 19 a § 38nb ↗</a></p></div></section>'''


def render_report_html(report: Mapping[str, Any]) -> str:
    language = _language(report.get("language"))
    en = language == "en"
    scope = report["scope"]
    result = report["result"]
    calculation = result.get("withholding_tax_calculation")
    schedule = result.get("withholding_compliance_schedule") or {}
    treatment = result.get("tax_treatment")
    non_taxing = treatment in {"exclusive_foreign_taxation", "domestic_exemption"}

    amount = scope.get("transaction_amount") or {}
    amount_copy = f"{_format_number(amount.get('amount'))} {escape(str(amount.get('currency') or ''))}".strip() if amount else ("Not provided" if en else "Neuvedena")

    if calculation and calculation.get("status") == "CALCULATED":
        tax_label = ("Czech tax payable" if en else "Česká daň k odvodu") if non_taxing else ("Withholding tax" if en else "Srážková daň")
        rate_value = ("Not applicable" if en else "Neuplatňuje se") if non_taxing else _format_rate(result.get("rate"))
        exchange = calculation.get("exchange_rate")
        exchange_row = ""
        if exchange:
            source_url = escape(str(exchange.get("source_url") or ""), quote=True)
            exchange_row = f'''<tr><th>{"CNB exchange rate" if en else "Kurz ČNB"}</th><td>1 {escape(str(exchange.get('currency') or ''))} = {_format_number(exchange.get('czk_per_unit'), maximum_decimals=6)} CZK</td><td>{_report_date(exchange.get('effective_date'), language)} · <a href="{source_url}">{"CNB source" if en else "zdroj ČNB"} ↗</a></td></tr>'''
        calculation_html = f'''
          <table class="calculation-table"><tbody>
            <tr><th>{"Gross amount" if en else "Hrubá částka"}</th><td>{_format_number(calculation.get('gross_amount'))} {escape(str(calculation.get('transaction_currency') or ''))}</td><td>{"Amount entered for this transaction" if en else "Částka zadaná pro tuto transakci"}</td></tr>
            <tr><th>{"Tax base" if en else "Daňový základ"}</th><td>{_format_number(calculation.get('gross_amount_czk'))} CZK</td><td>{"Value converted to CZK" if en else "Hodnota po přepočtu do CZK"}</td></tr>
            <tr class="emphasis"><th>{tax_label}</th><td>{_format_number(calculation.get('withholding_tax_czk'))} CZK</td><td>{"Rate" if en else "Sazba"} {rate_value}</td></tr>
            {exchange_row}
          </tbody></table>'''
    else:
        calculation_html = f'<p class="empty-note">{"The amount calculation has not been finalised." if en else "Částkový výpočet nebyl uzavřen."}</p>'

    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    sources = report.get("official_sources", [])
    selected_source = next((s for s in sources if s.get("rule_id") == selected_rule_id), None)
    if treatment == "domestic_exemption":
        selected_source = next((s for s in sources if s.get("path_role") == "domestic_exemption_basis"), selected_source)
    selected_source_title = _source_title(selected_source, language) if selected_source else None
    conclusion, conclusion_detail = _result_copy(result, selected_source_title, language)
    if selected_source:
        why_result = (f"Under {_source_title(selected_source, language)}, TaxTreat matched the rule used in the calculation to the entered facts." if en else f"Podle {_source_title(selected_source, language)} je v TaxTreat při zadaných údajích přiřazeno pravidlo použité ve výpočtu.")
    else:
        why_result = "TaxTreat displays the rules matched to the entered facts and the legal sources shown in this output." if en else "TaxTreat zobrazuje pravidla přiřazená k zadaným údajům a právní zdroje uvedené v tomto výstupu."

    source_items = []
    for source in sources:
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        excerpt_html = f"<blockquote>{excerpt}</blockquote>" if excerpt else ""
        provenance = ""
        if en and source.get("legal_layer") in {"treaty", "protocol", "mli"}:
            status_label = escape(str(source.get("excerpt_status_label") or "English source status not available"))
            authority = escape(str(source.get("excerpt_authority") or ""))
            detail = f" · {authority}" if authority else ""
            provenance = f'<p class="source-provenance"><strong>English text status:</strong> {status_label}{detail}</p>'
        link_label = "Source for displayed text" if en else "Oficiální zdroj"
        source_items.append(
            f'<article class="legal-source"><div class="source-head"><h3>{_source_title(source, language)}</h3>'
            f'<a href="{url}">{link_label} ↗</a></div>{provenance}{excerpt_html}</article>'
        )
    if not source_items:
        source_items.append(f'<p class="empty-note">{"No specific legal source was assigned to this information output." if en else "Pro tento informační výstup nebyl přiřazen konkrétní právní zdroj."}</p>')

    fact_labels = _FACT_LABELS[language]
    missing = report.get("missing_facts", [])
    missing_items = "".join(f"<li>{escape(fact_labels.get(str(item), str(item).replace('_', ' ')))}</li>" for item in missing) or f'<li>{"No open factual items." if en else "Žádné otevřené skutkové údaje."}</li>'
    documents = "".join(f"<li>{escape(str(item))}</li>" for item in report.get("required_documentation", []))

    deadline_labels = {
        "reference_date": "Reference date" if en else "Rozhodné datum",
        "remittance_deadline": "Withholding tax remittance" if en else "Odvod srážkové daně",
        "notification_deadline": "Outbound income notification" if en else "Oznámení příjmu do zahraničí",
    }
    deadline_rows = []
    for key, label in deadline_labels.items():
        if schedule.get(key):
            deadline_rows.append(f"<div><span>{label}</span><strong>{_report_date(schedule[key], language)}</strong></div>")
    compliance_html = "".join(deadline_rows) or f'<p class="empty-note">{"Compliance deadlines are not available for this result." if en else "Navazující lhůty nejsou pro tento výsledek k dispozici."}</p>'

    section19_html = _section19_assessment(report, language)
    ir_exemption_html = _ir_exemption_section(report, language)

    return f'''<!doctype html>
<html lang="{language}"><head><meta charset="utf-8"><title>TaxTreat · {"Withholding tax report" if en else "Report srážkové daně"}</title>
<style>
:root{{--forest:#173f39;--forest2:#28584f;--sage:#dce9e2;--cream:#f2efe8;--ink:#19342e;--muted:#6f7c77;--line:#dde3df;--white:#fff}}
*{{box-sizing:border-box}} body{{margin:0;color:var(--ink);background:var(--cream);font:13px/1.55 Inter,Arial,sans-serif}}
.report{{width:min(920px,calc(100% - 32px));margin:24px auto;background:#fff;box-shadow:0 12px 40px #173f3915}}
.masthead{{display:flex;justify-content:space-between;align-items:center;padding:25px 34px;color:#fff;background:var(--forest)}}
.brand{{font-size:19px;font-weight:800;letter-spacing:-.03em}} .brand-mark{{display:inline-grid;place-items:center;width:32px;height:32px;margin-right:9px;border-radius:9px;color:var(--forest);background:#d8e8d1;font-size:10px}}
.masthead small{{display:block;margin-top:5px;color:#bcd0c9}} .cutoff{{text-align:right;color:#d2dfda;font-size:10px;text-transform:uppercase;letter-spacing:.07em}}
main{{padding:34px}} .hero{{display:grid;grid-template-columns:1.25fr .75fr;gap:24px;padding:0 0 28px;border-bottom:1px solid var(--line)}}
.eyebrow{{margin-bottom:8px;color:#688079;font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}} h1{{margin:0 0 10px;font-size:29px;line-height:1.08;letter-spacing:-.04em}} .hero p{{margin:0;color:var(--muted)}}
.result-card{{padding:20px;border-radius:12px;background:#edf4f0;border:1px solid #d8e5de}} .result-card span{{display:block;color:#60766e;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}} .result-card strong{{display:block;margin-top:7px;color:var(--forest);font-size:21px;line-height:1.2}}
.transaction-strip{{display:grid;grid-template-columns:repeat(5,1fr);margin:24px 0 4px;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.transaction-strip div{{padding:13px 12px;border-right:1px solid var(--line)}} .transaction-strip div:last-child{{border-right:0}} .transaction-strip span{{display:block;color:#81908a;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}} .transaction-strip strong{{display:block;margin-top:5px;font-size:12px}}
section{{padding:27px 0;border-bottom:1px solid var(--line)}} section:last-child{{border-bottom:0}} h2{{margin:0 0 15px;color:var(--forest);font-size:18px;letter-spacing:-.02em}} h3{{margin:0;font-size:13px}}
.summary-box{{padding:17px 19px;border-left:4px solid var(--forest2);background:#f6f8f6;color:#39524b}} .summary-box p{{margin:0 0 8px}} .summary-box p:last-child{{margin-bottom:0}} .summary-box a{{color:var(--forest2);font-weight:700;text-decoration:none}}
.calculation-table{{width:100%;border-collapse:collapse;border:1px solid var(--line)}} .calculation-table th,.calculation-table td{{padding:13px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} .calculation-table th{{width:24%;color:#536a63;background:#f8f9f7;font-size:11px}} .calculation-table td:nth-child(2){{width:26%;font-weight:750;font-size:14px}} .calculation-table td:nth-child(3){{color:var(--muted);font-size:11px}} .calculation-table .emphasis td,.calculation-table .emphasis th{{background:#edf4f0}} .calculation-table .emphasis td:nth-child(2){{color:var(--forest);font-size:18px}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:28px}} ul{{margin:8px 0 0;padding-left:18px}} li{{margin:5px 0}}
.deadlines{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}} .deadlines div{{padding:14px;border:1px solid var(--line);border-radius:9px;background:#fafbf9}} .deadlines span{{display:block;color:#7b8984;font-size:9px;text-transform:uppercase;font-weight:800;letter-spacing:.05em}} .deadlines strong{{display:block;margin-top:6px}}
.legal-source{{padding:14px 0;border-top:1px solid var(--line)}} .legal-source:first-of-type{{border-top:0}} .source-head{{display:flex;justify-content:space-between;gap:20px}} .legal-source a{{color:var(--forest2);font-weight:700;text-decoration:none;font-size:11px}}
blockquote{{margin:12px 0 0;padding:14px 16px;border-left:3px solid #9ebcb1;background:#f7f9f7;color:#40534d;white-space:pre-line;font:11px/1.55 Georgia,serif}}
.source-provenance{{margin:8px 0 0;color:var(--muted);font-size:10px}} .source-provenance strong{{color:#536a63}}
.empty-note{{color:var(--muted)}} footer{{padding:18px 34px 24px;color:#78847f;background:#fafaf8;border-top:1px solid var(--line);font-size:9px}}
@media(max-width:720px){{.report{{width:100%;margin:0}} main{{padding:22px}} .hero,.two-col{{grid-template-columns:1fr}} .transaction-strip{{grid-template-columns:1fr 1fr}} .deadlines{{grid-template-columns:1fr}}}}
@media print{{@page{{size:A4;margin:11mm}} body{{background:#fff}} .report{{width:auto;margin:0;box-shadow:none}} .masthead{{print-color-adjust:exact;-webkit-print-color-adjust:exact}} section,.hero,.result-card,.calculation-table{{break-inside:avoid}} .legal-source{{break-inside:auto}} blockquote{{break-inside:auto}} a{{color:inherit;text-decoration:none}}}}
</style></head><body><article class="report">
<header class="masthead"><div><div class="brand"><span class="brand-mark">TT</span>TaxTreat</div><small>{"Czech withholding tax information" if en else "Informace k české srážkové dani"}</small></div><div class="cutoff">{"Legal status" if en else "Právní stav"}<br><strong>{_report_date(report.get('legal_data_cutoff'), language)}</strong></div></header>
<main>
<div class="hero"><div><div class="eyebrow">{"Information output" if en else "Informační výstup"}</div><h1>{"Czech withholding tax information" if en else "Informace k české srážkové dani"}</h1><p>{"Automated overview of legal rules and the calculation based on facts entered by the user." if en else "Automatizovaný přehled právních pravidel a výpočtu vycházejícího z údajů zadaných uživatelem."}</p></div><aside class="result-card"><span>{"Rule assigned to the entered facts" if en else "Pravidlo přiřazené k zadaným údajům"}</span><strong>{escape(conclusion)}</strong><p>{escape(conclusion_detail)}</p></aside></div>
<div class="transaction-strip"><div><span>{"Source" if en else "Zdroj"}</span><strong>{escape(str(scope.get('source_country') or '—'))}</strong></div><div><span>{"Recipient" if en else "Příjemce"}</span><strong>{escape(str(scope.get('recipient_country') or '—'))}</strong></div><div><span>{"Income" if en else "Příjem"}</span><strong>{escape(_income_type_label(scope.get('income_type'), language))}</strong></div><div><span>{"Date" if en else "Datum"}</span><strong>{_report_date(scope.get('transaction_date'), language)}</strong></div><div><span>{"Amount" if en else "Částka"}</span><strong>{amount_copy}</strong></div></div>
<section><h2>{"Tax calculation" if en else "Výpočet daně"}</h2>{calculation_html}</section>
{section19_html}
<section><h2>{"Applied legal rule" if en else "Použité právní pravidlo"}</h2><div class="summary-box"><p>{why_result}</p></div></section>
{ir_exemption_html}
<section><h2>{"Entered conditions and supporting documentation" if en else "Zadané podmínky a související podklady"}</h2><div class="two-col"><div><h3>{"Open factual items" if en else "Otevřené skutkové údaje"}</h3><ul>{missing_items}</ul></div><div><h3>{"Supporting documentation" if en else "Související podklady"}</h3><ul>{documents}</ul></div></div></section>
<section><h2>{"Tax calendar" if en else "Daňový kalendář"}</h2><div class="deadlines">{compliance_html}</div></section>
<section><h2>{"Legal basis" if en else "Právní základ"}</h2>{''.join(source_items)}</section>
</main><footer>{escape(str(report['disclaimer']))}</footer></article></body></html>'''
