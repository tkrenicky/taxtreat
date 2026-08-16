from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html import escape
from typing import Any, Mapping


REPORT_SCHEMA_VERSION = 3
LEGAL_DATA_CUTOFF = "2026-08-12"
DISCLAIMER = (
    "Výstup byl vytvořen automatizovaným výpočtem z uvedených údajů. "
    "Není právním nebo daňovým poradenstvím a nemá povahu závazného "
    "stanoviska. Před použitím pro splnění daňových povinností má být "
    "posouzen kvalifikovaným daňovým poradcem."
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
            "Před použitím výsledku je vyžadováno doplnění údajů nebo "
            "odborné ověření označených podmínek."
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
        "Výsledek vyžaduje doplnění nebo odborné ověření",
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


def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report["scope"]
    result = report["result"]
    calculation = result.get("withholding_tax_calculation")
    conclusion, conclusion_detail = _result_copy(result)
    treatment = result.get("tax_treatment")
    non_taxing = treatment in {
        "exclusive_foreign_taxation",
        "domestic_exemption",
    }

    if calculation and calculation.get("status") == "CALCULATED":
        tax_label = "Česká daň k odvodu" if non_taxing else "Srážková daň"
        rate_value = (
            "Neuplatňuje se"
            if non_taxing
            else f"{escape(str(result.get('rate')))} %"
        )
        exchange = calculation.get("exchange_rate")
        exchange_row = ""
        if exchange:
            source_url = escape(str(exchange.get("source_url") or ""), quote=True)
            exchange_row = (
                '<div><span>Přepočet ČNB</span><strong>'
                f"1 {escape(str(exchange['currency']))} = "
                f"{escape(str(exchange['czk_per_unit']))} CZK"
                f'</strong><small>{escape(str(exchange["effective_date"]))} · '
                f'<a href="{source_url}">kurzovní lístek</a></small></div>'
            )
        calculation_html = f"""
          <div class="number-grid">
            <div><span>Hrubá částka</span><strong>{escape(str(calculation['gross_amount']))} {escape(str(calculation['transaction_currency']))}</strong></div>
            <div><span>Daňový základ v CZK</span><strong>{escape(str(calculation['gross_amount_czk']))} Kč</strong></div>
            <div class="accent"><span>{tax_label}</span><strong>{escape(str(calculation['withholding_tax_czk']))} Kč</strong></div>
            <div><span>Použitá sazba</span><strong>{rate_value}</strong></div>
            {exchange_row}
          </div>"""
    else:
        calculation_html = (
            '<p class="muted">Částkový výpočet nebyl uzavřen. Důvod: '
            f"{escape(str((calculation or {}).get('reason') or 'částka nebyla zadána'))}.</p>"
        )

    source_items = []
    for index, source in enumerate(report.get("official_sources", []), 1):
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        excerpt_html = (
            f"<details><summary>Zobrazit znění ustanovení</summary><blockquote>{excerpt}</blockquote></details>"
            if excerpt
            else ""
        )
        source_items.append(
            '<article class="source">'
            f'<span class="source-number">{index:02d}</span><div><h3>{_source_title(source)}</h3>'
            f'<a href="{url}">Otevřít oficiální zdroj ↗</a>{excerpt_html}</div></article>'
        )
    if not source_items:
        source_items.append('<p class="muted">Nebyl vybrán konkrétní právní zdroj.</p>')

    missing = report.get("missing_facts", [])
    missing_items = "".join(
        f"<li>{escape(_FACT_LABELS.get(str(item), str(item).replace('_', ' ')))}</li>"
        for item in missing
    ) or "<li>Žádné otevřené skutkové údaje.</li>"
    documents = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in report.get("required_documentation", [])
    )
    amount = scope.get("transaction_amount") or {}
    amount_copy = (
        f"{escape(str(amount.get('amount')))} {escape(str(amount.get('currency')))}"
        if amount
        else "Neuvedena"
    )

    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>TaxTreat · {escape(str(report['report_id']))}</title>
  <style>
    :root {{ --ink:#10233e; --paper:#fffdf8; --canvas:#f0ece2; --line:#d9d1c2; --copper:#a85f32; --sage:#315c55; --muted:#687386; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--canvas); font:15px/1.55 Inter, ui-sans-serif, system-ui, sans-serif; }}
    .sheet {{ width:min(1080px,calc(100% - 40px)); margin:34px auto; padding:58px 64px; background:var(--paper); box-shadow:0 18px 55px #2b35401a; }}
    header {{ display:grid; grid-template-columns:1fr auto; gap:40px; padding-bottom:34px; border-bottom:1px solid var(--line); }}
    .brand {{ font-size:13px; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:var(--copper); }}
    h1 {{ max-width:650px; margin:12px 0 8px; font:700 42px/1.08 Georgia, serif; letter-spacing:-.025em; }}
    h2 {{ margin:0 0 18px; font:700 24px/1.2 Georgia, serif; }} h3 {{ margin:0 0 5px; font-size:15px; }}
    p {{ margin:0; }} .muted,.meta {{ color:var(--muted); }} .meta {{ font-size:12px; text-align:right; }}
    .meta strong {{ display:block; margin-bottom:8px; color:var(--ink); font-size:13px; }}
    .scope {{ display:grid; grid-template-columns:repeat(4,1fr); gap:0; margin:30px 0 0; border:1px solid var(--line); }}
    .scope div {{ padding:14px 16px; border-right:1px solid var(--line); }} .scope div:last-child {{ border:0; }}
    .scope span,.number-grid span {{ display:block; color:var(--muted); font-size:11px; letter-spacing:.06em; text-transform:uppercase; }}
    .scope strong {{ display:block; margin-top:5px; }}
    .verdict {{ margin:34px 0 0; padding:34px 38px; color:white; background:var(--ink); border-left:9px solid var(--copper); }}
    .verdict .eyebrow {{ color:#e4b28f; font-size:11px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }}
    .verdict h2 {{ margin:9px 0; color:white; font-size:30px; }} .verdict p {{ max-width:760px; color:#dce4ee; }}
    section.numbered {{ display:grid; grid-template-columns:52px 1fr; gap:22px; padding:40px 0; border-bottom:1px solid var(--line); }}
    .section-no {{ color:var(--copper); font:700 18px Georgia,serif; }}
    .number-grid {{ display:grid; grid-template-columns:repeat(2,1fr); border-top:1px solid var(--line); border-left:1px solid var(--line); }}
    .number-grid>div {{ min-height:90px; padding:17px 18px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); }}
    .number-grid strong {{ display:block; margin-top:8px; font-size:20px; }} .number-grid small {{ display:block; margin-top:5px; color:var(--muted); }}
    .number-grid .accent strong {{ color:var(--copper); font-size:25px; }} a {{ color:var(--sage); }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:42px; }} ul {{ margin:0; padding-left:20px; }} li {{ margin:7px 0; }}
    .source {{ display:grid; grid-template-columns:42px 1fr; gap:14px; padding:18px 0; border-top:1px solid var(--line); }}
    .source-number {{ color:var(--copper); font:700 16px Georgia,serif; }} details {{ margin-top:9px; }} summary {{ cursor:pointer; color:var(--sage); font-weight:700; }}
    blockquote {{ max-height:230px; overflow:auto; margin:12px 0 0; padding:15px 18px; white-space:pre-line; color:#38465a; background:#f4f0e8; border-left:3px solid var(--line); font-size:13px; }}
    footer {{ display:grid; grid-template-columns:1fr auto; gap:35px; padding-top:30px; color:var(--muted); font-size:11px; }}
    footer .notice {{ max-width:720px; padding-left:14px; border-left:3px solid var(--copper); }}
    @media(max-width:760px) {{ .sheet{{width:100%;margin:0;padding:34px 22px}} header,.two-col{{grid-template-columns:1fr}} .meta{{text-align:left}} .scope{{grid-template-columns:1fr 1fr}} .scope div:nth-child(2){{border-right:0}} section.numbered{{grid-template-columns:1fr}} }}
    @media print {{ @page{{size:A4;margin:14mm}} body{{background:white}} .sheet{{width:auto;margin:0;padding:0;box-shadow:none}} section.numbered,.verdict,.source{{break-inside:avoid}} a{{color:inherit;text-decoration:none}} }}
  </style>
</head>
<body><main class="sheet">
  <header><div><div class="brand">TaxTreat · výstup kontroly platby</div><h1>Česká srážková daň</h1><p class="muted">Jednotný záznam vstupních údajů, výsledku, výpočtu a použitých podkladů.</p></div>
    <div class="meta"><strong>{escape(str(report['report_id']))}</strong>Vytvořeno {escape(str(report['generated_at']))}<br>Právní stav k {escape(str(report['legal_data_cutoff']))}</div></header>
  <div class="scope"><div><span>Plátce / zdroj</span><strong>{escape(str(scope['source_country']))}</strong></div><div><span>Rezidence příjemce</span><strong>{escape(str(scope['recipient_country']))}</strong></div><div><span>Druh příjmu</span><strong>{escape(str(scope['income_type']))}</strong></div><div><span>Částka</span><strong>{amount_copy}</strong></div></div>
  <section class="verdict"><div class="eyebrow">Závěr kontroly</div><h2>{escape(conclusion)}</h2><p>{escape(conclusion_detail)}</p></section>
  <section class="numbered"><span class="section-no">01</span><div><h2>Výpočet a daňové zacházení</h2>{calculation_html}<p class="muted" style="margin-top:14px">{escape(str(report['risk_assessment']))}</p></div></section>
  <section class="numbered"><span class="section-no">02</span><div><h2>Údaje a podklady</h2><div class="two-col"><div><h3>Otevřené body</h3><ul>{missing_items}</ul></div><div><h3>Dokumentace k založení</h3><ul>{documents}</ul></div></div></div></section>
  <section class="numbered"><span class="section-no">03</span><div><h2>Použité právní podklady</h2>{''.join(source_items)}</div></section>
  <footer><p class="notice">{escape(str(report['disclaimer']))}</p><p>TaxTreat<br>{escape(str(report['report_id']))}</p></footer>
</main></body></html>"""
