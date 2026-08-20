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
# reporting.py now stores localized disclaimers in _DISCLAIMERS. Keep the
# editorial compatibility layer importable while defaulting its legacy
# DISCLAIMER export to Czech; localized report generation still uses the
# language-aware implementation from reporting.py.
DISCLAIMER = getattr(_DATA, "DISCLAIMER", _DATA._DISCLAIMERS["cs"])
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
        return f"{ref} MLI"
    return f"{ref} zákona č. 586/1992 Sb., o daních z příjmů"


def _result_copy(report: Mapping[str, Any]) -> tuple[str, str]:
    result = report.get("result", {})
    status = result.get("status")
    treatment = result.get("tax_treatment")
    rate = result.get("rate")
    source = next((item for item in report.get("legal_basis", []) if item.get("selected")), None)
    source_sentence = _source_sentence(source)
    if status == "FINAL" and treatment == "domestic_exemption":
        return (
            "Příjem je osvobozen od české srážkové daně",
            f"Podle {source_sentence} je při zadaných údajích příjem v České republice osvobozen od srážkové daně.",
        )
    if status == "FINAL" and treatment == "exclusive_foreign_taxation":
        return (
            "Příjem se v České republice nezdaňuje",
            f"Podle {source_sentence} se při zadaných údajích příjem v České republice nezdaňuje.",
        )
    if status == "FINAL" and rate is not None:
        return (
            f"Srážková daň {_rate(rate)}",
            f"Podle {source_sentence} činí při zadaných údajích sazba srážkové daně {_number(rate)} %.",
        )
    candidate = result.get("candidate_rate")
    if candidate is not None:
        return (
            "Výsledek vyžaduje doplnění",
            f"Byla identifikována sazba {_number(candidate)} %. Její použití závisí na splnění právních a skutkových podmínek uvedených níže.",
        )
    return (
        "Výsledek zatím nelze uzavřít",
        "Sazbu zatím nelze určit. Konkrétní důvod je uveden v části Podmínky a další kroky níže.",
    )


def _fact_value(value: Any) -> str:
    if isinstance(value, bool):
        return "Ano" if value else "Ne"
    if value in (None, ""):
        return "—"
    return escape(str(value))


def _fact_rows(report: Mapping[str, Any]) -> str:
    facts = report.get("facts", {})
    rows = []
    for key, label in _FACT_LABELS.items():
        if key not in facts:
            continue
        rows.append(
            f"<tr><th>{escape(label)}</th><td>{_fact_value(facts.get(key))}</td></tr>"
        )
    return "".join(rows) or '<tr><td colspan="2">Bez dalších skutkových údajů.</td></tr>'


def _legal_basis(report: Mapping[str, Any]) -> str:
    cards = []
    for source in report.get("legal_basis", []):
        selected = " selected" if source.get("selected") else ""
        cards.append(
            f'<article class="source{selected}"><p class="eyebrow">{escape(_layer(source.get("legal_layer")))}</p>'
            f"<h3>{_source_title(source)}</h3>"
            f"<p>{escape(str(source.get('excerpt') or source.get('source_text') or ''))}</p>"
            f"<p class=\"source-meta\">{escape(str(source.get('source_url') or source.get('url') or ''))}</p></article>"
        )
    return "".join(cards) or '<p class="muted">Právní zdroj není k dispozici.</p>'


def render_report_html(report: Mapping[str, Any]) -> str:
    title, explanation = _result_copy(report)
    request = report.get("request", {})
    amount = request.get("transaction_amount") or {}
    result = report.get("result", {})
    compliance = report.get("withholding_compliance_schedule") or {}
    reporting = report.get("reporting") or {}
    deadline = compliance.get("remittance_deadline") or compliance.get("deadline") or "—"
    notification = reporting.get("notification_deadline") or compliance.get("notification_deadline") or "—"
    docs = report.get("required_documentation") or []
    docs_html = "".join(f"<li>{escape(str(item))}</li>" for item in docs)

    return f"""<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TaxTreat · Report srážkové daně</title>
<style>
:root{{--ink:#17211f;--muted:#62706c;--line:#dbe3df;--paper:#fff;--soft:#f4f7f5;--accent:#28584f;--warn:#8a5b18}}
*{{box-sizing:border-box}} body{{margin:0;background:#edf1ef;color:var(--ink);font-family:Inter,Arial,sans-serif;line-height:1.5}}
.page{{width:min(1040px,calc(100% - 32px));margin:28px auto;background:var(--paper);box-shadow:0 12px 40px #17211f14}}
header{{padding:42px 46px 32px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:28px}}
.brand{{font-size:28px;font-weight:800;letter-spacing:-.04em}} .eyebrow{{margin:0 0 5px;color:var(--muted);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}
h1{{margin:5px 0 8px;font-size:32px;line-height:1.15}} h2{{margin:0 0 12px;font-size:20px}} h3{{margin:4px 0 8px;font-size:16px}} p{{margin:0 0 10px}}
main{{padding:34px 46px 46px}} section{{margin:0 0 32px}} .hero{{padding:26px;border:1px solid var(--line);border-left:5px solid var(--accent);background:var(--soft)}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}} .card,.source{{padding:18px;border:1px solid var(--line);border-radius:10px}} .source.selected{{border-color:var(--accent);box-shadow:inset 4px 0 0 var(--accent)}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:11px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{width:45%;font-weight:650}}
.metric{{font-size:24px;font-weight:800}} .muted,.source-meta{{color:var(--muted);font-size:13px;word-break:break-word}} .warning{{padding:16px;border-left:4px solid var(--warn);background:#fff8ea}}
footer{{padding:22px 46px 30px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}
@media print{{body{{background:#fff}} .page{{width:100%;margin:0;box-shadow:none}} @page{{size:A4;margin:12mm}}}}
</style>
</head>
<body><div class="page">
<header><div><div class="brand">TaxTreat</div><p class="eyebrow">Report srážkové daně</p><h1>{escape(_income(request.get('income_type')))}</h1><p>{escape(str(request.get('source_country') or '—'))} → {escape(str(request.get('recipient_country') or '—'))}</p></div><div><p class="eyebrow">ID reportu</p><strong>{escape(str(report.get('report_id') or '—'))}</strong><p class="muted">Vytvořeno {_date(report.get('generated_at'))}</p></div></header>
<main>
<section class="hero"><p class="eyebrow">Výsledek</p><h1>{escape(title)}</h1><p>{escape(explanation)}</p></section>
<section><h2>Transakce</h2><div class="grid"><div class="card"><p class="eyebrow">Hrubá částka</p><div class="metric">{_number(amount.get('amount'))} {escape(str(amount.get('currency') or ''))}</div></div><div class="card"><p class="eyebrow">Datum transakce</p><div class="metric">{_date(request.get('transaction_date'))}</div></div></div></section>
<section><h2>Skutkové údaje použité ve výpočtu</h2><table>{_fact_rows(report)}</table></section>
<section><h2>Právní základ</h2>{_legal_basis(report)}</section>
<section><h2>Podmínky a další kroky</h2><div class="grid"><div class="card"><p class="eyebrow">Odvod srážkové daně</p><div class="metric">{escape(str(deadline))}</div></div><div class="card"><p class="eyebrow">Oznámení</p><div class="metric">{escape(str(notification))}</div></div></div></section>
<section><h2>Dokumentace</h2><ul>{docs_html}</ul></section>
<section class="warning"><strong>Upozornění</strong><p>{escape(DISCLAIMER)}</p></section>
</main>
<footer>TaxTreat · dataset {escape(str(report.get('dataset_version') or report.get('legal_dataset_release') or '—'))} · právní stav {LEGAL_DATA_CUTOFF}</footer>
</div></body></html>"""
