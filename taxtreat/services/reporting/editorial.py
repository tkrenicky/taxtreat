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


def _short_excerpt(source: Mapping[str, Any], limit: int = 1550) -> str:
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


def _why_steps(sources: list[Mapping[str, Any]], selected: Mapping[str, Any] | None, missing: list[Any]) -> str:
    domestic = next((s for s in sources if s.get("legal_layer") == "domestic"), None)
    treaty = next((s for s in sources if s.get("legal_layer") == "treaty"), None)
    rows: list[tuple[str, str]] = []
    if domestic:
        rows.append(("Česká vnitrostátní úprava", f"Výchozí pravidlo: {_source_sentence(domestic)}; evidovaná sazba {_source_rate(domestic)}."))
    if treaty:
        rows.append(("Použitelná smlouva o zamezení dvojího zdanění", f"Pro zadanou dvojici států je zohledněno ustanovení {_source_sentence(treaty)}."))
    if selected:
        rows.append(("Rozhodující ustanovení", f"Výsledek je navázán na {_source_sentence(selected)}."))
    if missing:
        names = ", ".join(_FACT_LABELS.get(str(x), str(x).replace("_", " ")) for x in missing[:3])
        rows.append(("Otevřené skutkové údaje", f"Pro uzavření výsledku je třeba doplnit: {names}."))
    else:
        rows.append(("Skutkové podmínky", "U zadaných údajů není evidován otevřený skutkový bod, který by bránil použití přiřazeného pravidla."))
    return "".join(
        f'<div class="path-step"><span class="check">✓</span><div><b>{escape(title)}</b><p>{escape(text)}</p></div></div>'
        for title, text in rows[:5]
    )


def _legal_source_list(sources: list[Mapping[str, Any]], selected_rule_id: Any) -> str:
    return "".join(
        f'<div class="source-tab{" selected" if source.get("rule_id") == selected_rule_id else ""}"><span>{escape(_layer(source.get("legal_layer")))}</span><b>{escape(_article(source))}</b></div>'
        for source in sources
    )


def _illustration(kind: str) -> str:
    if kind == "summary":
        return '''<svg viewBox="0 0 230 150" role="img" aria-label="Ilustrace reportu a daňového výpočtu"><rect x="30" y="31" width="105" height="73" rx="9" fill="#fff" stroke="#14295f" stroke-width="3"/><rect x="43" y="43" width="78" height="8" rx="4" fill="#dbe8ff"/><rect x="43" y="60" width="51" height="7" rx="3.5" fill="#e8eef9"/><rect x="43" y="75" width="66" height="7" rx="3.5" fill="#e8eef9"/><path d="M17 113h133" stroke="#14295f" stroke-width="3" stroke-linecap="round"/><path d="M52 113l8 13h44l8-13" fill="#dbe8ff" stroke="#14295f" stroke-width="3"/><circle cx="171" cy="48" r="20" fill="#e8f8ed" stroke="#169447" stroke-width="3"/><path d="M162 48l6 6 12-14" fill="none" stroke="#169447" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><rect x="157" y="82" width="44" height="37" rx="7" fill="#eef4ff" stroke="#2f68ce" stroke-width="3"/><path d="M168 105V94m11 11V88m11 17V98" stroke="#2f68ce" stroke-width="4" stroke-linecap="round"/><circle cx="203" cy="26" r="6" fill="#ffd9a8"/><circle cx="20" cy="52" r="7" fill="#cfe2ff"/></svg>'''
    if kind == "path":
        return '''<svg viewBox="0 0 180 105" aria-hidden="true"><path d="M24 76C43 28 75 87 94 43s49 15 64-20" fill="none" stroke="#c9d8f3" stroke-width="5" stroke-linecap="round"/><circle cx="24" cy="76" r="10" fill="#fff" stroke="#169447" stroke-width="3"/><path d="M20 76l3 3 6-7" fill="none" stroke="#169447" stroke-width="3" stroke-linecap="round"/><circle cx="94" cy="43" r="10" fill="#fff" stroke="#2f68ce" stroke-width="3"/><path d="M90 43l3 3 6-7" fill="none" stroke="#2f68ce" stroke-width="3" stroke-linecap="round"/><rect x="133" y="10" width="34" height="28" rx="6" fill="#eef4ff" stroke="#14295f" stroke-width="2.5"/><path d="M141 20h17m-17 8h12" stroke="#2f68ce" stroke-width="3" stroke-linecap="round"/></svg>'''
    if kind == "sources":
        return '''<svg viewBox="0 0 180 105" aria-hidden="true"><rect x="31" y="20" width="60" height="68" rx="7" fill="#fff" stroke="#14295f" stroke-width="3"/><path d="M44 38h34m-34 13h28m-28 13h34" stroke="#c7d7f1" stroke-width="5" stroke-linecap="round"/><circle cx="121" cy="57" r="25" fill="#eef4ff" stroke="#2f68ce" stroke-width="3"/><circle cx="121" cy="57" r="11" fill="#fff" stroke="#2f68ce" stroke-width="3"/><path d="M139 75l20 20" stroke="#14295f" stroke-width="5" stroke-linecap="round"/><circle cx="147" cy="21" r="9" fill="#e8f8ed" stroke="#169447" stroke-width="2.5"/><path d="M143 21l3 3 5-6" fill="none" stroke="#169447" stroke-width="2.5"/></svg>'''
    return '''<svg viewBox="0 0 180 105" aria-hidden="true"><rect x="29" y="24" width="68" height="61" rx="8" fill="#fff" stroke="#14295f" stroke-width="3"/><path d="M29 42h68" stroke="#14295f" stroke-width="3"/><path d="M47 17v17m32-17v17" stroke="#2f68ce" stroke-width="4" stroke-linecap="round"/><circle cx="52" cy="60" r="6" fill="#d9e7ff"/><circle cx="72" cy="60" r="6" fill="#d9e7ff"/><circle cx="52" cy="76" r="6" fill="#e8f8ed"/><rect x="111" y="35" width="42" height="49" rx="7" fill="#eef4ff" stroke="#14295f" stroke-width="3"/><path d="M122 49h20m-20 12h20m-20 12h14" stroke="#2f68ce" stroke-width="3" stroke-linecap="round"/><circle cx="157" cy="22" r="9" fill="#e8f8ed" stroke="#169447" stroke-width="2.5"/><path d="M153 22l3 3 5-6" fill="none" stroke="#169447" stroke-width="2.5"/></svg>'''


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
    why_steps = _why_steps(sources, selected, missing)

    source_rows = []
    for source in sources:
        source_rows.append(f'<tr><td>{escape(_layer(source.get("legal_layer")))}</td><td>{escape(_article(source))}</td><td>{_source_rate(source)}</td><td>{_source_link(source)}</td></tr>')
    source_rows_html = "".join(source_rows) or '<tr><td colspan="4">Právní zdroje nejsou k dispozici.</td></tr>'

    missing_html = "".join(f"<li>{escape(_FACT_LABELS.get(str(x), str(x).replace('_', ' ')))}</li>" for x in missing) or "<li>Žádné otevřené skutkové údaje.</li>"
    docs_html = "".join(f"<li>{escape(str(x))}</li>" for x in report.get("required_documentation", [])) or "<li>Pro tento výstup není evidován samostatný seznam podkladů.</li>"

    deadlines = []
    for key, label in (("reference_date", "Rozhodné datum"), ("remittance_deadline", "Odvod srážkové daně"), ("notification_deadline", "Oznámení příjmu do zahraničí")):
        if schedule.get(key):
            deadlines.append(f'<div class="deadline"><span>{label}</span><b>{_date(schedule[key])}</b></div>')
    deadlines_html = "".join(deadlines) or '<p class="muted">Navazující lhůty nejsou pro tento výsledek k dispozici.</p>'

    return f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TaxTreat · Informace k české srážkové dani</title>
<style>
:root{{--navy:#0b1f52;--navy2:#17366f;--blue:#2d67ca;--pale:#eaf2ff;--pale2:#f4f7fc;--green:#159447;--green-bg:#edf9f0;--orange:#c97913;--orange-bg:#fff7ea;--ink:#0d1b3e;--text:#3d4967;--muted:#75809b;--line:#dfe6f1}}
*{{box-sizing:border-box}}html,body{{margin:0;background:#edf2f8;color:var(--text);font-family:Inter,Arial,"Segoe UI",sans-serif}}a{{color:var(--blue);text-decoration:none}}.report{{width:210mm;margin:16px auto}}.page{{position:relative;width:210mm;height:297mm;overflow:hidden;padding:10mm;background:#edf2f8;page-break-after:always}}.page:last-child{{page-break-after:auto}}.sheet{{position:relative;width:100%;height:100%;overflow:hidden;padding:12mm 13mm 13mm;border:1px solid #dce4ef;border-radius:7mm;background:#fff;box-shadow:0 12px 34px #18315d10}}
.header{{height:12mm;display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:6mm}}.brand{{display:flex;align-items:center;gap:7px;color:var(--navy);font-size:14px;font-weight:800}}.shield{{display:grid;place-items:center;width:21px;height:21px;border:2px solid var(--navy);border-radius:7px;font-size:7px;font-weight:900}}.head-meta{{text-align:right;color:var(--muted);font-size:7.2px;line-height:1.5}}.head-meta b{{display:block;color:var(--ink);font-size:8.5px}}
.hero{{display:grid;grid-template-columns:1.35fr .65fr;align-items:center;gap:8mm;margin:0 -13mm 8mm;padding:9mm 13mm;background:linear-gradient(90deg,#e8f1ff 0%,#f2f7ff 100%)}}.hero h1{{margin:2mm 0 2.5mm;color:var(--navy);font-size:24px;line-height:1.08;letter-spacing:-.035em}}.hero p{{max-width:105mm;margin:0;color:#64718e;font-size:9px;line-height:1.55}}.hero-art svg{{display:block;width:100%;max-height:42mm}}
.kicker{{color:#6076a6;font-size:7px;font-weight:800;letter-spacing:.11em;text-transform:uppercase}}h1{{margin:2mm 0;color:var(--ink);font-size:22px;line-height:1.12;letter-spacing:-.035em}}h2{{margin:0;color:var(--ink);font-size:15px;letter-spacing:-.02em}}h3{{margin:0;color:var(--ink);font-size:10.5px}}p{{font-size:8.5px;line-height:1.5}}.muted{{color:var(--muted)}}
.section-title-row{{display:flex;align-items:center;justify-content:space-between;gap:8mm;margin-bottom:5mm}}.section-title-row .title-wrap{{display:flex;align-items:center;gap:4mm}}.section-icon{{display:grid;place-items:center;width:11mm;height:11mm;border-radius:4mm;background:var(--pale)}}.section-icon svg{{width:9mm;height:9mm}}
.overview-grid{{display:grid;grid-template-columns:1.08fr .92fr;gap:5mm}}.result-card,.facts-card,.section-card{{border:1px solid var(--line);border-radius:4mm;background:#fff}}.result-card{{padding:5mm}}.result-top{{display:flex;justify-content:space-between;align-items:flex-start}}.status{{display:inline-flex;padding:2mm 3mm;border-radius:999px;font-size:6.8px;font-weight:800}}.status.ok{{color:#14723a;background:var(--green-bg)}}.status.warn{{color:#9b5c09;background:var(--orange-bg)}}.rate{{margin:4mm 0 2mm;color:var(--green);font-size:33px;font-weight:800;letter-spacing:-.05em}}.basis-line{{display:grid;grid-template-columns:1fr auto;gap:4mm;padding:2.6mm 0;border-top:1px solid var(--line);font-size:7.6px}}.basis-line span{{color:var(--muted)}}.basis-line b{{color:var(--ink);text-align:right;max-width:82mm}}.result-note{{margin-top:3mm;padding:3mm;border:1px solid #bde0c6;border-radius:3mm;background:var(--green-bg);color:#27683e;font-size:7.7px;line-height:1.5}}
.facts-card{{padding:4.5mm}}.fact-row{{display:flex;justify-content:space-between;gap:6mm;padding:2.7mm 0;border-bottom:1px solid var(--line);font-size:7.6px}}.fact-row:last-child{{border-bottom:0}}.fact-row span{{color:var(--muted)}}.fact-row b{{color:var(--ink);text-align:right}}
.section-card{{padding:4.5mm}}.source-table{{width:100%;margin-top:3mm;border-collapse:collapse;font-size:6.8px}}.source-table th,.source-table td{{padding:2.2mm;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}.source-table th{{color:#65708b;background:#f7f9fd;font-size:6.4px;text-transform:uppercase}}
.section-head{{display:grid;grid-template-columns:1fr 42mm;align-items:center;gap:8mm;margin:0 -4mm 6mm;padding:5mm 6mm;border-radius:5mm;background:#f6f9ff}}.section-head .art svg{{width:100%;height:24mm}}.path{{margin-top:4mm;border-left:1px solid #c9d5e8;padding-left:6mm}}.path-step{{position:relative;display:grid;grid-template-columns:7mm 1fr;gap:3mm;padding:0 0 5mm}}.path-step .check{{position:absolute;left:-10.5mm;top:0;display:grid;place-items:center;width:7mm;height:7mm;border:1px solid #63bd7d;border-radius:50%;color:var(--green);background:#fff;font-size:8px;font-weight:900}}.path-step b{{color:var(--ink);font-size:8.5px}}.path-step p{{margin:1.2mm 0 0;color:var(--muted);font-size:7.5px}}.final-rate{{margin-top:3mm;padding:3.5mm 4mm;border:1px solid #a9d8b8;border-radius:3mm;background:var(--green-bg);color:#176f39;font-size:10.5px;font-weight:800}}
.calc-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:5mm 0}}.calc{{padding:3.6mm;border:1px solid var(--line);border-radius:3mm;background:#fff}}.calc span{{display:block;color:var(--muted);font-size:6.8px;text-transform:uppercase;font-weight:800}}.calc b{{display:block;margin-top:1.8mm;color:var(--ink);font-size:12px}}.fx{{padding:2.8mm 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);font-size:7px;color:var(--muted)}}
.sources-layout{{display:grid;grid-template-columns:39mm 1fr;gap:4mm}}.source-tabs{{border:1px solid var(--line);border-radius:3mm;overflow:hidden;background:#fff}}.source-tab{{padding:3.5mm;border-bottom:1px solid var(--line)}}.source-tab:last-child{{border-bottom:0}}.source-tab.selected{{background:#f1f6ff;border-left:3px solid var(--blue)}}.source-tab span{{display:block;color:var(--muted);font-size:6.6px}}.source-tab b{{display:block;margin-top:1mm;color:var(--ink);font-size:8px}}.legal-source{{border:1px solid var(--line);border-radius:3mm;padding:4.2mm;background:#fff}}.legal-source .label{{color:#607099;font-size:6.6px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}}.legal-source h2{{margin:1.5mm 0 1mm;font-size:13.5px}}.legal-source .summary{{color:var(--muted);font-size:7.4px}}.quote{{margin-top:4mm;padding:3.5mm;border-radius:3mm;background:#f5f7fb;color:#434b62;font-size:7px;line-height:1.4;white-space:pre-line;max-height:69mm;overflow:hidden}}.official{{margin-top:3mm;padding-top:2.5mm;border-top:1px solid var(--line);font-size:7.4px;font-weight:750}}
.deadlines{{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:5mm 0 6mm}}.deadline{{padding:3.5mm;border:1px solid var(--line);border-radius:3mm;background:#fff}}.deadline span{{display:block;color:var(--muted);font-size:6.6px}}.deadline b{{display:block;margin-top:1.7mm;color:var(--ink);font-size:9.5px}}.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:4mm}}.section-card ul{{margin:3mm 0 0;padding-left:5mm}}.section-card li{{margin-bottom:1.7mm;font-size:7.5px;line-height:1.35}}.meta-grid{{display:grid;grid-template-columns:1fr 1fr;margin-top:5mm;border:1px solid var(--line);border-radius:3mm;overflow:hidden}}.meta{{padding:2.8mm;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}}.meta:nth-child(2n){{border-right:0}}.meta:nth-last-child(-n+2){{border-bottom:0}}.meta span{{display:block;color:var(--muted);font-size:6.2px;text-transform:uppercase}}.meta b{{display:block;margin-top:1mm;color:var(--ink);font-size:7.3px;word-break:break-word}}.disclaimer{{margin-top:5mm;padding-top:3.5mm;border-top:1px solid var(--line);color:#858da1;font-size:6.3px;line-height:1.4}}.footer{{position:absolute;left:13mm;right:13mm;bottom:6mm;display:flex;justify-content:space-between;color:#9aa1b1;font-size:6.3px}}.footer b{{color:#6d7690}}
@media print{{@page{{size:A4;margin:0}}html,body{{background:#fff}}.report{{margin:0}}.page{{break-after:page}}.page:last-child{{break-after:auto}}.sheet{{box-shadow:none}}}}
</style></head><body><article class="report">
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Informace k české srážkové dani</b>Vygenerováno {generated}</div></header><div class="hero"><div><span class="kicker">TaxTreat Analysis Summary</span><h1>{escape(_income(scope.get('income_type')))} · {pair}</h1><p>Souhrn transakce, výsledku a právních zdrojů použitých pro zadané údaje. Níže jsou odděleně zachyceny výsledek, právní cesta a konkrétní právní reference.</p></div><div class="hero-art">{_illustration('summary')}</div></div><div class="section-title-row"><div class="title-wrap"><div class="section-icon">{_illustration('path')}</div><div><span class="kicker">Withholding Tax Result</span><h2>Výsledek a základní údaje</h2></div></div></div><div class="overview-grid"><div class="result-card"><div class="result-top"><div><span class="kicker">Applicable WHT rate</span><div class="rate">{escape(rate_display)}</div></div><span class="status {status_class}">{escape(status_label)}</span></div><div class="basis-line"><span>Vnitrostátní sazba</span><b>{_source_rate(domestic) if domestic else '—'}</b></div><div class="basis-line"><span>Smluvní sazba / režim</span><b>{_source_rate(treaty) if treaty else '—'}</b></div><div class="basis-line"><span>Právní základ</span><b>{legal_basis}</b></div><div class="result-note">{escape(conclusion)}</div></div><div class="facts-card"><h3>Transaction details</h3><div class="fact-row"><span>Typ příjmu</span><b>{escape(_income(scope.get('income_type')))}</b></div><div class="fact-row"><span>Datum platby</span><b>{_date(scope.get('transaction_date'))}</b></div><div class="fact-row"><span>Hrubá částka</span><b>{amount_text}</b></div><div class="fact-row"><span>Jurisdikce</span><b>{pair}</b></div><div class="fact-row"><span>Právní stav</span><b>{cutoff}</b></div></div></div><div class="section-card" style="margin-top:5mm"><h3>Klíčové právní reference</h3><table class="source-table"><thead><tr><th>Vrstva</th><th>Ustanovení</th><th>Sazba</th><th>Zdroj</th></tr></thead><tbody>{source_rows_html}</tbody></table></div><div class="footer"><span>TaxTreat</span><b>01 / 04</b></div></div></section>
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Result · Why this rate?</b>{pair}</div></header><div class="section-head"><div><span class="kicker">Decision path</span><h2>Proč je zobrazen tento výsledek?</h2><p class="muted">Právní cesta od českého výchozího pravidla k přiřazenému výsledku.</p></div><div class="art">{_illustration('path')}</div></div><div class="calc-grid"><div class="calc"><span>Hrubá částka</span><b>{amount_text}</b></div><div class="calc"><span>Základ v CZK</span><b>{calc_base}</b></div><div class="calc"><span>Česká srážková daň</span><b>{calc_tax}</b></div></div>{f'<div class="fx">Přepočet měny · {fx_line}</div>' if fx_line else ''}<div class="path">{why_steps}</div><div class="final-rate">Applicable WHT rate: {escape(rate_display)}</div><div class="section-card" style="margin-top:6mm"><h3>Právní opora výsledku</h3><p>{escape(conclusion)}</p>{selected_link}</div><div class="footer"><span>TaxTreat</span><b>02 / 04</b></div></div></section>
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Result · Sources</b>Právní stav k {cutoff}</div></header><div class="section-head"><div><span class="kicker">Právní základ</span><h2>Zdroje, právní texty a relevantní výňatky</h2><p class="muted">Konkrétní ustanovení navázaná na tento výsledek.</p></div><div class="art">{_illustration('sources')}</div></div><div class="sources-layout"><aside class="source-tabs">{_legal_source_list(sources, selected_rule_id)}</aside><article class="legal-source"><span class="label">Použité právní pravidlo</span><h2>{_source_title(selected) if selected else 'Právní zdroj není k dispozici'}</h2><p class="summary">{escape(_source_sentence(selected).capitalize()) if selected else ''}</p><div class="quote">{selected_excerpt}</div><div class="official">{selected_link}</div></article></div><table class="source-table"><thead><tr><th>Právní vrstva</th><th>Ustanovení</th><th>Evidovaná sazba</th><th>Oficiální zdroj</th></tr></thead><tbody>{source_rows_html}</tbody></table><div class="footer"><span>TaxTreat</span><b>03 / 04</b></div></div></section>
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Report details</b>{pair}</div></header><div class="section-head"><div><span class="kicker">Navazující informace</span><h2>Lhůty, podklady a otevřené body</h2><p class="muted">Praktický přehled údajů navazujících na výsledek.</p></div><div class="art">{_illustration('details')}</div></div><div class="deadlines">{deadlines_html}</div><div class="two-col"><article class="section-card"><h3>Otevřené skutkové údaje</h3><ul>{missing_html}</ul></article><article class="section-card"><h3>Související dokumentace</h3><ul>{docs_html}</ul></article></div><div class="meta-grid"><div class="meta"><span>Právní stav</span><b>{cutoff}</b></div><div class="meta"><span>Dataset</span><b>{dataset}</b></div><div class="meta"><span>Vygenerováno</span><b>{generated}</b></div><div class="meta"><span>Typ příjmu</span><b>{escape(_income(scope.get('income_type')))}</b></div></div><div class="disclaimer">{escape(str(report.get('disclaimer') or ''))}</div><div class="footer"><span>TaxTreat</span><b>04 / 04</b></div></div></section>
</article></body></html>'''
