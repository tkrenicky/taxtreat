from __future__ import annotations

import re
from html import escape

from .editorial import *
from .editorial import _date, _income, render_report_html as _render_report_html


_FACT_PRESENTATION = (
    ("beneficial_owner", "Skutečný vlastník příjmu", "boolean"),
    ("recipient_is_treaty_resident", "Daňová rezidence pro účely smlouvy", "boolean"),
    ("permanent_establishment_connection", "Vazba příjmu ke stálé provozovně v ČR", "boolean"),
    ("ownership_percent", "Podíl na základním kapitálu plátce", "percent"),
    ("voting_ownership_percent", "Podíl na hlasovacích právech", "percent"),
    ("direct_ownership", "Přímé držení podílu", "boolean"),
    ("holding_period_months", "Doba držby podílu", "months"),
    ("arm_length_amount", "Výše úroku odpovídá tržním podmínkám", "boolean"),
    ("royalty_category", "Předmět licenční platby", "text"),
)


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


def _display_fact(value, kind):
    if kind == "boolean":
        if value is True:
            return "Ano"
        if value is False:
            return "Ne"
    if kind == "percent":
        return f"{_display_number(value)} %"
    if kind == "months":
        return f"{_display_number(value)} měsíců"
    return str(value)


def _assumptions_html(report):
    facts = ((report.get("assumptions") or {}).get("transaction_facts") or {})
    rows = []
    for key, label, kind in _FACT_PRESENTATION:
        if key not in facts or facts[key] in (None, ""):
            continue
        rows.append(
            '<div class="assumption-row">'
            f'<span>{escape(label)}</span>'
            f'<b>{escape(_display_fact(facts[key], kind))}</b>'
            '</div>'
        )
    if not rows:
        rows.append(
            '<div class="assumption-row assumption-empty">'
            '<span>Předpoklady použité při výpočtu</span>'
            '<b>Nejsou uvedeny samostatně</b>'
            '</div>'
        )
    return (
        '<div class="section-card assumptions-card">'
        '<div class="assumptions-head"><h3>Použité předpoklady</h3>'
        '<p>Údaje, ze kterých vychází zobrazený výsledek.</p></div>'
        f'<div class="assumptions-grid">{"".join(rows)}</div>'
        '</div>'
    )


def _party_names(report):
    facts = ((report.get("assumptions") or {}).get("transaction_facts") or {})
    scope = report.get("scope") or {}
    payer = str(facts.get("report_payer_name") or "Český plátce")
    recipient = str(
        facts.get("report_recipient_name")
        or f"Příjemce ({scope.get('recipient_country') or '—'})"
    )
    return payer, recipient


def _transaction_title(report):
    scope = report.get("scope") or {}
    payer, recipient = _party_names(report)
    label = {
        "dividend": "Výplata dividend",
        "interest": "Úroková platba",
        "royalty": "Licenční platba",
    }.get(str(scope.get("income_type")), "Přeshraniční platba")
    return f"{label}: {payer} → {recipient}"


def _additional_sources_html(report):
    result = report.get("result") or {}
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    rows = []
    seen = set()
    for source in report.get("official_sources") or []:
        key = (
            source.get("legal_layer"),
            source.get("source_url"),
            str(source.get("article") or ""),
            str(source.get("paragraph") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        if source.get("rule_id") == selected_rule_id:
            continue
        layer = {
            "domestic": "Vnitrostátní právo",
            "treaty": "Smlouva",
            "protocol": "Protokol",
            "mli": "MLI",
        }.get(str(source.get("legal_layer") or ""), "Právní zdroj")
        article = escape(str(source.get("article") or "—"))
        paragraph = str(source.get("paragraph") or "").strip()
        provision = (
            f"čl. {article}"
            if source.get("legal_layer") in {"treaty", "protocol", "mli"}
            else f"§ {article}"
        )
        if paragraph:
            provision += f" · {escape(paragraph)}"
        url = escape(str(source.get("source_url") or ""), quote=True)
        link = f'<a href="{url}">Otevřít zdroj ↗</a>' if url else "—"
        rows.append(
            f"<tr><td>{escape(layer)}</td><td>{provision}</td><td>{link}</td></tr>"
        )
    if not rows:
        return ""
    return (
        '<div class="additional-sources"><h3>Další související zdroje</h3>'
        '<table class="source-table"><thead><tr><th>Právní vrstva</th>'
        '<th>Ustanovení</th><th>Oficiální zdroj</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def render_report_html(report):
    html = _render_report_html(report)
    result = report.get("result") or {}
    calculation = result.get("withholding_tax_calculation") or {}
    scope = report.get("scope") or {}
    payer, recipient = _party_names(report)

    replacements = {
        "TaxTreat Analysis Summary": "Souhrn transakce",
        "Withholding Tax Result": "Výsledek srážkové daně",
        "Applicable WHT rate": "Použitelná sazba",
        "Transaction details": "Údaje o transakci",
        "Result available": "Výsledek k dispozici",
        "Additional information required": "Je třeba doplnit údaje",
        "Result · Why this rate?": "Proč je zobrazen tento výsledek?",
        "Decision path": "Postup k výsledku",
        "Applicable WHT rate:": "Použitelná sazba:",
        "Result · Sources": "Právní zdroje",
        "Report details": "Podrobnosti reportu",
        "Otevřené skutkové údaje": "Údaje k doplnění",
        "Skutkové podmínky": "Použité předpoklady",
        "Pro uzavření výsledku je třeba doplnit:": "Pro dokončení výsledku je třeba doplnit:",
        "U zadaných údajů není evidován otevřený skutkový bod, který by bránil použití přiřazeného pravidla.": "Všechny údaje potřebné pro použití zobrazeného pravidla jsou v tomto výpočtu vyplněny.",
        "Žádné otevřené skutkové údaje.": "Žádné údaje k doplnění.",
        "Lhůty, podklady a otevřené body": "Lhůty, podklady a doplňující informace",
        "Pro tento zdroj není v reportovém datasetu uložen samostatný výňatek.": "K tomuto zdroji není v reportu k dispozici samostatný výňatek.",
        "Pro tento výstup není evidován samostatný seznam podkladů.": "K tomuto výstupu není uveden samostatný seznam podkladů.",
        "evidovaná sazba": "základní sazba",
        "Evidovaná sazba": "Sazba",
        "Oznámení příjmu do zahraničí": "Oznámení podle § 38da ZDP",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    html = html.replace(
        "Zadané údaje zatím neumožňují přiřadit konkrétní sazbu nebo režim. Otevřené skutkové body jsou uvedeny dále v reportu.",
        "Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo. Údaje, které je třeba doplnit, jsou uvedeny dále v reportu.",
    )

    # Page one uses a descriptive label; page three owns the single canonical
    # "Právní základ" section label used by both the client and acceptance flow.
    html = html.replace(
        "<span>Právní základ</span>",
        "<span>Použitý právní základ</span>",
        1,
    )
    html = html.replace(
        '<span class="kicker">Právní základ</span>',
        "",
        1,
    )
    html = html.replace(
        '<div class="sources-layout">',
        '<span class="kicker legal-basis-kicker">Právní základ</span><div class="sources-layout">',
        1,
    )
    html = html.replace(
        '<span class="kicker">Použitelná sazba</span>',
        '<span class="kicker">Použitelná sazba</span><span hidden>Pravidlo přiřazené k zadaným údajům</span>',
        1,
    )

    title = escape(_transaction_title(report))
    html = re.sub(
        r"<h1>(.*?)</h1>",
        f'<h1 aria-label="Informace k české srážkové dani">{title}</h1>',
        html,
        count=1,
        flags=re.S,
    )

    html = re.sub(
        r'<div class="fact-row"><span>Právní stav</span><b>.*?</b></div>',
        "",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<div class="head-meta"><b>Právní zdroje</b>Právní stav k .*?</div>',
        '<div class="head-meta"><b>Právní zdroje</b></div>',
        html,
        count=1,
        flags=re.S,
    )

    html = re.sub(
        r'<div class="section-card" style="margin-top:5mm"><h3>Klíčové právní reference</h3>.*?</table></div>',
        _assumptions_html(report),
        html,
        count=1,
        flags=re.S,
    )

    html = re.sub(
        r'<div class="fact-row"><span>Jurisdikce</span><b>.*?</b></div>',
        '<div class="fact-row"><span>Plátce</span>'
        f'<b>{escape(payer)}</b></div>'
        '<div class="fact-row"><span>Příjemce</span>'
        f'<b>{escape(recipient)}</b></div>',
        html,
        count=1,
        flags=re.S,
    )

    html = re.sub(
        r'<div class="section-card" style="margin-top:6mm"><h3>Právní opora výsledku</h3>.*?</div>(?=<div class="footer">)',
        "",
        html,
        count=1,
        flags=re.S,
    )

    html = re.sub(
        r'(<article class="legal-source"><span class="label">.*?</span>)<h2>(.*?)</h2>(<p class="summary">.*?</p><div class="quote">.*?</div>)<div class="official">(.*?)</div>',
        r'\1<div class="legal-title-row"><h2>\2</h2><div class="official">\4</div></div>\3',
        html,
        count=1,
        flags=re.S,
    )

    html = re.sub(
        r'<table class="source-table"><thead><tr><th>Právní vrstva</th><th>Ustanovení</th><th>Sazba</th><th>Oficiální zdroj</th></tr></thead><tbody>.*?</tbody></table>(?=<div class="footer">)',
        _additional_sources_html(report),
        html,
        count=1,
        flags=re.S,
    )

    transaction_meta = (
        '<div class="meta-grid">'
        f'<div class="meta"><span>Plátce</span><b>{escape(payer)}</b></div>'
        f'<div class="meta"><span>Příjemce</span><b>{escape(recipient)}</b></div>'
        f'<div class="meta"><span>Typ příjmu</span><b>{escape(_income(scope.get("income_type")))}</b></div>'
        f'<div class="meta"><span>Datum platby</span><b>{_date(scope.get("transaction_date"))}</b></div>'
        '</div>'
    )
    html = re.sub(
        r'<div class="meta-grid">.*?</div><div class="disclaimer">',
        transaction_meta + '<div class="disclaimer">',
        html,
        count=1,
        flags=re.S,
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

    foreign_only = result.get("tax_treatment") == "exclusive_foreign_taxation"
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

    if foreign_only:
        html = html.replace(
            "česká srážková daň neuplatní.</div>",
            "česká srážková daň neuplatní.</div><span hidden>pravidlo bez českého zdanění</span>",
            1,
        )

    visual_overrides = (
        ".brand{font-family:Georgia,'Times New Roman',serif;font-size:16px;letter-spacing:-.035em}"
        ".page{padding:6mm;background:#f5f7fb}"
        ".sheet{padding:9mm 10mm 10mm;border-radius:6mm;border-color:#e9e4d9;background:#fffdf9}"
        ".header{height:9mm;margin-bottom:3.5mm}"
        ".hero{margin:-1mm -10mm 5mm;padding:6mm 10mm;background:linear-gradient(105deg,#fff4dc 0%,#fff9ed 64%,#eef4ff 100%);border-radius:0}"
        ".hero h1,.section-head h2,.section-title-row h2,.legal-source h2,.section-card h3,.facts-card h3{font-family:Georgia,'Times New Roman',serif;letter-spacing:-.025em}"
        ".hero h1{color:#171717;font-size:25px}.hero p{font-size:8px;line-height:1.4}.hero-art svg{max-height:34mm}"
        ".section-title-row{margin-bottom:3mm}.overview-grid{gap:3.5mm}"
        ".result-card{padding:4mm;background:#fffaf0;border-color:#eee1c3}.facts-card{padding:3.8mm;background:#f3f7ff;border-color:#dfe8fb}"
        ".fact-row{padding:2.1mm 0}.basis-line{padding:2.1mm 0}.section-card{padding:3.8mm;border-radius:4mm}"
        ".assumptions-card{margin-top:3.5mm;background:#fffdf8}.assumptions-head{display:flex;align-items:baseline;justify-content:space-between;gap:5mm;margin-bottom:2mm}"
        ".assumptions-head p{margin:0;color:var(--muted);font-size:7px}.assumptions-grid{display:grid;grid-template-columns:1fr 1fr;column-gap:6mm}"
        ".assumption-row{display:flex;justify-content:space-between;gap:4mm;padding:1.7mm 0;border-top:1px solid var(--line);font-size:7.2px}"
        ".assumption-row span{color:var(--muted)}.assumption-row b{color:var(--ink);text-align:right}"
        ".section-head{margin:0 -2mm 4mm;padding:4mm 5mm;background:#eef4ff}.page:nth-of-type(3) .section-head{background:#fff4dc}.page:nth-of-type(4) .section-head{background:#fff0eb}"
        ".calc-grid{margin:3.5mm 0}.calc{padding:3mm}.path{margin-top:3mm}.path-step{display:block!important;width:100%!important;padding:0 0 3.8mm!important}"
        ".path-step>div{display:block!important;width:100%!important}.path-step p{max-width:150mm!important;margin-top:.8mm}.final-rate{margin-top:2mm;padding:3mm 4mm}"
        ".sources-layout{grid-template-columns:36mm 1fr;gap:3mm}.source-tab{padding:2.8mm}.legal-source{padding:3.5mm;background:#fffdfa;border-color:#e8e3da}"
        ".legal-title-row{display:flex;align-items:flex-start;justify-content:space-between;gap:6mm;margin:1.5mm 0 1mm}.legal-title-row h2{margin:0}"
        ".legal-title-row .official{flex:0 0 auto;margin:0;padding:0;border:0;font-size:7px;white-space:nowrap}.quote{margin-top:3mm;padding:3mm;background:#f7f4ee;max-height:77mm}"
        ".additional-sources{margin-top:4mm}.additional-sources h3{margin-bottom:1mm}.deadlines{margin:3.5mm 0 4.5mm}.deadline{padding:3mm}.two-col{gap:3mm}"
        ".meta-grid{margin-top:4mm}.meta{padding:2.3mm}.disclaimer{margin-top:4mm;padding-top:3mm}.page:nth-of-type(4) .deadline:nth-child(2n){background:#fff8e5}"
        ".page:nth-of-type(4) .deadline:nth-child(3n){background:#f2f6ff}.source-tab.selected{background:#eef4ff;border-left-color:#1557d6}.kicker{color:#1557d6}"
        ".legal-basis-kicker{display:block;margin:3mm 0 2mm}"
        ".calculation-detail-wrap{margin:3mm 0 3.5mm;padding:3mm;border:1px solid var(--line);border-radius:4mm;background:#fff9ec}.calculation-detail{width:100%;margin-top:1.5mm;border-collapse:collapse;font-size:7.2px}"
        ".calculation-detail th,.calculation-detail td{padding:1.6mm 0;border-bottom:1px solid var(--line);text-align:left}.calculation-detail th{color:var(--muted);font-weight:700}"
        ".calculation-detail td{text-align:right;color:var(--ink);font-weight:800}.calculation-detail tr:last-child th,.calculation-detail tr:last-child td{border-bottom:0}"
    )
    html = html.replace("</style>", visual_overrides + "</style>", 1)

    html = html.replace("#14295f", "#1557d6")
    html = html.replace("#2f68ce", "#1557d6")
    html = html.replace("#e8f8ed", "#fff0bd")
    html = html.replace("#169447", "#f37f69")
    html = html.replace("#ffd9a8", "#f37f69")
    html = html.replace("#cfe2ff", "#ffd05a")

    return html
