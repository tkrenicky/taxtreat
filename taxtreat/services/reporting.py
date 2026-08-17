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
        risk = "Výsledek byl určen z uvolněného katalogu právních pravidel."
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


def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report["scope"]
    result = report["result"]
    calculation = result.get("withholding_tax_calculation")
    schedule = result.get("withholding_compliance_schedule") or {}
    conclusion, conclusion_detail = _result_copy(result)
    treatment = result.get("tax_treatment")
    non_taxing = treatment in {"exclusive_foreign_taxation", "domestic_exemption"}

    if calculation and calculation.get("status") == "CALCULATED":
        tax_label = "Česká daň k odvodu" if non_taxing else "Srážková daň"
        rate_value = "Neuplatňuje se" if non_taxing else f"{escape(str(result.get('rate')))} %"
        exchange = calculation.get("exchange_rate")
        exchange_row = ""
        if exchange:
            source_url = escape(str(exchange.get("source_url") or ""), quote=True)
            exchange_row = (
                '<div class="metric"><span>Přepočet ČNB</span><strong>'
                f"1 {escape(str(exchange['currency']))} = {escape(str(exchange['czk_per_unit']))} CZK"
                f'</strong><small>{_report_date(exchange.get("effective_date"))} · '
                f'<a href="{source_url}">kurzovní lístek ČNB</a></small></div>'
            )
        calculation_html = f"""
        <div class="metric-grid">
          <div class="metric"><span>Hrubá částka</span><strong>{escape(str(calculation['gross_amount']))} {escape(str(calculation['transaction_currency']))}</strong></div>
          <div class="metric"><span>Daňový základ</span><strong>{escape(str(calculation['gross_amount_czk']))} Kč</strong></div>
          <div class="metric primary-metric"><span>{tax_label}</span><strong>{escape(str(calculation['withholding_tax_czk']))} Kč</strong></div>
          <div class="metric"><span>Použitá sazba</span><strong>{rate_value}</strong></div>
          {exchange_row}
        </div>"""
    else:
        calculation_html = '<p class="note">Částkový výpočet nebyl uzavřen.</p>'

    source_items: list[str] = []
    for source in report.get("official_sources", []):
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        excerpt_html = (
            f"<details><summary>Zobrazit přesné znění ustanovení</summary><blockquote>{excerpt}</blockquote></details>"
            if excerpt else ""
        )
        source_items.append(
            '<article class="legal-source"><div><h3>'
            f'{_source_title(source)}</h3><a href="{url}">Otevřít zdroj ↗</a></div>{excerpt_html}</article>'
        )
    if not source_items:
        source_items.append('<p class="note">Pro tento výsledek nebyl vybrán konkrétní právní zdroj.</p>')

    missing = report.get("missing_facts", [])
    missing_items = "".join(
        f"<li>{escape(_FACT_LABELS.get(str(item), str(item).replace('_', ' ')))}</li>" for item in missing
    ) or "<li>Žádné otevřené skutkové údaje.</li>"
    documents = "".join(f"<li>{escape(str(item))}</li>" for item in report.get("required_documentation", []))
    amount = scope.get("transaction_amount") or {}
    amount_copy = f"{escape(str(amount.get('amount')))} {escape(str(amount.get('currency')))}" if amount else "Neuvedena"

    deadline_rows = []
    labels = {
        "reference_date": "Rozhodné datum",
        "remittance_deadline": "Odvod srážkové daně",
        "notification_deadline": "Oznámení příjmu do zahraničí",
    }
    for key, label in labels.items():
        value = schedule.get(key)
        if value:
            deadline_rows.append(f"<div><span>{label}</span><strong>{_report_date(value)}</strong></div>")
    compliance_html = "".join(deadline_rows) or '<p class="note">Navazující lhůty nejsou pro tento výsledek k dispozici.</p>'

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>TaxTreat · Analýza srážkové daně</title>
  <style>
    :root {{ --navy:#172b4d; --blue:#3157d5; --ink:#172033; --muted:#657085; --line:#dfe4ec; --soft:#f5f7fb; --paper:#ffffff; --green:#176c4f; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:#edf1f6; font:14px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }}
    .report {{ width:min(1040px,calc(100% - 36px)); margin:28px auto; background:var(--paper); box-shadow:0 16px 50px #172b4d14; }}
    header {{ display:flex; justify-content:space-between; gap:28px; padding:28px 38px; color:#fff; background:var(--navy); }}
    .brand {{ font-size:20px; font-weight:800; letter-spacing:-.02em; }}
    .brand span {{ display:inline-grid; place-items:center; width:34px; height:34px; margin-right:10px; border-radius:8px; color:#fff; background:var(--blue); font-size:12px; vertical-align:middle; }}
    header p {{ margin:5px 0 0; color:#cbd6e7; }} header .cutoff {{ align-self:center; text-align:right; font-size:12px; }}
    main {{ padding:34px 38px 42px; }}
    h1 {{ margin:0; font-size:30px; letter-spacing:-.035em; }} h2 {{ margin:0 0 16px; color:var(--navy); font-size:20px; }} h3 {{ margin:0 0 5px; font-size:14px; }}
    .transaction {{ margin-bottom:26px; padding:24px; border:1px solid #cad5e7; border-top:5px solid var(--blue); background:#fbfcff; }}
    .transaction .eyebrow,.verdict .eyebrow {{ color:var(--blue); font-size:11px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }}
    .transaction h1 {{ margin:6px 0 20px; }}
    .transaction-grid {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); border:1px solid var(--line); background:#fff; }}
    .transaction-grid div {{ min-height:72px; padding:13px 14px; border-right:1px solid var(--line); }} .transaction-grid div:last-child {{ border-right:0; }}
    .transaction-grid span,.metric span,.deadline-grid span {{ display:block; color:var(--muted); font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
    .transaction-grid strong {{ display:block; margin-top:6px; font-size:14px; }}
    .verdict {{ margin-bottom:30px; padding:25px 28px; border-left:5px solid var(--blue); background:#eef3ff; }}
    .verdict h2 {{ margin:7px 0 7px; font-size:25px; }} .verdict p {{ max-width:780px; color:#46536a; }}
    section {{ padding:26px 0; border-top:1px solid var(--line); }}
    .metric-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid var(--line); border-left:1px solid var(--line); }}
    .metric {{ min-height:88px; padding:16px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); }} .metric strong {{ display:block; margin-top:7px; font-size:19px; }} .metric small {{ display:block; margin-top:4px; color:var(--muted); }}
    .primary-metric {{ background:#f0f4ff; }} .primary-metric strong {{ color:var(--blue); font-size:24px; }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:34px; }} ul {{ margin:0; padding-left:18px; }} li {{ margin:7px 0; }}
    .deadline-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }} .deadline-grid div {{ padding:14px; border:1px solid var(--line); background:var(--soft); }} .deadline-grid strong {{ display:block; margin-top:5px; }}
    .legal-source {{ padding:16px 0; border-top:1px solid var(--line); }} .legal-source:first-of-type {{ border-top:0; }} .legal-source a {{ color:var(--blue); font-weight:700; text-decoration:none; }}
    details {{ margin-top:10px; }} summary {{ cursor:pointer; color:var(--blue); font-weight:700; }} blockquote {{ max-height:260px; overflow:auto; margin:12px 0 0; padding:15px 17px; white-space:pre-line; color:#334158; background:var(--soft); border-left:3px solid #b9c7e7; font-size:12px; }}
    .note {{ color:var(--muted); }} .risk {{ margin-top:12px; color:#4c596e; }}
    footer {{ padding:20px 38px 26px; border-top:1px solid var(--line); color:var(--muted); background:#fafbfc; font-size:10px; }}
    @media(max-width:760px) {{ .report{{width:100%;margin:0}} header{{display:block}} header .cutoff{{margin-top:16px;text-align:left}} main{{padding:24px 20px}} .transaction-grid{{grid-template-columns:1fr 1fr}} .transaction-grid div{{border-bottom:1px solid var(--line)}} .metric-grid,.two-col,.deadline-grid{{grid-template-columns:1fr}} }}
    @media print {{ @page{{size:A4;margin:13mm}} body{{background:#fff}} .report{{width:auto;margin:0;box-shadow:none}} header{{print-color-adjust:exact;-webkit-print-color-adjust:exact}} section,.verdict,.transaction,.legal-source{{break-inside:avoid}} a{{color:inherit;text-decoration:none}} details{{display:block}} }}
  </style>
</head>
<body><article class="report">
  <header><div><div class="brand"><span>TT</span>TaxTreat</div><p>Withholding tax analysis</p></div><div class="cutoff">Právní stav k {_report_date(report.get('legal_data_cutoff'))}</div></header>
  <main>
    <section class="transaction"><div class="eyebrow">Analyzovaná transakce</div><h1>Česká srážková daň</h1><div class="transaction-grid">
      <div><span>Zdroj příjmu</span><strong>{escape(str(scope.get('source_country') or '—'))}</strong></div>
      <div><span>Rezidence příjemce</span><strong>{escape(str(scope.get('recipient_country') or '—'))}</strong></div>
      <div><span>Druh příjmu</span><strong>{escape(_income_type_label(scope.get('income_type')))}</strong></div>
      <div><span>Datum transakce</span><strong>{_report_date(scope.get('transaction_date'))}</strong></div>
      <div><span>Částka</span><strong>{amount_copy}</strong></div>
    </div></section>
    <section class="verdict"><div class="eyebrow">Výsledek</div><h2>{escape(conclusion)}</h2><p>{escape(conclusion_detail)}</p></section>
    <section><h2>Výpočet</h2>{calculation_html}<p class="risk">{escape(str(report['risk_assessment']))}</p></section>
    <section><h2>Podmínky a podklady</h2><div class="two-col"><div><h3>Otevřené skutkové údaje</h3><ul>{missing_items}</ul></div><div><h3>Podklady k dokumentaci</h3><ul>{documents}</ul></div></div></section>
    <section><h2>Daňový kalendář</h2><div class="deadline-grid">{compliance_html}</div></section>
    <section><h2>Právní základ</h2>{''.join(source_items)}</section>
  </main>
  <footer>{escape(str(report['disclaimer']))}</footer>
</article></body></html>"""
