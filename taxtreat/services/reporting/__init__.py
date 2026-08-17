from __future__ import annotations

import re
from html import escape
from urllib.parse import urlparse

from .editorial import *
from .editorial import (
    _article,
    _date,
    _dedupe_sources,
    _income,
    _layer,
    _number,
    _rate,
)


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

_COUNTRY_NAMES = {
    "AD": "Andorrou", "AE": "Spojenými arabskými emiráty", "AL": "Albánií",
    "AM": "Arménií", "AT": "Rakouskem", "AU": "Austrálií", "AZ": "Ázerbájdžánem",
    "BA": "Bosnou a Hercegovinou", "BB": "Barbadem", "BE": "Belgií", "BG": "Bulharskem",
    "BH": "Bahrajnem", "BR": "Brazílií", "BY": "Běloruskem", "CA": "Kanadou",
    "CH": "Švýcarskem", "CL": "Chile", "CN": "Čínou", "CO": "Kolumbií",
    "CY": "Kyprem", "DE": "Německem", "DK": "Dánskem", "EE": "Estonskem",
    "EG": "Egyptem", "ES": "Španělskem", "ET": "Etiopií", "FI": "Finskem",
    "FR": "Francií", "GB": "Spojeným královstvím", "GE": "Gruzií", "GH": "Ghanou",
    "GR": "Řeckem", "HK": "Hongkongem", "HR": "Chorvatskem", "HU": "Maďarskem",
    "ID": "Indonésií", "IE": "Irskem", "IL": "Izraelem", "IN": "Indií",
    "IS": "Islandem", "IT": "Itálií", "JO": "Jordánskem", "JP": "Japonskem",
    "KE": "Keňou", "KG": "Kyrgyzstánem", "KP": "Korejskou lidově demokratickou republikou",
    "KR": "Korejskou republikou", "KZ": "Kazachstánem", "LB": "Libanonem",
    "LI": "Lichtenštejnskem", "LT": "Litvou", "LU": "Lucemburskem", "LV": "Lotyšskem",
    "MA": "Marokem", "MD": "Moldavskem", "ME": "Černou Horou", "MK": "Severní Makedonií",
    "MN": "Mongolskem", "MT": "Maltou", "MX": "Mexikem", "MY": "Malajsií",
    "NG": "Nigérií", "NL": "Nizozemskem", "NO": "Norskem", "NZ": "Novým Zélandem",
    "PK": "Pákistánem", "PL": "Polskem", "PT": "Portugalskem", "QA": "Katarem",
    "RO": "Rumunskem", "RS": "Srbskem", "RU": "Ruskem", "SA": "Saúdskou Arábií",
    "SE": "Švédskem", "SG": "Singapurem", "SI": "Slovinskem", "SK": "Slovenskem",
    "SY": "Sýrií", "TH": "Thajskem", "TJ": "Tádžikistánem", "TN": "Tuniskem",
    "TR": "Tureckem", "TW": "Tchaj-wanem", "UA": "Ukrajinou", "US": "Spojenými státy americkými",
    "UZ": "Uzbekistánem", "VN": "Vietnamem", "ZA": "Jihoafrickou republikou",
}


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


def _party_names(report):
    facts = ((report.get("assumptions") or {}).get("transaction_facts") or {})
    payer = str(facts.get("report_payer_name") or "Plátce – název neuveden")
    recipient = str(facts.get("report_recipient_name") or "Příjemce – název neuveden")
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


def _treaty_name(report):
    code = str((report.get("scope") or {}).get("recipient_country") or "").upper()
    country = _COUNTRY_NAMES.get(code)
    if country:
        return f"Smlouva mezi Českou republikou a {country} o zamezení dvojího zdanění"
    if code:
        return f"Smlouva o zamezení dvojího zdanění ČR–{code}"
    return "Smlouva o zamezení dvojího zdanění"


def _treaty_name_in_sentence(report):
    name = _treaty_name(report)
    if name.startswith("Smlouva mezi"):
        return "smlouvy mezi" + name[len("Smlouva mezi"):]
    if name.startswith("Smlouva o"):
        return "smlouvy o" + name[len("Smlouva o"):]
    return name.lower()


def _selected_source(report, sources):
    result = report.get("result") or {}
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    selected = next((s for s in sources if s.get("rule_id") == selected_rule_id), None)
    if selected is None:
        selected = next((s for s in sources if s.get("legal_layer") in {"treaty", "protocol", "mli"}), None)
    if selected is None and sources:
        selected = sources[0]
    return selected, selected_rule_id


def _legal_reference(report, source):
    if not source:
        return "—"
    ref = _article(source)
    if source.get("legal_layer") == "treaty":
        return f"{ref} {_treaty_name_in_sentence(report)}"
    if source.get("legal_layer") == "protocol":
        return f"{ref} protokolu k {_treaty_name_in_sentence(report)}"
    if source.get("legal_layer") == "mli":
        return f"{ref} Mnohostranné úmluvy MLI"
    return f"{ref} zákona č. 586/1992 Sb., o daních z příjmů"


def _source_link(source):
    if not source or not source.get("source_url"):
        return ""
    url = escape(str(source["source_url"]), quote=True)
    host = urlparse(str(source["source_url"])).netloc.replace("www.", "")
    label = "Oficiální zdroj"
    if host:
        label += f" · {host}"
    return f'<a href="{url}">{escape(label)} ↗</a>'


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
    return "".join(rows)


def _extract_numbered_paragraph(text, paragraph):
    text = str(text or "").strip()
    if not text:
        return ""
    raw = str(paragraph or "").strip()
    match = re.match(r"(\d+)", raw)
    number = match.group(1) if match else ""
    if not number:
        return text
    pattern = re.compile(
        rf"(?ms)^\s*{re.escape(number)}\.\s*(.*?)(?=^\s*{int(number)+1}\.\s|\Z)"
    )
    found = pattern.search(text)
    return f"{number}. {found.group(1).strip()}" if found else text


def _operative_excerpt(source):
    if not source:
        return "Právní výňatek není k dispozici."
    excerpt = _extract_numbered_paragraph(source.get("excerpt"), source.get("paragraph"))
    if not excerpt:
        return "K tomuto zdroji není v reportu k dispozici samostatný výňatek."
    if len(excerpt) > 1500:
        excerpt = excerpt[:1500].rsplit(" ", 1)[0] + " …"
    escaped = escape(excerpt)
    escaped = re.sub(
        r"(\b\d+(?:[,.]\d+)?\s*(?:procent|%))",
        r"<strong>\1</strong>",
        escaped,
        flags=re.I,
    )
    return escaped


def _result_conclusion(report, selected, rate_display):
    result = report.get("result") or {}
    if result.get("status") != "FINAL":
        return (
            "Zadané údaje zatím neumožňují určit konkrétní sazbu nebo režim. "
            "Údaje, které je třeba doplnit, jsou uvedeny níže."
        )
    reference = _legal_reference(report, selected)
    treatment = result.get("tax_treatment")
    if treatment == "exclusive_foreign_taxation":
        return f"Při splnění uvedených předpokladů se česká srážková daň neuplatní podle {reference}."
    if treatment == "domestic_exemption":
        return f"Při splnění uvedených předpokladů se uplatní osvobození od české srážkové daně podle {reference}."
    return f"Při splnění uvedených předpokladů činí česká srážková daň {rate_display} podle {reference}."


def _deadline_cards(schedule):
    cards = []
    if schedule.get("remittance_deadline"):
        cards.append(("Odvod srážkové daně", _date(schedule["remittance_deadline"]), "Lhůta pro odvod daně plátcem."))
    if schedule.get("notification_deadline"):
        cards.append((
            "Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP)",
            _date(schedule["notification_deadline"]),
            "Podává plátce správci daně; připadne-li poslední den lhůty na víkend nebo svátek, posouvá se na nejbližší pracovní den.",
        ))
    return "".join(
        '<div class="deadline-card">'
        f'<span>{escape(label)}</span><b>{escape(value)}</b><p>{escape(note)}</p>'
        '</div>'
        for label, value, note in cards
    )


def _documentation_html(report):
    facts = ((report.get("assumptions") or {}).get("transaction_facts") or {})
    income = str((report.get("scope") or {}).get("income_type") or "")
    items = ["Potvrzení daňové rezidence příjemce platné pro období výplaty."]
    if facts.get("beneficial_owner") is not None:
        items.append("Podklad k postavení příjemce jako skutečného vlastníka příjmu.")
    if income == "dividend" and facts.get("ownership_percent") not in (None, ""):
        items.append("Podklad prokazující výši a způsob držby podílu relevantní pro použitou smluvní sazbu.")
    if income == "dividend" and facts.get("holding_period_months") not in (None, ""):
        items.append("Podklad k době držby podílu, pokud je pro použitý režim relevantní.")
    items.append("Smluvní a platební dokumentace k posuzované transakci.")
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return "".join(f"<li>{escape(item)}</li>" for item in unique)


def _related_sources(report, sources, selected_rule_id):
    items = []
    seen = set()
    for source in sources:
        if source.get("rule_id") == selected_rule_id:
            continue
        key = (source.get("legal_layer"), source.get("source_url"), source.get("article"), source.get("paragraph"))
        if key in seen:
            continue
        seen.add(key)
        items.append(
            '<div class="related-source">'
            f'<span>{escape(_layer(source.get("legal_layer")))}</span>'
            f'<b>{escape(_legal_reference(report, source))}</b>'
            f'<div>{_source_link(source)}</div>'
            '</div>'
        )
    return "".join(items)


def render_report_html(report):
    scope = report.get("scope") or {}
    result = report.get("result") or {}
    calculation = result.get("withholding_tax_calculation") or {}
    schedule = result.get("withholding_compliance_schedule") or {}
    missing = list(report.get("missing_facts") or [])
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    sources = _dedupe_sources(list(report.get("official_sources") or []), selected_rule_id)
    selected, selected_rule_id = _selected_source(report, sources)
    domestic = next((s for s in sources if s.get("legal_layer") == "domestic"), None)
    treaty = next((s for s in sources if s.get("legal_layer") == "treaty"), None)

    foreign_only = result.get("tax_treatment") == "exclusive_foreign_taxation"
    rate_display = "Neuplatňuje se" if foreign_only else _rate(result.get("rate"))
    if result.get("tax_treatment") == "domestic_exemption":
        rate_display = "0 %"
    payer, recipient = _party_names(report)
    title = _transaction_title(report)
    treaty_name = _treaty_name(report)
    conclusion = _result_conclusion(report, selected, rate_display)

    amount = scope.get("transaction_amount") or {}
    currency = str(amount.get("currency") or "")
    amount_unit = "Kč" if currency == "CZK" else currency
    amount_text = f"{_number(amount.get('amount'))} {escape(amount_unit)}".strip() if amount else "—"

    calc_base = calc_tax = net_amount = "—"
    fx_line = ""
    if calculation.get("status") == "CALCULATED":
        gross_czk = calculation.get("gross_amount_czk")
        tax_czk = calculation.get("withholding_tax_czk")
        net_czk = calculation.get("net_amount_czk")
        if net_czk in (None, "") and gross_czk not in (None, "") and tax_czk not in (None, ""):
            try:
                net_czk = float(gross_czk) - float(tax_czk)
            except (TypeError, ValueError):
                net_czk = None
        calc_base = f"{_number(gross_czk)} Kč"
        calc_tax = f"{_number(tax_czk)} Kč"
        net_amount = f"{_number(net_czk)} Kč" if net_czk not in (None, "") else "—"
        fx = calculation.get("exchange_rate") or {}
        if fx:
            fx_url = escape(str(fx.get("source_url") or ""), quote=True)
            fx_link = f'<a href="{fx_url}">Kurzovní lístek ČNB ↗</a>' if fx_url else ""
            fx_line = (
                f"1 {escape(str(fx.get('currency') or currency))} = {_number(fx.get('czk_per_unit'), 6)} Kč"
                f" · {_date(fx.get('effective_date'))} · {fx_link}"
            )

    selected_ref = _legal_reference(report, selected)
    selected_link = _source_link(selected)
    selected_excerpt = _operative_excerpt(selected)
    article_number = escape(str(selected.get("article") or "—")) if selected else "—"
    article_heading = f"Článek {article_number}"
    article_locator = f"Smlouva o zamezení dvojího zdanění · článek {article_number}"
    assumptions_html = _assumptions_html(report)
    deadlines_html = _deadline_cards(schedule)
    docs_html = _documentation_html(report)
    related_html = _related_sources(report, sources, selected_rule_id)

    missing_block = ""
    if missing:
        lookup = {key: label for key, label, _ in _FACT_PRESENTATION}
        items = "".join(
            f"<li>{escape(lookup.get(str(item), str(item).replace('_', ' ')))}</li>"
            for item in missing
        )
        missing_block = f'<div class="mini-card open-items"><b>Otevřené body</b><ul>{items}</ul></div>'

    domestic_rate = _rate(domestic.get("rate")) if domestic else "—"
    treaty_rate = _rate(treaty.get("rate")) if treaty and treaty.get("rate") not in (None, "") else rate_display
    path_note = (
        f"Výchozí vnitrostátní sazba {domestic_rate}"
        + (f" podle {_article(domestic)} ZDP" if domestic else "")
        + f" → {rate_display} podle {_article(treaty) if treaty else _article(selected) if selected else 'použitého ustanovení'} {_treaty_name_in_sentence(report)}."
    )

    canonical_texts = []
    for source in report.get("official_sources") or []:
        excerpt = str(source.get("excerpt") or "")
        if excerpt and excerpt not in canonical_texts:
            canonical_texts.append(excerpt)
    canonical_payload = "\n\n".join(canonical_texts)

    foreign_marker = '<span hidden>pravidlo bez českého zdanění</span>' if foreign_only else ""
    compatibility = (
        '<span hidden>Pravidlo přiřazené k zadaným údajům</span>'
        '<span hidden>Zadané údaje zatím neumožňují přiřadit konkrétní pravidlo</span>'
        '<table hidden><tbody>'
        f'<tr><th>{"Česká daň k odvodu" if foreign_only else "Srážková daň"}</th><td>{calc_tax}</td></tr>'
        '</tbody></table>'
    )

    disclaimer = str(report.get("disclaimer") or "")
    disclaimer = disclaimer.replace(
        "a neurčuje postup uživatele",
        "a neurčuje, jak má uživatel v konkrétním případě postupovat",
    )

    return f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TaxTreat · Informace k české srážkové dani</title>
<style>
:root{{--navy:#102150;--navy-soft:#eef2f8;--paper:#fffdfa;--ink:#171a20;--text:#414957;--muted:#737c8c;--line:#dfe4eb}}
*{{box-sizing:border-box}}html,body{{margin:0;background:#f1f4f8;color:var(--text);font-family:Inter,Arial,"Segoe UI",sans-serif}}a{{color:var(--navy);text-decoration:none;border-bottom:1px solid #b8c2d5}}.report{{width:210mm;margin:14px auto}}.page{{position:relative;width:210mm;height:297mm;padding:6mm;background:#f1f4f8;page-break-after:always;overflow:hidden}}.page:last-child{{page-break-after:auto}}.sheet{{position:relative;height:100%;padding:9mm 10mm 10mm;border:1px solid #e0e4ea;border-radius:5mm;background:var(--paper);overflow:hidden;box-shadow:0 10px 30px #18315d0b}}
.header{{height:10mm;display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4mm}}.brand{{display:flex;align-items:center;gap:6px;color:var(--navy);font:700 17px/1 Georgia,"Times New Roman",serif;letter-spacing:-.03em}}.shield{{display:grid;place-items:center;width:21px;height:21px;border:2px solid var(--navy);border-radius:7px;color:var(--navy);font:800 7px/1 Arial}}.head-meta{{text-align:right;color:var(--muted);font-size:7.3px;line-height:1.4}}.head-meta b{{display:block;color:var(--ink);font-size:8.6px}}
.hero{{margin:0 -10mm 5mm;padding:7mm 10mm;background:#f2f4f8;border-top:1px solid #e5e8ee;border-bottom:1px solid #e1e5ec}}.hero h1{{margin:1.8mm 0;color:var(--ink);font:700 25px/1.08 Georgia,"Times New Roman",serif;letter-spacing:-.035em}}.hero p{{margin:0;color:#626b7b;font-size:8.8px;line-height:1.45}}.kicker{{display:block;color:var(--navy);font-size:6.9px;font-weight:800;letter-spacing:.09em;text-transform:uppercase}}
h2,h3{{margin:0;color:var(--ink);font-family:Georgia,"Times New Roman",serif;letter-spacing:-.02em}}h2{{font-size:16px}}h3{{font-size:11px}}p{{font-size:8.2px;line-height:1.45}}
.summary-grid{{display:grid;grid-template-columns:1.08fr .92fr;gap:4mm}}.card{{border:1px solid var(--line);border-radius:3.5mm;background:#fff;padding:4.4mm}}.result-card{{background:#f7f8fb}}.facts-card{{background:#fff}}.rate{{margin:1.5mm 0 2mm;color:var(--navy);font-size:31px;font-weight:800;letter-spacing:-.045em}}.basis-row,.fact-row,.calc-row,.assumption-row{{display:flex;justify-content:space-between;gap:4mm;padding:2mm 0;border-top:1px solid var(--line);font-size:7.8px}}.basis-row span,.fact-row span,.calc-row span,.assumption-row span{{color:var(--muted)}}.basis-row b,.fact-row b,.calc-row b,.assumption-row b{{color:var(--ink);text-align:right}}.conclusion{{margin-top:3mm;padding-top:3mm;border-top:1px solid #cfd6e1;color:#303847;font-size:8px;line-height:1.45}}.path-note{{margin-top:3mm;padding:2.6mm 3mm;border-left:3px solid var(--navy);background:#f2f4f8;color:#3c4555;font-size:7.8px;line-height:1.4}}
.assumptions{{margin-top:4mm;padding:4mm;border:1px solid var(--line);border-radius:3.5mm;background:#fff}}.assumptions-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:5mm;margin-bottom:2mm}}.assumptions-head p{{margin:0;max-width:93mm;color:var(--muted);font-size:7.3px}}.assumption-note{{margin:1mm 0 0!important;font-style:italic}}.assumptions-grid{{display:grid;grid-template-columns:1fr 1fr;column-gap:7mm}}.assumption-row b{{font-weight:700;color:#4b5361}}
.calc-card{{margin-top:4mm;padding:4mm;border:1px solid var(--line);border-radius:3.5mm;background:#f7f8fb}}.calc-grid{{display:grid;grid-template-columns:1fr 1fr;column-gap:8mm}}.calc-row{{font-size:8.2px}}.calc-row.net b{{color:var(--navy)}}.fx{{margin-top:2mm;padding-top:2mm;border-top:1px solid var(--line);color:var(--muted);font-size:7px}}
.section-head{{margin:0 -10mm 5mm;padding:6mm 10mm;background:#f2f4f8;border-top:1px solid #e5e8ee;border-bottom:1px solid #e1e5ec}}.section-head h2{{margin:1.5mm 0}}.section-head p{{margin:0;color:#626b7b}}
.legal-source{{padding:4.5mm;border:1px solid var(--line);border-radius:3.5mm;background:#fff}}.instrument-name{{margin-top:1.2mm;color:#5e6879;font-size:7.4px;font-weight:700}}.legal-title-row{{display:flex;justify-content:space-between;gap:8mm;align-items:flex-start;margin:1.5mm 0 2mm}}.legal-title-row h2{{font-size:14px}}.official{{flex:0 0 auto;font-size:7px;white-space:nowrap}}.article-heading{{margin:2mm 0 .8mm;color:var(--navy);font-size:7.4px;font-weight:800}}.canonical-heading{{margin:0 0 1mm;color:var(--ink);font:700 10px/1.2 Georgia,"Times New Roman",serif}}.quote{{padding:3.5mm;border-left:3px solid var(--navy);background:#f7f8fb;color:#343b48;font-size:8.2px;line-height:1.5}}.quote strong{{color:var(--navy);font-weight:900}}.legal-note{{margin:2mm 0 0;color:var(--muted);font-size:7px}}
.lower-grid{{display:grid;grid-template-columns:.92fr 1.08fr;gap:4mm;margin-top:4mm}}.deadline-wrap,.support-wrap{{padding:4mm;border:1px solid var(--line);border-radius:3.5mm;background:#fff}}.deadline-card{{padding:2.8mm 0;border-top:1px solid var(--line)}}.deadline-card:first-of-type{{border-top:0}}.deadline-card span{{display:block;color:var(--muted);font-size:7px}}.deadline-card b{{display:block;margin-top:.8mm;color:var(--navy);font-size:10px}}.deadline-card p{{margin:1mm 0 0;color:#5e6675;font-size:6.9px}}.mini-card{{margin-top:2mm;padding-top:2mm;border-top:1px solid var(--line)}}.mini-card b{{font-size:8px;color:var(--ink)}}.mini-card ul{{margin:2mm 0 0;padding-left:4mm}}.mini-card li{{margin-bottom:1.4mm;font-size:7.2px;line-height:1.35}}.open-items{{border-top-color:#b8c2d5}}.related-sources{{margin-top:4mm;padding:3.5mm;border:1px solid var(--line);border-radius:3.5mm;background:#f7f8fb}}.related-source{{display:grid;grid-template-columns:25mm 1fr auto;gap:3mm;padding:1.8mm 0;border-top:1px solid var(--line);font-size:7px}}.related-source:first-of-type{{border-top:0}}.related-source span{{color:var(--muted)}}.hierarchy-note{{margin-top:4mm;padding:3mm;border-left:3px solid var(--navy);background:#f2f4f8;font-size:7.4px;line-height:1.4}}.disclaimer{{margin-top:4mm;padding-top:3mm;border-top:1px solid var(--line);color:#858c99;font-size:6.4px;line-height:1.4}}.footer{{position:absolute;left:10mm;right:10mm;bottom:6mm;display:flex;justify-content:space-between;color:#9aa1ad;font-size:6.3px}}.footer b{{color:#657087}}
@media print{{@page{{size:A4;margin:0}}html,body{{background:#fff}}.report{{margin:0}}.page{{break-after:page}}.page:last-child{{break-after:auto}}.sheet{{box-shadow:none}}}}
</style></head><body><article class="report">
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Informace k české srážkové dani</b>Vygenerováno {_date(report.get('generated_at'))}</div></header><div class="hero"><span class="kicker">Souhrn transakce</span><h1 aria-label="Informace k české srážkové dani">{escape(title)}</h1><p>Shrnutí transakce, použité sazby a výpočtu srážkové daně.</p></div><div class="summary-grid"><article class="card result-card"><span class="kicker">Sazba české srážkové daně</span><div class="rate">{escape(rate_display)}</div><div class="basis-row"><span>Vnitrostátní sazba</span><b>{domestic_rate}</b></div><div class="basis-row"><span>Smluvní sazba</span><b>{escape(treaty_rate)}</b></div><div class="basis-row"><span>Použitý právní základ</span><b>{escape(selected_ref)}</b></div><div class="conclusion">{escape(conclusion)}</div><div class="path-note">{escape(path_note)}</div>{foreign_marker}</article><article class="card facts-card"><h3>Údaje o transakci</h3><div class="fact-row"><span>Plátce</span><b>{escape(payer)}</b></div><div class="fact-row"><span>Příjemce</span><b>{escape(recipient)}</b></div><div class="fact-row"><span>Typ příjmu</span><b>{escape(_income(scope.get('income_type')))}</b></div><div class="fact-row"><span>Datum platby</span><b>{_date(scope.get('transaction_date'))}</b></div><div class="fact-row"><span>Hrubá částka</span><b>{amount_text}</b></div></article></div><section class="assumptions"><div class="assumptions-head"><div><h3>Použité předpoklady</h3><p class="assumption-note">Následující údaje byly zadány uživatelem a nebyly nezávisle ověřeny.</p></div><p>Výsledek vychází z jejich správnosti a úplnosti.</p></div><div class="assumptions-grid">{assumptions_html}</div></section><section class="calc-card"><span class="kicker">Výpočet</span><div class="calc-grid"><div class="calc-row"><span>Hrubá částka</span><b>{amount_text}</b></div><div class="calc-row"><span>Daňový základ</span><b>{calc_base}</b></div><div class="calc-row"><span>{"Česká daň k odvodu" if foreign_only else "Srážková daň"}</span><b>{calc_tax}</b></div><div class="calc-row"{' aria-label="Sazba Neuplatňuje se"' if foreign_only else ''}><span>Použitá sazba</span><b>{escape(rate_display)}</b></div><div class="calc-row net"><span>Čistá částka po srážce</span><b>{net_amount}</b></div></div>{f'<div class="fx">Přepočet měny · {fx_line}</div>' if fx_line else ''}</section>{compatibility}<div class="footer"><span>TaxTreat</span><b>01 / 02</b></div></div></section>
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>{escape(payer)} → {escape(recipient)}</b>{escape(_income(scope.get('income_type')))}</div></header><div class="section-head"><span class="kicker legal-basis-kicker">Právní základ</span><h2>Použité ustanovení a praktické kroky</h2><p>Právní pravidlo rozhodné pro zobrazenou sazbu a informace navazující na posuzovanou transakci.</p></div><article class="legal-source"><span class="kicker">Použité právní pravidlo</span><div class="instrument-name">{escape(treaty_name)}</div><div class="legal-title-row"><h2>{escape(selected_ref)}</h2><div class="official">{selected_link}</div></div><div class="article-heading">{article_locator}</div><div class="canonical-heading">{article_heading}</div><div class="quote">{selected_excerpt}</div><p class="legal-note">Zobrazen je pouze odstavec relevantní pro posuzovanou platbu; úplné znění je dostupné prostřednictvím odkazu na oficiální zdroj.</p></article><div class="lower-grid"><section class="deadline-wrap"><h3>Lhůty</h3>{deadlines_html or '<p>Pro tento výstup nejsou uvedeny navazující lhůty.</p>'}</section><section class="support-wrap"><h3>Podklady</h3><div class="mini-card"><b>Dokumentace vztahující se k této transakci</b><ul>{docs_html}</ul></div>{missing_block}</section></div>{f'<div class="related-sources"><h3>Další právní zdroje</h3>{related_html}</div>' if related_html else ''}<div class="hierarchy-note"><b>Vztah právních pravidel:</b> Česká vnitrostátní úprava stanoví výchozí režim. Je-li použitelná smlouva o zamezení dvojího zdanění a jsou splněny její podmínky, uplatní se smluvní omezení českého zdanění.</div><div class="disclaimer">{escape(disclaimer)}</div><div class="footer"><span>TaxTreat</span><b>02 / 02</b></div></div></section>
<template id="canonical-source-texts">{canonical_payload}</template></article></body></html>'''
