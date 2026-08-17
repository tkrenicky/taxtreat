from .editorial import *
from .editorial import render_report_html as _render_report_html


def _plain_number(value):
    text = str(value if value is not None else "")
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _dedupe_sources(sources, selected_rule_id=None):
    """Collapse duplicate displays of the same legal provision.

    Distinct legal layers and distinct provisions remain separate. If the same
    provision is present more than once, prefer the entry selected by the
    decision engine so the displayed source keeps its applied-rule marker.
    """
    ordered_keys = []
    selected_by_key = {}
    for source in sources or []:
        source_key = source.get("source_id") or source.get("source_url") or source.get("legal_instrument")
        key = (
            source.get("legal_layer"),
            source_key,
            str(source.get("article") or ""),
            str(source.get("paragraph") or ""),
        )
        if key not in selected_by_key:
            ordered_keys.append(key)
            selected_by_key[key] = source
        elif source.get("rule_id") == selected_rule_id:
            selected_by_key[key] = source
    return [selected_by_key[key] for key in ordered_keys]


def render_report_html(report):
    result = report.get("result") or {}
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")

    # Render one card per actual legal provision, not one per internal rule-path
    # occurrence. This keeps legal references rich without duplicating the same
    # treaty article in the client document.
    render_report = dict(report)
    render_report["official_sources"] = _dedupe_sources(
        report.get("official_sources", []), selected_rule_id
    )
    html = _render_report_html(render_report)

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
        "Smlouva o zamezení dvojího zdanění · čl. ",
        "Smlouva o zamezení dvojího zdanění · článek ",
    )
    html = html.replace(
        "Protokol ke smlouvě o zamezení dvojího zdanění · čl. ",
        "Protokol ke smlouvě o zamezení dvojího zdanění · článek ",
    )
    html = html.replace(
        '<span>Česká srážková daň</span>',
        '<span>Srážková daň</span>',
    )
    html = html.replace(
        "Zadané údaje zatím neumožňují uzavřít použitelnou sazbu nebo režim. Otevřené body jsou uvedeny dále v reportu.",
        "Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo. Otevřené body jsou uvedeny dále v reportu.",
    )

    calculation = result.get("withholding_tax_calculation") or {}

    # A compact detailed calculation table complements the headline figures and
    # makes the basis of the tax amount explicit in the PDF.
    if calculation.get("status") == "CALCULATED":
        gross_czk = _plain_number(calculation.get("gross_amount_czk")) or "—"
        tax_czk = _plain_number(calculation.get("withholding_tax_czk")) or "—"
        rate = result.get("rate")
        foreign_only = result.get("tax_treatment") == "exclusive_foreign_taxation"
        rate_text = "Neuplatňuje se" if foreign_only else ("—" if rate is None else f"{_plain_number(rate)} %")
        tax_label = "Česká daň k odvodu" if foreign_only else "Srážková daň"
        detail = (
            '<div class="calculation-detail-wrap">'
            '<span class="mini-label">Detail výpočtu</span>'
            '<table class="calculation-detail"><tbody>'
            f'<tr><th>Daňový základ</th><td>{gross_czk} Kč</td></tr>'
            f'<tr><th>{tax_label}</th><td>{tax_czk} Kč</td></tr>'
            f'<tr><th>Sazba</th><td>{rate_text}</td></tr>'
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
