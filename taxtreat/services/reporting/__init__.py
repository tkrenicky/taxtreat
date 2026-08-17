from __future__ import annotations

import importlib.util
from html import escape
from pathlib import Path
from typing import Any, Mapping


# Keep the stable report schema/data builder from the existing module and replace
# only the presentation layer. The package intentionally shadows reporting.py.
_LEGACY_PATH = Path(__file__).resolve().parent.parent / "reporting.py"
_SPEC = importlib.util.spec_from_file_location("taxtreat.services._reporting_data", _LEGACY_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Unable to load report data model")
_DATA = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DATA)

REPORT_SCHEMA_VERSION = _DATA.REPORT_SCHEMA_VERSION
LEGAL_DATA_CUTOFF = _DATA.LEGAL_DATA_CUTOFF
DISCLAIMER = _DATA.DISCLAIMER
stable_report_id = _DATA.stable_report_id
build_professional_report = _DATA.build_professional_report


_FACT_LABELS = {
    "beneficial_owner": "Skutečné vlastnictví příjmu",
    "recipient_is_treaty_resident": "Daňová rezidence pro účely smlouvy",
    "permanent_establishment_connection": "Vazba příjmu ke stálé provozovně v ČR",
    "ownership_percent": "Podíl na základním kapitálu plátce",
    "holding_period_months": "Doba držby podílu",
    "direct_ownership": "Přímé držení podílu",
    "voting_ownership_percent": "Podíl na hlasovacích právech",
    "royalty_category": "Předmět licenční platby",
    "arm_length_amount": "Tržní výše úroku",
}


def _date(value: Any) -> str:
    text = str(value or "")
    try:
        from datetime import datetime
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return f"{parsed.day}. {parsed.month}. {parsed.year}"
    except ValueError:
        return text or "—"


def _number(value: Any, decimals: int = 2) -> str:
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if number.is_integer():
        rendered = f"{int(number):,}"
    else:
        rendered = f"{number:,.{decimals}f}".rstrip("0").rstrip(".")
    return rendered.replace(",", " ")


def _rate(value: Any) -> str:
    return "—" if value in (None, "") else f"{_number(value)} %"


def _income(value: Any) -> str:
    return {
        "dividend": "Dividendy",
        "interest": "Úroky",
        "royalty": "Licenční poplatky",
    }.get(str(value), str(value or "—"))


def _article(source: Mapping[str, Any]) -> str:
    article = str(source.get("article") or "—")
    paragraph = source.get("paragraph")
    suffix = f" odst. {paragraph}" if paragraph not in (None, "") else ""
    if source.get("legal_layer") in {"treaty", "protocol", "mli"}:
        return f"čl. {article}{suffix}"
    return f"§ {article}{suffix}"


def _source_title(source: Mapping[str, Any]) -> str:
    ref = escape(_article(source))
    layer = source.get("legal_layer")
    instrument = str(source.get("legal_instrument") or "").strip()
    if layer == "treaty":
        return f"Smlouva o zamezení dvojího zdanění · {ref}"
    if layer == "protocol":
        return f"Protokol ke smlouvě o zamezení dvojího zdanění · {ref}"
    if layer == "mli":
        return f"Mnohostranná úmluva MLI · {ref}"
    if instrument:
        return f"{escape(instrument)} · {ref}"
    return f"Zákon č. 586/1992 Sb., o daních z příjmů · {ref}"


def _source_sentence(source: Mapping[str, Any] | None) -> str:
    if not source:
        return "příslušného právního pravidla uvedeného v části Právní základ"
    ref = _article(source)
    layer = source.get("legal_layer")
    if layer == "treaty":
        return f"{ref} příslušné smlouvy o zamezení dvojího zdanění"
    if layer == "protocol":
        return f"{ref} příslušného protokolu ke smlouvě o zamezení dvojího zdanění"
    if layer == "mli":
        return f"{ref} Mnohostranné úmluvy MLI"
    return f"{ref} zákona č. 586/1992 Sb., o daních z příjmů"


def _layer(value: Any) -> str:
    return {
        "domestic": "Vnitrostátní právo",
        "treaty": "Smlouva",
        "protocol": "Protokol",
        "mli": "MLI",
    }.get(str(value or ""), str(value or "Právní zdroj"))


def _result(result: Mapping[str, Any], source: Mapping[str, Any] | None) -> tuple[str, str, str]:
    reference = _source_sentence(source)
    treatment = result.get("tax_treatment")
    if treatment == "exclusive_foreign_taxation":
        return (
            "Bez české srážkové daně",
            "0 %",
            f"Podle {reference} se při zadaných skutečnostech česká srážková daň neuplatní.",
        )
    if treatment == "domestic_exemption":
        return (
            "Osvobození v České republice",
            "0 %",
            f"Podle {reference} jsou při zadaných skutečnostech splněny podmínky použitého osvobození.",
        )
    if result.get("status") == "FINAL" and result.get("rate") is not None:
        rate = _rate(result.get("rate"))
        return (
            "Sazba české srážkové daně",
            rate,
            f"Podle {reference} činí sazba použitá pro zadanou platbu {rate}.",
        )
    return (
        "Výsledek není uzavřen",
        "—",
        "Zadané údaje zatím neumožňují uzavřít použitelnou sazbu nebo režim. Otevřené body jsou uvedeny dále v reportu.",
    )


def _source_cards(sources: list[Mapping[str, Any]], selected_rule_id: Any) -> str:
    if not sources:
        return '<p class="empty">Pro tento výstup nebyl evidován konkrétní právní zdroj.</p>'
    cards: list[str] = []
    for index, source in enumerate(sources, start=1):
        selected = source.get("rule_id") == selected_rule_id
        url = escape(str(source.get("source_url") or ""), quote=True)
        excerpt = escape(str(source.get("excerpt") or ""))
        badge = '<span class="badge selected">Použité pravidlo</span>' if selected else f'<span class="badge">{escape(_layer(source.get("legal_layer")))}</span>'
        meta = []
        if source.get("rate") not in (None, ""):
            meta.append(f"sazba {_rate(source.get('rate'))}")
        if source.get("source_id"):
            meta.append(f"ID {escape(str(source.get('source_id')))}")
        excerpt_html = f'<div class="quote"><span>Relevantní výňatek</span><p>{excerpt}</p></div>' if excerpt else ""
        link = f'<a href="{url}">Otevřít oficiální zdroj ↗</a>' if url else ""
        cards.append(f'''<article class="source-card{' is-selected' if selected else ''}">
          <div class="source-no">{index:02d}</div>
          <div><div class="source-eyebrow">{badge}<span>{escape(_layer(source.get('legal_layer')))}</span></div>
          <h3>{_source_title(source)}</h3><small>{' · '.join(meta)}</small>{excerpt_html}{link}</div>
        </article>''')
    return "".join(cards)


def _analysis_steps(report: Mapping[str, Any], selected_source: Mapping[str, Any] | None) -> str:
    rows: list[str] = []
    if selected_source:
        rows.append(f'''<div class="step primary-step"><span>01</span><div><b>Rozhodující právní pravidlo</b><p>{escape(_source_sentence(selected_source).capitalize())}.</p></div></div>''')
    for index, item in enumerate([str(x) for x in report.get("explanation", []) if x][:4], start=2):
        rows.append(f'''<div class="step"><span>{index:02d}</span><div><b>Vyhodnocený krok</b><p>{escape(item)}</p></div></div>''')
    if len(rows) <= (1 if selected_source else 0):
        rows.append('<div class="step"><span>02</span><div><b>Skutkové údaje</b><p>Výsledek vychází z údajů uvedených v přehledu transakce a z podmínek evidovaných pro daný typ příjmu.</p></div></div>')
    return "".join(rows)


def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report["scope"]
    result = report["result"]
    calculation = result.get("withholding_tax_calculation") or {}
    schedule = result.get("withholding_compliance_schedule") or {}
    sources = list(report.get("official_sources", []))
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    selected_source = next((s for s in sources if s.get("rule_id") == selected_rule_id), None)
    headline, headline_value, conclusion = _result(result, selected_source)

    amount = scope.get("transaction_amount") or {}
    amount_text = f"{_number(amount.get('amount'))} {escape(str(amount.get('currency') or ''))}".strip() if amount else "—"
    pair = f"{escape(str(scope.get('source_country') or '—'))} → {escape(str(scope.get('recipient_country') or '—'))}"
    tax_czk = "—"
    base_czk = "—"
    fx_html = ""
    if calculation.get("status") == "CALCULATED":
        tax_czk = f"{_number(calculation.get('withholding_tax_czk'))} Kč"
        base_czk = f"{_number(calculation.get('gross_amount_czk'))} Kč"
        fx = calculation.get("exchange_rate") or {}
        if fx:
            url = escape(str(fx.get("source_url") or ""), quote=True)
            link = f'<a href="{url}">Kurzovní lístek ČNB ↗</a>' if url else ""
            fx_html = f'''<div class="fx"><b>Přepočet měny</b><span>1 {escape(str(fx.get('currency') or ''))} = {_number(fx.get('czk_per_unit'), 6)} Kč · {_date(fx.get('effective_date'))} · {link}</span></div>'''

    refs = []
    for source in sources[:4]:
        url = escape(str(source.get("source_url") or ""), quote=True)
        text = escape(_source_sentence(source))
        refs.append(f'<a href="{url}">{text} ↗</a>' if url else f'<span>{text}</span>')
    refs_html = "".join(refs) or '<span>Právní reference nejsou k dispozici.</span>'

    missing = report.get("missing_facts", [])
    missing_html = "".join(f"<li>{escape(_FACT_LABELS.get(str(x), str(x).replace('_', ' ')))}</li>" for x in missing) or "<li>Žádné otevřené skutkové údaje.</li>"
    docs_html = "".join(f"<li>{escape(str(x))}</li>" for x in report.get("required_documentation", []))

    deadlines = []
    for key, label in (("reference_date", "Rozhodné datum"), ("remittance_deadline", "Odvod srážkové daně"), ("notification_deadline", "Oznámení příjmu do zahraničí")):
        if schedule.get(key):
            deadlines.append(f'<div class="deadline"><span>{label}</span><b>{_date(schedule[key])}</b></div>')
    deadlines_html = "".join(deadlines) or '<p class="empty">Navazující lhůty nejsou pro tento výsledek k dispozici.</p>'

    report_id = escape(str(report.get("report_id") or "—"))
    generated = _date(report.get("generated_at"))
    cutoff = _date(report.get("legal_data_cutoff"))
    dataset = escape(str(report.get("legal_dataset_release") or report.get("source_release") or "—"))
    source_cards = _source_cards(sources, selected_rule_id)
    analysis = _analysis_steps(report, selected_source)

    return f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TaxTreat · Informace k české srážkové dani</title>
<style>
:root{{--forest:#173f39;--forest2:#2b5d52;--sage:#dce8e1;--sage2:#edf3ef;--cream:#f3f0e8;--paper:#fffdf9;--ink:#17312b;--text:#334943;--muted:#75837e;--line:#dfe4df}}
*{{box-sizing:border-box}}html,body{{margin:0;background:#e9e6de;color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Arial,sans-serif}}a{{color:var(--forest2);text-decoration:none;border-bottom:1px solid #9cb7ad}}
.report{{width:210mm;margin:20px auto;background:var(--paper);box-shadow:0 18px 60px #173f3920}}.page{{position:relative;min-height:297mm;padding:20mm 18mm 18mm;page-break-after:always;background:var(--paper)}}.page:last-child{{page-break-after:auto}}.topline{{height:5px;position:absolute;top:0;left:0;right:0;background:var(--forest)}}
.page-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:18mm}}.brand{{display:flex;align-items:center;gap:10px;color:var(--forest);font-size:18px;font-weight:800;letter-spacing:-.03em}}.brandmark{{display:grid;place-items:center;width:34px;height:34px;border-radius:9px;background:var(--forest);color:#fff;font-size:10px}}.docmeta{{text-align:right;color:var(--muted);font-size:9px;line-height:1.5}}.docmeta b{{display:block;color:var(--ink);font-size:10px}}
.kicker,.mini-label{{display:block;margin:0 0 6px;color:var(--forest2);font-size:8px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}}h1{{max-width:130mm;margin:0;color:var(--ink);font:700 31px/1.08 Georgia,"Times New Roman",serif;letter-spacing:-.025em}}.lead{{max-width:135mm;margin:11px 0 0;color:#64736e;font-size:12px;line-height:1.65}}
.transaction{{display:grid;grid-template-columns:1.1fr 1fr 1fr 1fr;margin:12mm 0 10mm;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.transaction div{{padding:11px 12px 12px 0}}.transaction span{{display:block;margin-bottom:5px;color:var(--muted);font-size:8px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}.transaction b{{color:var(--ink);font-size:11px}}
.result-band{{display:grid;grid-template-columns:1.3fr .7fr;gap:18px;padding:9mm;border:1px solid #d6e2dc;border-radius:13px;background:var(--sage2)}}.result-copy h2{{margin:0 0 8px;color:var(--forest);font:700 22px/1.15 Georgia,"Times New Roman",serif}}.result-copy p{{margin:0;color:#415951;font-size:11px;line-height:1.7}}.result-value{{display:flex;flex-direction:column;justify-content:center;padding-left:18px;border-left:1px solid #cbdad3}}.result-value span{{color:var(--muted);font-size:8px;font-weight:800;letter-spacing:.09em;text-transform:uppercase}}.result-value strong{{margin-top:6px;color:var(--forest);font-size:34px;line-height:1}}
.references{{margin-top:8mm;padding-top:5mm;border-top:1px solid var(--line)}}.references h3{{margin:0 0 7px;color:var(--ink);font-size:10px}}.references div{{display:flex;flex-wrap:wrap;gap:7px 12px;font-size:9px}}
.section-title{{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:8mm;padding-bottom:4mm;border-bottom:1px solid var(--line)}}.section-title h2{{margin:0;color:var(--ink);font:700 24px/1.1 Georgia,"Times New Roman",serif}}.section-title span{{color:var(--muted);font-size:9px}}
.calc-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:8mm}}.calc-box{{min-height:27mm;padding:5mm;border:1px solid var(--line);border-radius:10px;background:#fff}}.calc-box.primary{{background:var(--forest);border-color:var(--forest)}}.calc-box span{{display:block;color:var(--muted);font-size:8px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}.calc-box b{{display:block;margin-top:7px;color:var(--ink);font-size:19px}}.calc-box.primary span{{color:#bcd0c9}}.calc-box.primary b{{color:#fff}}.fx{{display:flex;justify-content:space-between;gap:20px;padding:4mm 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);font-size:9px}}.fx b{{color:var(--ink)}}.fx span{{text-align:right;color:var(--muted)}}
.steps{{margin-top:10mm}}.step{{display:grid;grid-template-columns:10mm 1fr;gap:4mm;padding:5mm 0;border-top:1px solid var(--line)}}.step>span{{color:#9caaa5;font:700 11px Georgia,serif}}.step b{{display:block;color:var(--ink);font-size:11px}}.step p{{margin:5px 0 0;color:#52655f;font-size:10px;line-height:1.55}}.primary-step>span{{color:var(--forest2)}}.prose{{margin-top:8mm;padding:6mm 7mm;border-left:3px solid var(--forest2);background:#f7f9f7}}.prose p{{margin:0;font-size:11px;line-height:1.7}}
.source-card{{display:grid;grid-template-columns:13mm 1fr;gap:5mm;padding:6mm 0;border-top:1px solid var(--line);break-inside:avoid}}.source-card:first-child{{border-top:0}}.source-no{{color:#9aa8a3;font:700 18px/1 Georgia,serif}}.source-eyebrow{{display:flex;align-items:center;gap:8px;margin-bottom:4px;color:var(--muted);font-size:8px;text-transform:uppercase;letter-spacing:.07em}}.source-card h3{{margin:0;color:var(--ink);font:700 14px/1.25 Georgia,serif}}.source-card small{{display:block;margin-top:5px;color:var(--muted);font-size:8px}}.badge{{padding:3px 6px;border-radius:999px;background:#efeee8;color:#6f766f;font-size:7px;font-weight:800}}.badge.selected{{background:var(--sage);color:var(--forest)}}.quote{{margin:4mm 0;padding:4mm 5mm;background:#f7f7f3;border-left:2px solid #9fb9af}}.quote span{{display:block;color:var(--muted);font-size:7px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}.quote p{{margin:5px 0 0;color:#4f5c57;font:10px/1.55 Georgia,"Times New Roman",serif;white-space:pre-line}}.source-card a{{display:inline-block;margin-top:4mm;font-size:9px;font-weight:700}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:10mm}}.panel{{padding:6mm;border:1px solid var(--line);border-radius:10px;background:#fff}}.panel h3{{margin:0 0 4mm;color:var(--ink);font-size:12px}}.panel ul{{margin:0;padding-left:17px}}.panel li{{margin:0 0 7px;font-size:9px;line-height:1.5}}.deadline-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:9mm}}.deadline{{padding:5mm;border-top:3px solid var(--forest2);background:#f7f9f7}}.deadline span{{display:block;color:var(--muted);font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}}.deadline b{{display:block;margin-top:7px;color:var(--ink);font-size:13px}}
.metadata{{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--line);border-left:1px solid var(--line);margin-top:8mm}}.metadata div{{padding:4mm;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}}.metadata span{{display:block;color:var(--muted);font-size:7px;text-transform:uppercase;letter-spacing:.08em}}.metadata b{{display:block;margin-top:4px;color:var(--ink);font-size:9px;word-break:break-word}}.disclaimer{{margin-top:10mm;padding-top:5mm;border-top:1px solid var(--line);color:#7c8984;font-size:8px;line-height:1.6}}.page-number{{position:absolute;left:18mm;right:18mm;bottom:8mm;display:flex;justify-content:space-between;color:#99a49f;font-size:7px}}.page-number b{{color:#687872}}.empty{{color:var(--muted);font-size:10px}}
@media(max-width:850px){{.report{{width:100%;margin:0}}.page{{min-height:auto;padding:28px 20px 55px}}.transaction{{grid-template-columns:1fr 1fr}}.result-band,.two-col{{grid-template-columns:1fr}}.result-value{{border-left:0;border-top:1px solid #cbdad3;padding:16px 0 0}}.calc-grid,.deadline-grid{{grid-template-columns:1fr}}}}
@media print{{@page{{size:A4;margin:0}}html,body{{background:#fff}}.report{{width:210mm;margin:0;box-shadow:none}}.page{{min-height:297mm;break-after:page}}.page:last-child{{break-after:auto}}a{{color:inherit;text-decoration:none;border-bottom:0}}.topline,.result-band,.calc-box.primary,.badge.selected{{print-color-adjust:exact;-webkit-print-color-adjust:exact}}}}
</style></head><body><article class="report">
<section class="page"><div class="topline"></div><header class="page-head"><div class="brand"><span class="brandmark">TT</span>TaxTreat</div><div class="docmeta"><b>Informace k české srážkové dani</b>Report {report_id}<br>Vygenerováno {generated}</div></header><p class="kicker">Přehled transakce a výsledku</p><h1>{escape(_income(scope.get('income_type')))} · {pair}</h1><p class="lead">Přehled vychází z údajů zadaných pro konkrétní platbu a z právních zdrojů uvedených v tomto reportu.</p><div class="transaction"><div><span>Typ příjmu</span><b>{escape(_income(scope.get('income_type')))}</b></div><div><span>Datum transakce</span><b>{_date(scope.get('transaction_date'))}</b></div><div><span>Hrubá částka</span><b>{amount_text}</b></div><div><span>Jurisdikce</span><b>{pair}</b></div></div><div class="result-band"><div class="result-copy"><span class="mini-label">Výsledek</span><h2>{escape(headline)}</h2><p>{escape(conclusion)}</p></div><div class="result-value"><span>Rozhodující sazba / režim</span><strong>{escape(headline_value)}</strong></div></div><div class="references"><h3>Klíčové právní reference</h3><div>{refs_html}</div></div><div class="page-number"><span>{report_id}</span><b>01 / 04</b></div></section>
<section class="page"><div class="topline"></div><header class="page-head"><div class="brand"><span class="brandmark">TT</span>TaxTreat</div><div class="docmeta"><b>Právní logika a výpočet</b>Report {report_id}</div></header><div class="section-title"><h2>Výpočet a právní logika</h2><span>Strana 2</span></div><div class="calc-grid"><div class="calc-box"><span>Hrubá částka</span><b>{amount_text}</b></div><div class="calc-box"><span>Základ v CZK</span><b>{base_czk}</b></div><div class="calc-box primary"><span>Česká srážková daň</span><b>{tax_czk}</b></div></div>{fx_html}<div class="steps">{analysis}</div><div class="prose"><span class="mini-label">Právní opora výsledku</span><p>{escape(conclusion)} {'Podrobné znění a odkazy na oficiální zdroje jsou uvedeny na následující straně.' if sources else ''}</p></div><div class="page-number"><span>{report_id}</span><b>02 / 04</b></div></section>
<section class="page"><div class="topline"></div><header class="page-head"><div class="brand"><span class="brandmark">TT</span>TaxTreat</div><div class="docmeta"><b>Právní základ</b>Právní stav k {cutoff}</div></header><div class="section-title"><h2>Právní základ a oficiální zdroje</h2><span>{len(sources)} evidovaných zdrojů</span></div>{source_cards}<div class="page-number"><span>{report_id}</span><b>03 / 04</b></div></section>
<section class="page"><div class="topline"></div><header class="page-head"><div class="brand"><span class="brandmark">TT</span>TaxTreat</div><div class="docmeta"><b>Lhůty, podklady a metadata</b>Report {report_id}</div></header><div class="section-title"><h2>Navazující lhůty a podklady</h2><span>Strana 4</span></div><div class="deadline-grid">{deadlines_html}</div><div class="two-col"><div class="panel"><h3>Otevřené skutkové údaje</h3><ul>{missing_html}</ul></div><div class="panel"><h3>Související dokumentace</h3><ul>{docs_html}</ul></div></div><div class="metadata"><div><span>ID reportu</span><b>{report_id}</b></div><div><span>Právní stav</span><b>{cutoff}</b></div><div><span>Dataset</span><b>{dataset}</b></div><div><span>Vygenerováno</span><b>{generated}</b></div></div><div class="disclaimer">{escape(str(report.get('disclaimer') or ''))}</div><div class="page-number"><span>{report_id}</span><b>04 / 04</b></div></section>
</article></body></html>'''
