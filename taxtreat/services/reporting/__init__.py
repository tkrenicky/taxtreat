from .editorial import *
from .editorial import render_report_html as _render_report_html


def _plain_number(value):
    text = str(value if value is not None else "")
    if text.endswith(".0"):
        text = text[:-2]
    return text


def render_report_html(report):
    html = _render_report_html(report)

    # Keep the established accessible document name while allowing the visible
    # cover title to describe the actual transaction.
    html = html.replace(
        "<h1>",
        '<h1 aria-label="Informace k české srážkové dani">',
        1,
    )

    # Do not expose the internal deterministic report identifier in the client
    # document. It remains available in the structured report data only.
    report_id = str(report.get("report_id") or "")
    if report_id:
        html = html.replace(f"Report {report_id}", "")
        html = html.replace(report_id, "")

    # Concise professional section hierarchy.
    html = html.replace(
        '<span class="mini-label">Výsledek</span>',
        '<span class="mini-label">Pravidlo přiřazené k zadaným údajům</span>',
        1,
    )
    html = html.replace(
        '<div class="section-title"><h2>Výpočet a právní logika</h2>',
        '<div class="section-title"><h2>Použité právní pravidlo</h2>',
        1,
    )
    html = html.replace(
        '<div class="section-title"><h2>Právní základ a oficiální zdroje</h2>',
        '<div class="section-title"><h2>Právní základ</h2>',
        1,
    )
    html = html.replace(
        '<div class="docmeta"><b>Právní základ</b>',
        '<div class="docmeta"><b>Právní základ a oficiální zdroje</b>',
        1,
    )
    html = html.replace('class="source-card', 'class="legal-source source-card')
    html = html.replace(
        '<span>Česká srážková daň</span>',
        '<span>Srážková daň</span>',
    )
    html = html.replace(
        "Zadané údaje zatím neumožňují uzavřít použitelnou sazbu nebo režim. Otevřené body jsou uvedeny dále v reportu.",
        "Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo. Otevřené body jsou uvedeny dále v reportu.",
    )

    result = report.get("result") or {}
    calculation = result.get("withholding_tax_calculation") or {}

    # A compact detailed calculation table complements the headline figures and
    # makes the basis of the tax amount explicit in the PDF.
    if calculation.get("status") == "CALCULATED":
        gross_czk = _plain_number(calculation.get("gross_amount_czk")) or "—"
        tax_czk = _plain_number(calculation.get("withholding_tax_czk")) or "—"
        rate = result.get("rate")
        rate_text = "—" if rate is None else f"{_plain_number(rate)} %"
        detail = (
            '<div class="calculation-detail-wrap">'
            '<span class="mini-label">Detail výpočtu</span>'
            '<table class="calculation-detail"><tbody>'
            f'<tr><th>Daňový základ</th><td>{gross_czk} Kč</td></tr>'
            f'<tr><th>Srážková daň</th><td>{tax_czk} Kč</td></tr>'
            f'<tr><th>Použitá sazba</th><td>{rate_text}</td></tr>'
            '</tbody></table></div>'
        )
        html = html.replace('<div class="steps">', detail + '<div class="steps">', 1)
        html = html.replace(
            "</style>",
            ".calculation-detail-wrap{margin:7mm 0 1mm}.calculation-detail{width:100%;border-collapse:collapse;border:1px solid var(--line);background:#fff}.calculation-detail th,.calculation-detail td{padding:3.5mm 4mm;border-bottom:1px solid var(--line);text-align:left}.calculation-detail th{width:42%;color:var(--muted);font-size:9px;font-weight:700}.calculation-detail td{color:var(--ink);font-size:10px;font-weight:700}.calculation-detail tr:last-child th,.calculation-detail tr:last-child td{border-bottom:0}</style>",
            1,
        )

    if result.get("tax_treatment") == "exclusive_foreign_taxation":
        html = html.replace(
            " se při zadaných skutečnostech česká srážková daň neuplatní.",
            " představuje při zadaných skutečnostech pravidlo bez českého zdanění; česká srážková daň se proto neuplatní.",
        )

    return html
