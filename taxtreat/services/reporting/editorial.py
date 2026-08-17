from __future__ import annotations

import importlib.util
import re
from html import escape
from pathlib import Path
from typing import Any, Mapping


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
    if value in (None, ""):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if number.is_integer():
        text = f"{int(number):,}"
    else:
        text = f"{number:,.{decimals}f}".rstrip("0").rstrip(".")
    return text.replace(",", " ")


def _rate(value: Any) -> str:
    return "—" if value in (None, "") else f"{_number(value)} %"


def _income(value: Any) -> str:
    return {
        "dividend": "Dividendy",
        "interest": "Úroky",
        "royalty": "Licenční poplatky",
    }.get(str(value), str(value or "—"))


def _clean_paragraph(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^(odst\.?|paragraph|para\.?)\s*", "", text, flags=re.I)
    return text.strip()


def _article(source: Mapping[str, Any], long: bool = False) -> str:
    article = str(source.get("article") or "—").strip()
    paragraph = _clean_paragraph(source.get("paragraph"))
    if source.get("legal_layer") in {"treaty", "protocol", "mli"}:
        prefix = "článek" if long else "čl."
        ref = f"{prefix} {article}"
    else:
        ref = f"§ {article}"
    if paragraph:
        ref += f" odst. {paragraph}"
    return ref


def _layer(value: Any) -> str:
    return {
        "domestic": "Vnitrostátní právo",
        "treaty": "Smlouva",
        "protocol": "Protokol",
        "mli": "MLI",
    }.get(str(value or ""), "Právní zdroj")


def _source_title(source: Mapping[str, Any]) -> str:
    layer = source.get("legal_layer")
    ref = escape(_article(source, long=True))
    if layer == "treaty":
        return f"Smlouva o zamezení dvojího zdanění · {ref}"
    if layer == "protocol":
        return f"Protokol ke smlouvě o zamezení dvojího zdanění · {ref}"
    if layer == "mli":
        return f"Mnohostranná úmluva MLI · {ref}"
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


def _dedupe_sources(sources: list[Mapping[str, Any]], selected_rule_id: Any) -> list[Mapping[str, Any]]:
    ordered: list[tuple[Any, ...]] = []
    by_key: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for source in sources:
        key = (
            source.get("legal_layer"),
            source.get("source_url") or source.get("legal_instrument") or source.get("source_id"),
            str(source.get("article") or ""),
            _clean_paragraph(source.get("paragraph")),
        )
        if key not in by_key:
            ordered.append(key)
            by_key[key] = source
        elif source.get("rule_id") == selected_rule_id:
            by_key[key] = source
    return [by_key[key] for key in ordered]


def _result_copy(result: Mapping[str, Any], selected: Mapping[str, Any] | None) -> tuple[str, str, str]:
    reference = _source_sentence(selected)
    treatment = result.get("tax_treatment")
    if treatment == "exclusive_foreign_taxation":
        return (
            "Neuplatňuje se",
            "Result available",
            f"Podle {reference} se při zadaných skutečnostech česká srážková daň neuplatní.",
        )
    if treatment == "domestic_exemption":
        return (
            "0 %",
            "Result available",
            f"Podle {reference} se při zadaných skutečnostech uplatní osvobození od české srážkové daně.",
        )
    if result.get("status") == "FINAL" and result.get("rate") is not None:
        rate = _rate(result.get("rate"))
        return (
            rate,
            "Result available",
            f"Podle {reference} činí sazba české srážkové daně pro zadanou platbu {rate}.",
        )
    return (
        "—",
        "Additional information required",
        "Zadané údaje zatím neumožňují přiřadit konkrétní sazbu nebo režim. Otevřené skutkové body jsou uvedeny dále v reportu.",
    )


def _source_rate(source: Mapping[str, Any]) -> str:
    return _rate(source.get("rate")) if source.get("rate") not in (None, "") else "—"


def _short_excerpt(source: Mapping[str, Any], limit: int = 1800) -> str:
    excerpt = str(source.get("excerpt") or "").strip()
    if not excerpt:
        return "Pro tento zdroj není v reportovém datasetu uložen samostatný výňatek."
    if len(excerpt) <= limit:
        return excerpt
    cut = excerpt[:limit]
    last_break = max(cut.rfind("\n"), cut.rfind(". "))
    if last_break > int(limit * 0.65):
        cut = cut[: last_break + 1]
    return cut.rstrip() + " …"


def _source_link(source: Mapping[str, Any]) -> str:
    url = escape(str(source.get("source_url") or ""), quote=True)
    return f'<a href="{url}">Otevřít oficiální zdroj ↗</a>' if url else ""


def _why_steps(result: Mapping[str, Any], sources: list[Mapping[str, Any]], selected: Mapping[str, Any] | None, missing: list[Any]) -> str:
    domestic = next((s for s in sources if s.get("legal_layer") == "domestic"), None)
    treaty = next((s for s in sources if s.get("legal_layer") == "treaty"), None)
    rows: list[tuple[str, str]] = []
    if domestic:
        rows.append((
            "Česká vnitrostátní úprava",
            f"Výchozí české pravidlo je zachyceno v {_source_sentence(domestic)}; evidovaná sazba činí {_source_rate(domestic)}.",
        ))
    if treaty:
        rows.append((
            "Použitelná smlouva o zamezení dvojího zdanění",
            f"Pro zadanou dvojici států je zohledněno ustanovení {_source_sentence(treaty)}.",
        ))
    if selected:
        rows.append((
            "Rozhodující ustanovení",
            f"Výsledek je navázán na {_source_sentence(selected)}.",
        ))
    if missing:
        names = ", ".join(_FACT_LABELS.get(str(x), str(x).replace("_", " ")) for x in missing[:3])
        rows.append(("Otevřené skutkové údaje", f"Pro uzavření výsledku je třeba doplnit: {names}."))
    else:
        rows.append((
            "Skutkové podmínky",
            "U zadaných údajů nebyl v reportu evidován otevřený skutkový bod bránící použití přiřazeného pravidla.",
        ))
    output = []
    for idx, (title, text) in enumerate(rows[:5], start=1):
        output.append(f'''<div class="path-step"><span class="check">✓</span><div><b>{escape(title)}</b><p>{escape(text)}</p></div></div>''')
    return "".join(output)


def _legal_source_list(sources: list[Mapping[str, Any]], selected_rule_id: Any) -> str:
    items = []
    for source in sources:
        selected = source.get("rule_id") == selected_rule_id
        items.append(
            f'''<div class="source-tab{' selected' if selected else ''}"><span>{escape(_layer(source.get('legal_layer')))}</span><b>{escape(_article(source))}</b></div>'''
        )
    return "".join(items)


def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report.get("scope") or {}
    result = report.get("result") or {}
    calculation = result.get("withholding_tax_calculation") or {}
    schedule = result.get("withholding_compliance_schedule") or {}
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    sources = _dedupe_sources(list(report.get("official_sources") or []), selected_rule_id)
    selected = next((s for s in sources if s.get("rule_id") == selected_rule_id), None)
    if selected is None:
        selected = next((s for s in sources if s.get("legal_layer") in {"treaty", "protocol", "mli"}), None)
    if selected is None and sources:
        selected = sources[0]

    rate_display, status_label, conclusion = _result_copy(result, selected)
    amount = scope.get("transaction_amount") or {}
    amount_text = f"{_number(amount.get('amount'))} {escape(str(amount.get('currency') or ''))}".strip() if amount else "—"
    pair = f"{escape(str(scope.get('source_country') or '—'))} → {escape(str(scope.get('recipient_country') or '—'))}"
    generated = _date(report.get("generated_at"))
    cutoff = _date(report.get("legal_data_cutoff"))
    dataset = escape(str(report.get("legal_dataset_release") or report.get("source_release") or "—"))
    missing = list(report.get("missing_facts") or [])

    domestic = next((s for s in sources if s.get("legal_layer") == "domestic"), None)
    treaty = next((s for s in sources if s.get("legal_layer") == "treaty"), None)
    protocol = next((s for s in sources if s.get("legal_layer") == "protocol"), None)
    mli = next((s for s in sources if s.get("legal_layer") == "mli"), None)

    calc_base = "—"
    calc_tax = "—"
    fx_line = ""
    if calculation.get("status") == "CALCULATED":
        calc_base = f"{_number(calculation.get('gross_amount_czk'))} Kč"
        calc_tax = f"{_number(calculation.get('withholding_tax_czk'))} Kč"
        fx = calculation.get("exchange_rate") or {}
        if fx:
            fx_url = escape(str(fx.get("source_url") or ""), quote=True)
            fx_link = f'<a href="{fx_url}">Kurzovní lístek ČNB ↗</a>' if fx_url else ""
            fx_line = f"1 {escape(str(fx.get('currency') or ''))} = {_number(fx.get('czk_per_unit'), 6)} Kč · {_date(fx.get('effective_date'))} · {fx_link}"

    status_class = "ok" if status_label == "Result available" else "warn"
    legal_basis = escape(_source_sentence(selected)) if selected else "—"
    selected_excerpt = escape(_short_excerpt(selected)) if selected else "Právní výňatek není k dispozici."
    selected_link = _source_link(selected) if selected else ""
    why_steps = _why_steps(result, sources, selected, missing)

    source_rows = []
    for source in sources:
        source_rows.append(
            f'''<tr><td>{escape(_layer(source.get('legal_layer')))}</td><td>{escape(_article(source))}</td><td>{_source_rate(source)}</td><td>{_source_link(source)}</td></tr>'''
        )
    source_rows_html = "".join(source_rows) or '<tr><td colspan="4">Právní zdroje nejsou k dispozici.</td></tr>'

    missing_html = "".join(f"<li>{escape(_FACT_LABELS.get(str(x), str(x).replace('_', ' ')))}</li>" for x in missing) or "<li>Žádné otevřené skutkové údaje.</li>"
    docs_html = "".join(f"<li>{escape(str(x))}</li>" for x in report.get("required_documentation", [])) or "<li>Pro tento výstup není evidován samostatný seznam podkladů.</li>"

    deadlines = []
    for key, label in (
        ("reference_date", "Rozhodné datum"),
        ("remittance_deadline", "Odvod srážkové daně"),
        ("notification_deadline", "Oznámení příjmu do zahraničí"),
    ):
        if schedule.get(key):
            deadlines.append(f'<div class="deadline"><span>{label}</span><b>{_date(schedule[key])}</b></div>')
    deadlines_html = "".join(deadlines) or '<p class="muted">Navazující lhůty nejsou pro tento výsledek k dispozici.</p>'

    return f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TaxTreat · Informace k české srážkové dani</title>
<style>
:root{{--navy:#071a4a;--navy2:#0d2b6b;--blue:#2467d8;--green:#169447;--green-bg:#edf9f0;--orange:#c97913;--orange-bg:#fff7ea;--ink:#0b1739;--text:#37415d;--muted:#737b91;--line:#dfe4ee;--soft:#f7f9fc}}
*{{box-sizing:border-box}}html,body{{margin:0;background:#eef1f5;color:var(--text);font-family:Inter,Arial,"Segoe UI",sans-serif}}a{{color:var(--blue);text-decoration:none}}.report{{width:210mm;margin:16px auto;background:#fff;box-shadow:0 16px 44px #091c4a16}}.page{{position:relative;width:210mm;height:297mm;overflow:hidden;padding:15mm 16mm 14mm;background:#fff;page-break-after:always}}.page:last-child{{page-break-after:auto}}
.header{{height:14mm;display:flex;align-items:flex-start;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:4mm;margin-bottom:8mm}}.brand{{display:flex;align-items:center;gap:7px;color:var(--navy);font-size:14px;font-weight:800}}.shield{{display:grid;place-items:center;width:21px;height:21px;border:2px solid var(--navy);border-radius:7px;font-size:7px;font-weight:900}}.head-meta{{text-align:right;color:var(--muted);font-size:7.5px;line-height:1.55}}.head-meta b{{display:block;color:var(--ink);font-size:8.5px}}
.kicker{{color:#607099;font-size:7px;font-weight:800;letter-spacing:.11em;text-transform:uppercase}}h1{{margin:2mm 0 2mm;color:var(--ink);font-size:23px;line-height:1.12;letter-spacing:-.035em}}h2{{margin:0;color:var(--ink);font-size:16px;letter-spacing:-.02em}}h3{{margin:0;color:var(--ink);font-size:11px}}p{{font-size:9px;line-height:1.55}}.muted{{color:var(--muted)}}
.overview-grid{{display:grid;grid-template-columns:1.15fr .85fr;gap:6mm;margin-top:8mm}}.result-card,.facts-card,.section-card{{border:1px solid var(--line);border-radius:9px;background:#fff}}.result-card{{padding:6mm}}.result-top{{display:flex;justify-content:space-between;align-items:flex-start}}.status{{display:inline-flex;padding:2.2mm 3mm;border-radius:999px;font-size:7px;font-weight:800}}.status.ok{{color:#14723a;background:var(--green-bg)}}.status.warn{{color:#9b5c09;background:var(--orange-bg)}}.rate{{margin:5mm 0 2mm;color:var(--green);font-size:34px;font-weight:800;letter-spacing:-.05em}}.basis-line{{display:grid;grid-template-columns:1fr auto;gap:5mm;padding:3mm 0;border-top:1px solid var(--line);font-size:8px}}.basis-line span{{color:var(--muted)}}.basis-line b{{color:var(--ink);text-align:right}}.result-note{{margin-top:4mm;padding:3.5mm;border:1px solid #bde0c6;border-radius:7px;background:var(--green-bg);color:#27683e}}
.facts-card{{padding:5mm}}.fact-row{{display:flex;justify-content:space-between;gap:8mm;padding:3mm 0;border-bottom:1px solid var(--line);font-size:8px}}.fact-row:last-child{{border-bottom:0}}.fact-row span{{color:var(--muted)}}.fact-row b{{color:var(--ink);text-align:right}}.action-row{{display:flex;gap:3mm;margin-top:5mm}}.pill{{padding:2.8mm 4mm;border:1px solid #cfd7e6;border-radius:7px;color:var(--navy);font-size:8px;font-weight:750;background:#fff}}
.section-head{{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:6mm}}.section-head span{{color:var(--muted);font-size:7px}}.path{{margin-top:4mm;border-left:1px solid #c9d5e8;padding-left:6mm}}.path-step{{position:relative;display:grid;grid-template-columns:7mm 1fr;gap:3mm;padding:0 0 6mm}}.path-step .check{{position:absolute;left:-10.5mm;top:0;display:grid;place-items:center;width:7mm;height:7mm;border:1px solid #63bd7d;border-radius:50%;color:var(--green);background:#fff;font-size:8px;font-weight:900}}.path-step b{{color:var(--ink);font-size:9px}}.path-step p{{margin:1.2mm 0 0;color:var(--muted);font-size:8px}}.final-rate{{margin-top:4mm;padding:4mm 5mm;border:1px solid #a9d8b8;border-radius:7px;background:var(--green-bg);color:#176f39;font-size:11px;font-weight:800}}
.calc-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:6mm 0}}.calc{{padding:4mm;border:1px solid var(--line);border-radius:8px;background:#fff}}.calc span{{display:block;color:var(--muted);font-size:7px;text-transform:uppercase;font-weight:800}}.calc b{{display:block;margin-top:2mm;color:var(--ink);font-size:13px}}.fx{{padding:3mm 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);font-size:7.5px;color:var(--muted)}}
.sources-layout{{display:grid;grid-template-columns:42mm 1fr;gap:5mm}}.source-tabs{{border:1px solid var(--line);border-radius:8px;overflow:hidden;background:#fff}}.source-tab{{padding:4mm;border-bottom:1px solid var(--line)}}.source-tab:last-child{{border-bottom:0}}.source-tab.selected{{background:#f1f6ff;border-left:3px solid var(--blue)}}.source-tab span{{display:block;color:var(--muted);font-size:7px}}.source-tab b{{display:block;margin-top:1mm;color:var(--ink);font-size:8.5px}}.legal-source{{border:1px solid var(--line);border-radius:8px;padding:5mm;background:#fff}}.legal-source .label{{color:#607099;font-size:7px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}}.legal-source h2{{margin:2mm 0 1mm;font-size:15px}}.legal-source .summary{{color:var(--muted);font-size:8px}}.quote{{margin-top:5mm;padding:4mm;border-radius:7px;background:#f6f7fa;color:#434b62;font-size:7.5px;line-height:1.45;white-space:pre-line;max-height:84mm;overflow:hidden}}.official{{margin-top:4mm;padding-top:3mm;border-top:1px solid var(--line);font-size:8px;font-weight:750}}.source-table{{width:100%;margin-top:6mm;border-collapse:collapse;font-size:7px}}.source-table th,.source-table td{{padding:2.3mm;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}.source-table th{{color:#65708b;background:#f8f9fc;font-size:6.8px;text-transform:uppercase}}.source-table td{{color:var(--text)}}
.deadlines{{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:5mm 0 7mm}}.deadline{{padding:4mm;border:1px solid var(--line);border-radius:7px}}.deadline span{{display:block;color:var(--muted);font-size:7px}}.deadline b{{display:block;margin-top:2mm;color:var(--ink);font-size:10px}}.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:4mm}}.section-card{{padding:5mm}}.section-card ul{{margin:3mm 0 0;padding-left:5mm}}.section-card li{{margin-bottom:2mm;font-size:8px;line-height:1.4}}.meta-grid{{display:grid;grid-template-columns:1fr 1fr;gap:0;margin-top:6mm;border:1px solid var(--line);border-radius:7px;overflow:hidden}}.meta{{padding:3mm;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}}.meta:nth-child(2n){{border-right:0}}.meta:nth-last-child(-n+2){{border-bottom:0}}.meta span{{display:block;color:var(--muted);font-size:6.5px;text-transform:uppercase}}.meta b{{display:block;margin-top:1mm;color:var(--ink);font-size:7.5px;word-break:break-word}}.disclaimer{{margin-top:6mm;padding-top:4mm;border-top:1px solid var(--line);color:#7f879b;font-size:6.8px;line-height:1.45}}.footer{{position:absolute;left:16mm;right:16mm;bottom:7mm;display:flex;justify-content:space-between;color:#9aa1b1;font-size:6.5px}}.footer b{{color:#6d7690}}
@media print{{@page{{size:A4;margin:0}}html,body{{background:#fff}}.report{{margin:0;box-shadow:none}}.page{{break-after:page}}.page:last-child{{break-after:auto}}}}
</style></head><body><article class="report">
<section class="page"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Informace k české srážkové dani</b>Vygenerováno {generated}</div></header><span class="kicker">Result · Overview</span><h1>{escape(_income(scope.get('income_type')))} · {pair}</h1><p class="muted">Přehled výsledku podle zadaných údajů a právních zdrojů uvedených v tomto reportu.</p><div class="overview-grid"><div class="result-card"><div class="result-top"><div><span class="kicker">Applicable WHT rate</span><div class="rate">{escape(rate_display)}</div></div><span class="status {status_class}">{escape(status_label)}</span></div><div class="basis-line"><span>Vnitrostátní sazba</span><b>{_source_rate(domestic) if domestic else '—'}</b></div><div class="basis-line"><span>Smluvní sazba / režim</span><b>{_source_rate(treaty) if treaty else '—'}</b></div><div class="basis-line"><span>Právní základ</span><b>{legal_basis}</b></div><div class="basis-line"><span>Účinnost pro datum platby</span><b>Ano</b></div><div class="result-note">{escape(conclusion)}</div><div class="action-row"><span class="pill">Why this rate?</span><span class="pill">Sources</span></div></div><div class="facts-card"><h3>Transaction details</h3><div class="fact-row"><span>Typ příjmu</span><b>{escape(_income(scope.get('income_type')))}</b></div><div class="fact-row"><span>Datum platby</span><b>{_date(scope.get('transaction_date'))}</b></div><div class="fact-row"><span>Hrubá částka</span><b>{amount_text}</b></div><div class="fact-row"><span>Jurisdikce</span><b>{pair}</b></div><div class="fact-row"><span>Právní stav</span><b>{cutoff}</b></div></div></div><div class="section-card" style="margin-top:6mm"><h3>Klíčové právní reference</h3><table class="source-table"><thead><tr><th>Vrstva</th><th>Ustanovení</th><th>Sazba</th><th>Zdroj</th></tr></thead><tbody>{source_rows_html}</tbody></table></div><div class="footer"><span>TaxTreat</span><b>01 / 04</b></div></section>
<section class="page"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Result · Why this rate?</b>{pair}</div></header><div class="section-head"><div><span class="kicker">Decision path</span><h2>Proč je zobrazen tento výsledek?</h2></div><span>Právní cesta od výchozího pravidla k výsledku</span></div><div class="calc-grid"><div class="calc"><span>Hrubá částka</span><b>{amount_text}</b></div><div class="calc"><span>Základ v CZK</span><b>{calc_base}</b></div><div class="calc"><span>Česká srážková daň</span><b>{calc_tax}</b></div></div>{f'<div class="fx">Přepočet měny · {fx_line}</div>' if fx_line else ''}<div class="path">{why_steps}</div><div class="final-rate">Applicable WHT rate: {escape(rate_display)}</div><div class="section-card" style="margin-top:7mm"><h3>Právní opora výsledku</h3><p>{escape(conclusion)}</p>{selected_link}</div><div class="footer"><span>TaxTreat</span><b>02 / 04</b></div></section>
<section class="page"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Result · Sources</b>Právní stav k {cutoff}</div></header><div class="section-head"><div><span class="kicker">Právní základ</span><h2>Zdroje, právní texty a relevantní výňatky</h2></div><span>{len(sources)} evidovaných zdrojů</span></div><div class="sources-layout"><aside class="source-tabs">{_legal_source_list(sources, selected_rule_id)}</aside><article class="legal-source"><span class="label">Použité právní pravidlo</span><h2>{_source_title(selected) if selected else 'Právní zdroj není k dispozici'}</h2><p class="summary">{escape(_source_sentence(selected).capitalize()) if selected else ''}</p><div class="quote">{selected_excerpt}</div><div class="official">{selected_link}</div></article></div><table class="source-table"><thead><tr><th>Právní vrstva</th><th>Ustanovení</th><th>Evidovaná sazba</th><th>Oficiální zdroj</th></tr></thead><tbody>{source_rows_html}</tbody></table><div class="footer"><span>TaxTreat</span><b>03 / 04</b></div></section>
<section class="page"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Report details</b>{pair}</div></header><div class="section-head"><div><span class="kicker">Navazující informace</span><h2>Lhůty, podklady a otevřené body</h2></div><span>Strana 4</span></div><div class="deadlines">{deadlines_html}</div><div class="two-col"><article class="section-card"><h3>Otevřené skutkové údaje</h3><ul>{missing_html}</ul></article><article class="section-card"><h3>Související dokumentace</h3><ul>{docs_html}</ul></article></div><div class="meta-grid"><div class="meta"><span>Právní stav</span><b>{cutoff}</b></div><div class="meta"><span>Dataset</span><b>{dataset}</b></div><div class="meta"><span>Vygenerováno</span><b>{generated}</b></div><div class="meta"><span>Typ příjmu</span><b>{escape(_income(scope.get('income_type')))}</b></div></div><div class="disclaimer">{escape(str(report.get('disclaimer') or ''))}</div><div class="footer"><span>TaxTreat</span><b>04 / 04</b></div></section>
</article></body></html>'''
