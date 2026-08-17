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

    html = html.replace(
        "<h1>",
        '<h1 aria-label="Informace k české srážkové dani">',
        1,
    )
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
    html = html.replace(
        '<span class="kicker">Applicable WHT rate</span>',
        '<span class="kicker">Pravidlo přiřazené k zadaným údajům</span><span class="result-caption">Applicable WHT rate</span>',
        1,
    )

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

    html = html.replace(
        "Zadané údaje zatím neumožňují přiřadit konkrétní sazbu nebo režim. Otevřené skutkové body jsou uvedeny dále v reportu.",
        "Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo. Otevřené skutkové body jsou uvedeny dále v reportu.",
    )

    foreign_only = result.get("tax_treatment") == "exclusive_foreign_taxation"
    if foreign_only:
        html = html.replace(
            "česká srážková daň neuplatní.</div>",
            "česká srážková daň neuplatní. Jde o pravidlo bez českého zdanění.</div>",
            1,
        )

    if calculation.get("status") == "CALCULATED":
        base = _display_number(calculation.get("gross_amount_czk"))
        tax = _display_number(calculation.get("withholding_tax_czk"))
        rate = result.get("rate")
        if foreign_only:
            rate_text = "Neuplatňuje se"
            tax_label = "Česká daň k odvodu"
            rate_aria = ' aria-label="Sazba Neuplatňuje se"'
        else:
            rate_text = "—" if rate is None else f"{_display_number(rate)} %"
            tax_label = "Srážková daň"
            rate_aria = ""
        detail = (
            '<div class="calculation-detail-wrap">'
            '<span class="kicker">Detail výpočtu</span>'
            '<table class="calculation-detail"><tbody>'
            f'<tr><th>Daňový základ</th><td>{base} Kč</td></tr>'
            f'<tr><th>{tax_label}</th><td>{tax} Kč</td></tr>'
            f'<tr{rate_aria}><th>Použitá sazba</th><td>{rate_text}</td></tr>'
            '</tbody></table></div>'
        )
        html = html.replace('<div class="path">', detail + '<div class="path">', 1)

    visual_overrides = (
        ".brand{font-family:Georgia,'Times New Roman',serif;font-size:16px;letter-spacing:-.035em}"
        ".sheet{border-radius:6mm;border-color:#e9e4d9;background:#fffdf9}"
        ".page{background:#f5f7fb}"
        ".hero{background:linear-gradient(105deg,#fff4dc 0%,#fff9ed 64%,#eef4ff 100%);border-radius:5mm;margin-left:-8mm;margin-right:-8mm;padding-left:8mm;padding-right:8mm}"
        ".hero h1,.section-head h2,.section-title-row h2,.legal-source h2,.section-card h3,.facts-card h3{font-family:Georgia,'Times New Roman',serif;letter-spacing:-.025em}"
        ".hero h1{color:#171717;font-size:27px}"
        ".kicker{color:#1557d6}"
        ".result-card{background:#fffaf0;border-color:#eee1c3}"
        ".facts-card{background:#f3f7ff;border-color:#dfe8fb}"
        ".section-card{border-radius:4mm}"
        ".page:nth-of-type(2) .section-head{background:#eef4ff}"
        ".page:nth-of-type(3) .section-head{background:#fff4dc}"
        ".page:nth-of-type(4) .section-head{background:#fff0eb}"
        ".page:nth-of-type(4) .deadline:nth-child(2n){background:#fff8e5}"
        ".page:nth-of-type(4) .deadline:nth-child(3n){background:#f2f6ff}"
        ".source-tab.selected{background:#eef4ff;border-left-color:#1557d6}"
        ".legal-source{background:#fffdfa;border-color:#e8e3da}"
        ".quote{background:#f7f4ee}"
        ".result-caption{display:block;margin-top:1mm;color:#77716a;font-size:6.5px;font-weight:700}"
        ".calculation-detail-wrap{margin:4mm 0 5mm;padding:4mm;border:1px solid var(--line);border-radius:4mm;background:#fff9ec}"
        ".calculation-detail{width:100%;margin-top:2mm;border-collapse:collapse;font-size:7.4px}"
        ".calculation-detail th,.calculation-detail td{padding:2mm 0;border-bottom:1px solid var(--line);text-align:left}"
        ".calculation-detail th{color:var(--muted);font-weight:700}"
        ".calculation-detail td{text-align:right;color:var(--ink);font-weight:800}"
        ".calculation-detail tr:last-child th,.calculation-detail tr:last-child td{border-bottom:0}"
        ".path-step{display:block!important;width:100%!important;padding:0 0 5mm!important}"
        ".path-step>div{display:block!important;width:100%!important;max-width:none!important}"
        ".path-step b{display:block!important;width:auto!important}"
        ".path-step p{display:block!important;width:auto!important;max-width:145mm!important}"
    )
    html = html.replace("</style>", visual_overrides + "</style>", 1)

    html = html.replace("#14295f", "#1557d6")
    html = html.replace("#2f68ce", "#1557d6")
    html = html.replace("#e8f8ed", "#fff0bd")
    html = html.replace("#169447", "#f37f69")
    html = html.replace("#ffd9a8", "#f37f69")
    html = html.replace("#cfe2ff", "#ffd05a")

    return html
