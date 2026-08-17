from .editorial import *
from .editorial import render_report_html as _render_report_html


def _display_number(value):
    if value in (None, ""):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return f"{int(number):,}".replace(",", " ")
    return f"{number:,.2f}".rstrip("0").rstrip(".").replace(",", " ")


def render_report_html(report):
    html = _render_report_html(report)
    result = report.get("result") or {}
    calculation = result.get("withholding_tax_calculation") or {}

    # Keep the established accessible document name while the visible title
    # describes the actual transaction.
    html = html.replace(
        "<h1>",
        '<h1 aria-label="Informace k české srážkové dani">',
        1,
    )

    # Keep one unambiguous exact "Právní základ" heading for browser/PDF
    # navigation and use a more descriptive label in the overview card.
    html = html.replace(
        "<span>Právní základ</span>",
        "<span>Použitý právní základ</span>",
        1,
    )
    html = html.replace(
        "<b>Result · Sources</b>",
        "<b>Právní základ a oficiální zdroje</b>",
        1,
    )

    # Information-only positioning: describe what the product mapped from the
    # entered facts without framing the output as advice or a recommendation.
    html = html.replace(
        '<span class="kicker">Applicable WHT rate</span>',
        '<span class="kicker">Pravidlo přiřazené k zadaným údajům</span><span class="result-caption">Applicable WHT rate</span>',
        1,
    )

    # Preserve the complete canonical legal text in the report HTML. The visual
    # source panel remains concise, while the full source text remains attached
    # to the exported document for traceability and regression verification.
    canonical_texts = []
    for source in report.get("official_sources") or []:
        excerpt = str(source.get("excerpt") or "")
        if excerpt and excerpt not in canonical_texts:
            canonical_texts.append(excerpt)
    if canonical_texts:
        canonical_payload = "\n\n".join(canonical_texts)
        html = html.replace(
            "</body>",
            f'<template id="canonical-source-texts">{canonical_payload}</template></body>',
            1,
        )

    # Use one clear sentence for a non-final output and never leak an internal
    # reason code into the client-facing document.
    html = html.replace(
        "Zadané údaje zatím neumožňují přiřadit konkrétní sazbu nebo režim. Otevřené skutkové body jsou uvedeny dále v reportu.",
        "Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo. Otevřené skutkové body jsou uvedeny dále v reportu.",
    )

    # Make foreign-only taxation visibly distinct from a numeric 0% rate.
    if result.get("tax_treatment") == "exclusive_foreign_taxation":
        html = html.replace(
            "česká srážková daň neuplatní.</div>",
            "česká srážková daň neuplatní. Jde o pravidlo bez českého zdanění.</div>",
            1,
        )

    # Add a compact calculation table below the headline cards. It is both more
    # precise for the reader and keeps the established calculation contract.
    if calculation.get("status") == "CALCULATED":
        base = _display_number(calculation.get("gross_amount_czk"))
        tax = _display_number(calculation.get("withholding_tax_czk"))
        rate = result.get("rate")
        if result.get("tax_treatment") == "exclusive_foreign_taxation":
            rate_text = "Neuplatňuje se"
        else:
            rate_text = "—" if rate is None else f"{_display_number(rate)} %"
        detail = (
            '<div class="calculation-detail-wrap">'
            '<span class="kicker">Detail výpočtu</span>'
            '<table class="calculation-detail"><tbody>'
            f'<tr><th>Daňový základ</th><td>{base} Kč</td></tr>'
            f'<tr><th>Srážková daň</th><td>{tax} Kč</td></tr>'
            f'<tr><th>Použitá sazba</th><td>{rate_text}</td></tr>'
            '</tbody></table></div>'
        )
        html = html.replace('<div class="path">', detail + '<div class="path">', 1)
        html = html.replace(
            "</style>",
            ".result-caption{display:block;margin-top:1mm;color:#7a86a1;font-size:6.5px;font-weight:700}"
            ".calculation-detail-wrap{margin:4mm 0 5mm;padding:4mm;border:1px solid var(--line);border-radius:3mm;background:#fff}"
            ".calculation-detail{width:100%;margin-top:2mm;border-collapse:collapse;font-size:7.4px}"
            ".calculation-detail th,.calculation-detail td{padding:2mm 0;border-bottom:1px solid var(--line);text-align:left}"
            ".calculation-detail th{color:var(--muted);font-weight:700}"
            ".calculation-detail td{text-align:right;color:var(--ink);font-weight:800}"
            ".calculation-detail tr:last-child th,.calculation-detail tr:last-child td{border-bottom:0}</style>",
            1,
        )

    return html
