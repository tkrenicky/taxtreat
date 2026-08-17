from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html import escape
from typing import Any, Mapping


REPORT_SCHEMA_VERSION = 3
LEGAL_DATA_CUTOFF = "2026-08-12"
DISCLAIMER = (
    "Výstup vychází ze zadaných údajů a z právních pravidel evidovaných "
    "v TaxTreat. Slouží jako pracovní podklad a nepředstavuje právní ani "
    "daňové poradenství nebo závazné stanovisko správce daně."
)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def stable_report_id(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> str:
    fingerprint = {
        "request": dict(request),
        "result": {
            "status": analysis.get("status"),
            "rate": analysis.get("rate"),
            "candidate_rate": analysis.get("candidate_rate"),
            "tax_treatment": analysis.get("tax_treatment"),
            "candidate_tax_treatment": analysis.get(
                "candidate_tax_treatment"
            ),
            "selected_rule_id": analysis.get("selected_rule_id"),
            "candidate_rule_id": analysis.get("candidate_rule_id"),
            "missing_facts": analysis.get("missing_facts", []),
            "legal_dataset_release": analysis.get(
                "legal_dataset_release"
            ),
            "source_release": analysis.get("dataset_version"),
            "withholding_tax_calculation": analysis.get(
                "withholding_tax_calculation"
            ),
            "citation_hashes": sorted(
                citation.get("excerpt_sha256")
                for citation in analysis.get("citations", [])
                if citation.get("excerpt_sha256")
            ),
        },
    }
    digest = hashlib.sha256(
        _canonical_json(fingerprint).encode("utf-8")
    ).hexdigest()
    return f"TAXTREAT-{digest[:20].upper()}"


def build_professional_report(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc)
    status = str(analysis.get("status"))

    treatment = analysis.get("tax_treatment")
    if status == "FINAL" and treatment == "exclusive_foreign_taxation":
        risk = (
            "Podle použitého smluvního pravidla se příjem zdaňuje pouze "
            "ve státě daňové rezidence příjemce."
        )
    elif status == "FINAL" and treatment == "domestic_exemption":
        risk = "Příjem je podle použitého vnitrostátního pravidla osvobozen."
    elif status == "FINAL":
        risk = "Výsledek vychází ze zadaných údajů a z právních pravidel uvedených v tomto výstupu."
    elif status == "OUT_OF_SCOPE":
        risk = "Transakce je mimo aktuálně podporovaný rozsah."
    else:
        risk = (
            "Před použitím výsledku je potřeba doplnit otevřené skutkové "
            "údaje nebo uzavřít označené podmínky."
        )

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
            "excerpt": (
                citation.get("excerpt")
                if citation.get("legal_layer") in {"treaty", "protocol", "mli"}
                else None
            ),
            "excerpt_sha256": (
                citation.get("excerpt_sha256")
                if citation.get("legal_layer") in {"treaty", "protocol", "mli"}
                else None
            ),
        }
        for citation in source_path
    ]

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": stable_report_id(request, analysis),
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
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
            "candidate_tax_treatment": analysis.get(
                "candidate_tax_treatment"
            ),
            "eligible": analysis.get("eligible"),
            "requires_review": analysis.get("requires_review"),
            "selected_rule_id": analysis.get("selected_rule_id"),
            "candidate_rule_id": analysis.get("candidate_rule_id"),
            "applied_rule_ids": analysis.get("applied_rule_ids", []),
            "withholding_tax_calculation": analysis.get(
                "withholding_tax_calculation"
            ),
            "withholding_compliance_schedule": analysis.get(
                "withholding_compliance_schedule"
            ),
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
        "required_documentation": [
            "Smluvní dokumentace a doklad o platbě nebo zaúčtování závazku",
            "Potvrzení daňové rezidence a podklady ke skutečnému vlastnictví",
            "Podklady ke každému skutkovému údaji použitému ve výpočtu",
            "Doklady vyžadované pro případné vnitrostátní osvobození",
        ],
        "disclaimer": DISCLAIMER,
    }
    return report


_FACT_LABELS = {
    "beneficial_owner": "Skutečné vlastnictví příjmu",
    "recipient_is_treaty_resident": "Daňová rezidence pro účely smlouvy",
    "permanent_establishment_connection": "Vazba příjmu ke stálé provozovně v ČR",
    "ownership_percent": "Podíl na základním kapitálu plátce",
    "holding_period_months": "Doba držby podílu",
    "direct_ownership": "Přímé držení podílu",
}


def _result_copy(result: Mapping[str, Any]) -> tuple[str, str]:
    treatment = result.get("tax_treatment")
    if treatment == "exclusive_foreign_taxation":
        return (
            "Příjem se v České republice nezdaňuje",
            "Podle použitého smluvního pravidla se příjem zdaňuje pouze "
            "ve státě daňové rezidence příjemce.",
        )
    if treatment == "domestic_exemption":
        return (
            "Příjem je v České republice osvobozen",
            "Podmínky použitého vnitrostátního osvobození byly podle "
            "zadaných údajů splněny.",
        )
    if result.get("status") == "FINAL" and result.get("rate") is not None:
        return (
            f"Sazba české srážkové daně: {result['rate']} %",
            "Sazba byla určena z uvedených údajů a použitých právních "
            "pravidel.",
        )
    return (
        "Výsledek vyžaduje doplnění údajů",
        "Bez uzavření položek uvedených v části Otevřené body nemá být "
        "výsledek použit pro splnění daňové povinnosti.",
    )


def _source_title(source: Mapping[str, Any]) -> str:
    article = escape(str(source.get("article") or "—"))
    paragraph = source.get("paragraph")
    suffix = f", {escape(str(paragraph))}" if paragraph else ""
    if source.get("legal_layer") in {"treaty", "protocol", "mli"}:
        return f"Smlouva o zamezení dvojího zdanění · článek {article}{suffix}"
    return (
        f"Zákon č. 586/1992 Sb., o daních z příjmů · "
        f"§ {article}{suffix}"
    )


def _report_date(value: Any) -> str:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return f"{parsed.day}. {parsed.month}. {parsed.year}"
    except ValueError:
        return text or "—"


def _income_type_label(value: Any) -> str:
    return {
        "dividend": "Dividendy",
        "interest": "Úroky",
        "royalty": "Licenční poplatky",
    }.get(str(value), str(value or "—"))


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


def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report["scope"]
    result = report["result"]
    calculation = result.get("withholding_tax_calculation")
    schedule = result.get("withholding_compliance_schedule") or {}
    conclusion, conclusion_detail = _result_copy(result)
    treatment = result.get("tax_treatment")
    non_taxing = treatment in {"exclusive_foreign_taxation", "domestic_exemption"}

    amount = scope.get("transaction_amount") or {}
    amount_copy = (
        f"{_format_number(amount.get('amount'))} {escape(str(amount.get('currency') or ''))}".strip()
        if amount else "Neuvedena"
    )

    if calculation and calculation.get("status") == "CALCULATED":
        tax_label = "Česká daň k odvodu" if non_taxing else "Srážková daň"
        rate_value = "Neuplatňuje se" if non_taxing else _format_rate(result.get("rate"))
        exchange = calculation.get("exchange_rate")
        exchange_row = ""
        if exchange:
            source_url = escape(str(exchange.get("source_url") or ""), quote=True)
            exchange_row = f'''<tr><th>Kurz ČNB</th><td>1 {escape(str(exchange.get('currency') or ''))} = {_format_number(exchange.get('czk_per_unit'), maximum_decimals=6)} Kč</td><td>{_report_date(exchange.get('effective_date'))} · <a href="{source_url}">zdroj ČNB ↗</a></td></tr>'''
        calculation_html = f'''
          <table class="calculation-table">
            <tbody>
              <tr><th>Hrubá částka</th><td>{_format_number(calculation.get('gross_amount'))} {escape(str(calculation.get('transaction_currency') or ''))}</td><td>Částka zadaná pro analyzovanou transakci</td></tr>
              <tr><th>Daňový základ</th><td>{_format_number(calculation.get('gross_amount_czk'))} Kč</td><td>Hodnota po přepočtu do CZK</td></tr>
              <tr class="emphasis"><th>{tax_label}</th><td>{_format_number(calculation.get('withholding_tax_czk'))} Kč</td><td>Sazba {rate_value}</td></tr>
              {exchange_row}
            </tbody>
          </table>'''
    else:
        calculation_html = '<p class="empty-note">Částkový výpočet nebyl uzavřen.</p>'

    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    selected_source = next((s for s in report.get("official_sources", []) if s.get("rule_id") == selected_rule_id), None)
    if selected_source and selected_source.get("legal_layer") in {"treaty", "protocol", "mli"}:
        why_result = f"Sazba vychází z {_source_title(selected_source)} a ze skutkových údajů potvrzených pro tuto transakci."
    elif selected_source:
        why_result = f"Výsledek vychází z {_source_title(selected_source)} a ze skutkových údajů potvrzených pro tuto transakci."
    else:
        why_result = "Výsledek vychází ze zadaných údajů a z právních podkladů uvedených v tomto reportu."

    source_items = []
    for source in report.get("official_sources", []):
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        excerpt_html = f"<blockquote>{excerpt}</blockquote>" if excerpt else ""
        source_items.append(f'''<article class="legal-source"><div class="source-head"><h3>{_source_title(source)}</h3><a href="{url}">Oficiální zdroj ↗</a></div>{excerpt_html}</article>''')
    if not source_items:
        source_items.append('<p class="empty-note">Pro tento výsledek nebyl vybrán konkrétní právní zdroj.</p>')

    missing = report.get("missing_facts", [])
    missing_items = "".join(f"<li>{escape(_FACT_LABELS.get(str(item), str(item).replace('_', ' ')))}</li>" for item in missing) or "<li>Žádné otevřené skutkové údaje.</li>"
    documents = "".join(f"<li>{escape(str(item))}</li>" for item in report.get("required_documentation", []))

    deadline_rows = []
    labels = {"reference_date":"Rozhodné datum","remittance_deadline":"Odvod srážkové daně","notification_deadline":"Oznámení příjmu do zahraničí"}
    for key, label in labels.items():
        if schedule.get(key):
            deadline_rows.append(f"<div><span>{label}</span><strong>{_report_date(schedule[key])}</strong></div>")
    compliance_html = "".join(deadline_rows) or '<p class="empty-note">Navazující lhůty nejsou pro tento výsledek k dispozici.</p>'

    return f'''<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><title>TaxTreat · Report srážkové daně</title>
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
.summary-box{{padding:17px 19px;border-left:4px solid var(--forest2);background:#f6f8f6;color:#39524b}} .summary-box p{{margin:0}}
.calculation-table{{width:100%;border-collapse:collapse;border:1px solid var(--line)}} .calculation-table th,.calculation-table td{{padding:13px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} .calculation-table th{{width:24%;color:#536a63;background:#f8f9f7;font-size:11px}} .calculation-table td:nth-child(2){{width:26%;font-weight:750;font-size:14px}} .calculation-table td:nth-child(3){{color:var(--muted);font-size:11px}} .calculation-table .emphasis td,.calculation-table .emphasis th{{background:#edf4f0}} .calculation-table .emphasis td:nth-child(2){{color:var(--forest);font-size:18px}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:28px}} ul{{margin:8px 0 0;padding-left:18px}} li{{margin:5px 0}}
.deadlines{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}} .deadlines div{{padding:14px;border:1px solid var(--line);border-radius:9px;background:#fafbf9}} .deadlines span{{display:block;color:#7b8984;font-size:9px;text-transform:uppercase;font-weight:800;letter-spacing:.05em}} .deadlines strong{{display:block;margin-top:6px}}
.legal-source{{padding:14px 0;border-top:1px solid var(--line)}} .legal-source:first-of-type{{border-top:0}} .source-head{{display:flex;justify-content:space-between;gap:20px}} .legal-source a{{color:var(--forest2);font-weight:700;text-decoration:none;font-size:11px}}
blockquote{{margin:12px 0 0;padding:14px 16px;border-left:3px solid #9ebcb1;background:#f7f9f7;color:#40534d;white-space:pre-line;font:11px/1.55 Georgia,serif}}
.empty-note{{color:var(--muted)}} footer{{padding:18px 34px 24px;color:#78847f;background:#fafaf8;border-top:1px solid var(--line);font-size:9px}}
@media(max-width:720px){{.report{{width:100%;margin:0}} main{{padding:22px}} .hero,.two-col{{grid-template-columns:1fr}} .transaction-strip{{grid-template-columns:1fr 1fr}} .deadlines{{grid-template-columns:1fr}}}}
@media print{{@page{{size:A4;margin:11mm}} body{{background:#fff}} .report{{width:auto;margin:0;box-shadow:none}} .masthead{{print-color-adjust:exact;-webkit-print-color-adjust:exact}} section,.hero,.result-card,.calculation-table{{break-inside:avoid}} .legal-source{{break-inside:auto}} blockquote{{break-inside:auto}} a{{color:inherit;text-decoration:none}}}}
</style></head><body><article class="report">
<header class="masthead"><div><div class="brand"><span class="brand-mark">TT</span>TaxTreat</div><small>Analýza české srážkové daně</small></div><div class="cutoff">Právní stav<br><strong>{_report_date(report.get('legal_data_cutoff'))}</strong></div></header>
<main>
<div class="hero"><div><div class="eyebrow">Daňový report</div><h1>Posouzení srážkové daně</h1><p>Vyhodnocení konkrétní přeshraniční platby z České republiky na základě zadaných skutkových údajů a relevantních právních pravidel.</p></div><aside class="result-card"><span>Závěr</span><strong>{escape(conclusion)}</strong><p>{escape(conclusion_detail)}</p></aside></div>
<div class="transaction-strip"><div><span>Zdroj</span><strong>{escape(str(scope.get('source_country') or '—'))}</strong></div><div><span>Příjemce</span><strong>{escape(str(scope.get('recipient_country') or '—'))}</strong></div><div><span>Příjem</span><strong>{escape(_income_type_label(scope.get('income_type')))}</strong></div><div><span>Datum</span><strong>{_report_date(scope.get('transaction_date'))}</strong></div><div><span>Částka</span><strong>{amount_copy}</strong></div></div>
<section><h2>Výpočet daně</h2>{calculation_html}</section>
<section><h2>Odůvodnění výsledku</h2><div class="summary-box"><p>{why_result}</p></div></section>
<section><h2>Podmínky a doporučené podklady</h2><div class="two-col"><div><h3>Otevřené skutkové údaje</h3><ul>{missing_items}</ul></div><div><h3>Dokumentace k transakci</h3><ul>{documents}</ul></div></div></section>
<section><h2>Daňový kalendář</h2><div class="deadlines">{compliance_html}</div></section>
<section><h2>Právní základ</h2>{''.join(source_items)}</section>
</main><footer>{escape(str(report['disclaimer']))}</footer></article></body></html>'''
