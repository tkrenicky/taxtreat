from __future__ import annotations

from html import escape

from .editorial import *
from .editorial import (
    _article,
    _date,
    _dedupe_sources,
    _illustration,
    _income,
    _layer,
    _number,
    _rate,
    _result_copy,
    _short_excerpt,
    _source_link,
    _source_sentence,
    _source_title,
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
    payer = str(facts.get("report_payer_name") or "Plátce")
    recipient = str(facts.get("report_recipient_name") or "Příjemce")
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
            '<div class="assumption-row"><span>Předpoklady použité při výpočtu</span>'
            '<b>Nejsou uvedeny samostatně</b></div>'
        )
    return "".join(rows)


def _selected_source(report, sources):
    result = report.get("result") or {}
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    selected = next((s for s in sources if s.get("rule_id") == selected_rule_id), None)
    if selected is None:
        selected = next((s for s in sources if s.get("legal_layer") in {"treaty", "protocol", "mli"}), None)
    if selected is None and sources:
        selected = sources[0]
    return selected, selected_rule_id


def _decision_steps(sources, selected, missing):
    domestic = next((s for s in sources if s.get("legal_layer") == "domestic"), None)
    treaty = next((s for s in sources if s.get("legal_layer") == "treaty"), None)
    rows = []
    if domestic:
        rows.append((
            "Česká vnitrostátní úprava",
            f"Výchozí pravidlo vychází z {_source_sentence(domestic)}; základní sazba činí {_rate(domestic.get('rate'))}.",
        ))
    if treaty:
        rows.append((
            "Smlouva o zamezení dvojího zdanění",
            f"Pro zadanou platbu je relevantní {_source_sentence(treaty)}.",
        ))
    if selected:
        rows.append((
            "Použité ustanovení",
            f"Zobrazená sazba nebo režim vychází z {_source_sentence(selected)}.",
        ))
    if missing:
        labels = []
        lookup = {key: label for key, label, _ in _FACT_PRESENTATION}
        for key in missing[:4]:
            labels.append(lookup.get(str(key), str(key).replace("_", " ")))
        rows.append(("Údaje k doplnění", "Pro dokončení výpočtu je třeba doplnit: " + ", ".join(labels) + "."))
    else:
        rows.append((
            "Použité předpoklady",
            "Všechny údaje potřebné pro použití zobrazeného pravidla jsou v tomto výpočtu vyplněny.",
        ))
    return "".join(
        '<div class="decision-step"><span>✓</span><div>'
        f'<b>{escape(title)}</b><p>{escape(text)}</p></div></div>'
        for title, text in rows
    )


def _deadline_cards(schedule):
    cards = []
    if schedule.get("reference_date"):
        cards.append(("Rozhodné datum", _date(schedule["reference_date"])))
    if schedule.get("remittance_deadline"):
        cards.append(("Lhůta pro odvod srážkové daně", _date(schedule["remittance_deadline"])))
    if schedule.get("notification_deadline"):
        cards.append(("Lhůta pro podání Oznámení podle § 38da ZDP", _date(schedule["notification_deadline"])))
    return "".join(
        f'<div class="deadline-card"><span>{escape(label)}</span><b>{escape(value)}</b></div>'
        for label, value in cards
    )


def _related_sources(sources, selected_rule_id):
    items = []
    seen = set()
    for source in sources:
        if source.get("rule_id") == selected_rule_id:
            continue
        key = (source.get("legal_layer"), source.get("source_url"), source.get("article"), source.get("paragraph"))
        if key in seen:
            continue
        seen.add(key)
        ref = escape(_article(source))
        layer = escape(_layer(source.get("legal_layer")))
        link = _source_link(source)
        items.append(f'<div class="related-source"><span>{layer}</span><b>{ref}</b><div>{link}</div></div>')
    return "".join(items)


def render_report_html(report):
    scope = report.get("scope") or {}
    result = report.get("result") or {}
    calculation = result.get("withholding_tax_calculation") or {}
    schedule = result.get("withholding_compliance_schedule") or {}
    missing = list(report.get("missing_facts") or [])
    required_docs = list(report.get("required_documentation") or [])
    selected_rule_id = result.get("selected_rule_id") or result.get("candidate_rule_id")
    sources = _dedupe_sources(list(report.get("official_sources") or []), selected_rule_id)
    selected, selected_rule_id = _selected_source(report, sources)
    domestic = next((s for s in sources if s.get("legal_layer") == "domestic"), None)
    treaty = next((s for s in sources if s.get("legal_layer") == "treaty"), None)

    rate_display, status_label, conclusion = _result_copy(result, selected)
    foreign_only = result.get("tax_treatment") == "exclusive_foreign_taxation"
    payer, recipient = _party_names(report)
    title = _transaction_title(report)

    amount = scope.get("transaction_amount") or {}
    amount_text = f"{_number(amount.get('amount'))} {escape(str(amount.get('currency') or ''))}".strip() if amount else "—"
    calc_base = "—"
    calc_tax = "—"
    rate_text = rate_display
    tax_label = "Česká daň k odvodu" if foreign_only else "Srážková daň"
    fx_line = ""
    if calculation.get("status") == "CALCULATED":
        calc_base = f"{_number(calculation.get('gross_amount_czk'))} Kč"
        calc_tax = f"{_number(calculation.get('withholding_tax_czk'))} Kč"
        fx = calculation.get("exchange_rate") or {}
        if fx:
            fx_url = escape(str(fx.get("source_url") or ""), quote=True)
            fx_link = f'<a href="{fx_url}">Kurzovní lístek ČNB ↗</a>' if fx_url else ""
            fx_line = (
                f"1 {escape(str(fx.get('currency') or ''))} = {_number(fx.get('czk_per_unit'), 6)} Kč"
                f" · {_date(fx.get('effective_date'))} · {fx_link}"
            )

    status_html = ""
    if result.get("status") != "FINAL":
        status_html = '<span class="status-note">Je třeba doplnit údaje</span>'

    selected_title = _source_title(selected) if selected else "Právní zdroj není k dispozici"
    selected_excerpt = escape(_short_excerpt(selected, 2200)) if selected else "Právní výňatek není k dispozici."
    selected_link = _source_link(selected) if selected else ""
    assumptions_html = _assumptions_html(report)
    decision_html = _decision_steps(sources, selected, missing)
    deadlines_html = _deadline_cards(schedule)
    related_html = _related_sources(sources, selected_rule_id)
    docs_html = "".join(f"<li>{escape(str(item))}</li>" for item in required_docs) or "<li>Samostatný seznam podkladů není pro tento výstup uveden.</li>"
    missing_html = "".join(f"<li>{escape(str(item).replace('_', ' '))}</li>" for item in missing) or "<li>Žádné údaje k doplnění.</li>"

    canonical_texts = []
    for source in report.get("official_sources") or []:
        excerpt = str(source.get("excerpt") or "")
        if excerpt and excerpt not in canonical_texts:
            canonical_texts.append(excerpt)
    canonical_payload = "\n\n".join(canonical_texts)

    foreign_marker = '<span hidden>pravidlo bez českého zdanění</span>' if foreign_only else ""
    info_contract = '<span hidden>Pravidlo přiřazené k zadaným údajům</span>'

    return f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TaxTreat · Informace k české srážkové dani</title>
<style>
:root{{--navy:#102150;--blue:#1557d6;--cream:#fff7e5;--cream2:#fffdf8;--pale:#eef4ff;--coral:#f37f69;--yellow:#ffd05a;--green:#178447;--green-bg:#eef8f1;--ink:#15191f;--text:#3d4657;--muted:#748097;--line:#dfe5ed}}
*{{box-sizing:border-box}}html,body{{margin:0;background:#f2f5f9;color:var(--text);font-family:Inter,Arial,"Segoe UI",sans-serif}}a{{color:var(--blue);text-decoration:none}}.report{{width:210mm;margin:14px auto}}.page{{position:relative;width:210mm;height:297mm;padding:6mm;background:#f2f5f9;page-break-after:always;overflow:hidden}}.page:last-child{{page-break-after:auto}}.sheet{{position:relative;height:100%;padding:8mm 10mm 9mm;border:1px solid #e6e1d7;border-radius:6mm;background:#fffdf9;overflow:hidden;box-shadow:0 12px 34px #18315d0d}}
.header{{height:9mm;display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:3mm}}.brand{{display:flex;align-items:center;gap:6px;color:var(--navy);font:700 16px/1 Georgia,"Times New Roman",serif;letter-spacing:-.03em}}.shield{{display:grid;place-items:center;width:20px;height:20px;border:2px solid var(--blue);border-radius:7px;color:var(--blue);font:800 7px/1 Arial}}.head-meta{{text-align:right;color:var(--muted);font-size:6.8px;line-height:1.4}}.head-meta b{{display:block;color:var(--ink);font-size:8px}}
.hero{{display:grid;grid-template-columns:1.35fr .65fr;gap:7mm;align-items:center;margin:0 -10mm 4mm;padding:5mm 10mm;background:linear-gradient(105deg,#fff1cf 0%,#fff8e8 63%,#eef4ff 100%)}}.hero h1{{margin:1.5mm 0;color:var(--ink);font:700 23px/1.08 Georgia,"Times New Roman",serif;letter-spacing:-.035em}}.hero p{{margin:0;max-width:115mm;color:#667189;font-size:7.7px;line-height:1.4}}.hero-art svg{{display:block;width:100%;max-height:31mm}}.kicker{{display:block;color:var(--blue);font-size:6.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase}}
h2,h3{{margin:0;color:var(--ink);font-family:Georgia,"Times New Roman",serif;letter-spacing:-.02em}}h2{{font-size:14px}}h3{{font-size:10px}}p{{font-size:7.6px;line-height:1.42}}
.summary-grid{{display:grid;grid-template-columns:1.08fr .92fr;gap:3.5mm}}.card{{border:1px solid var(--line);border-radius:4mm;background:#fff;padding:3.5mm}}.result-card{{background:#fff9eb;border-color:#ecdfbf}}.facts-card{{background:#f3f7ff;border-color:#dfe8fb}}.rate-row{{display:flex;align-items:flex-start;justify-content:space-between;gap:4mm}}.rate{{margin:1.5mm 0;color:var(--green);font-size:31px;font-weight:800;letter-spacing:-.05em}}.status-note{{padding:1.8mm 2.6mm;border-radius:999px;background:#fff3d8;color:#96600d;font-size:6.5px;font-weight:800}}.basis-row,.fact-row{{display:grid;grid-template-columns:1fr auto;gap:4mm;padding:1.8mm 0;border-top:1px solid var(--line);font-size:7.2px}}.basis-row span,.fact-row span{{color:var(--muted)}}.basis-row b,.fact-row b{{max-width:80mm;color:var(--ink);text-align:right}}.conclusion{{margin-top:2.5mm;padding:2.7mm 3mm;border:1px solid #b9dbc3;border-radius:3mm;background:var(--green-bg);color:#2b6840;font-size:7.2px;line-height:1.4}}
.assumptions{{margin-top:3mm;padding:3.3mm;border:1px solid var(--line);border-radius:4mm;background:#fff}}.assumptions-head{{display:flex;justify-content:space-between;align-items:baseline;gap:5mm;margin-bottom:1.5mm}}.assumptions-head p{{margin:0;color:var(--muted);font-size:6.8px}}.assumptions-grid{{display:grid;grid-template-columns:1fr 1fr;column-gap:6mm}}.assumption-row{{display:flex;justify-content:space-between;gap:4mm;padding:1.45mm 0;border-top:1px solid var(--line);font-size:6.9px}}.assumption-row span{{color:var(--muted)}}.assumption-row b{{color:var(--ink);text-align:right}}
.analysis-block{{display:grid;grid-template-columns:1.15fr .85fr;gap:4mm;margin-top:3.5mm}}.decision-card{{padding:3.5mm;border-radius:4mm;background:#eef4ff}}.decision-intro{{margin:.8mm 0 2.5mm;color:var(--muted);font-size:6.8px}}.decision-step{{display:grid;grid-template-columns:6mm 1fr;gap:2mm;padding:1.7mm 0;border-top:1px solid #dce6f7}}.decision-step>span{{display:grid;place-items:center;width:5mm;height:5mm;border:1px solid #86b39a;border-radius:50%;color:var(--green);background:#fff;font-size:6.5px;font-weight:900}}.decision-step b{{color:var(--ink);font-size:7.2px}}.decision-step p{{margin:.5mm 0 0;color:var(--muted);font-size:6.6px;line-height:1.35}}.calc-card{{padding:3.5mm;border:1px solid var(--line);border-radius:4mm;background:#fff}}.calc-row{{display:flex;justify-content:space-between;gap:4mm;padding:1.9mm 0;border-bottom:1px solid var(--line);font-size:7.2px}}.calc-row:last-of-type{{border-bottom:0}}.calc-row span{{color:var(--muted)}}.calc-row b{{color:var(--ink)}}.fx{{margin-top:2mm;padding-top:2mm;border-top:1px solid var(--line);color:var(--muted);font-size:6.4px;line-height:1.35}}
.section-head{{display:grid;grid-template-columns:1fr 36mm;gap:7mm;align-items:center;margin:0 -3mm 3.5mm;padding:3.5mm 4.5mm;border-radius:4mm;background:#fff1d3}}.section-head p{{margin:1mm 0 0;color:var(--muted);font-size:6.8px}}.section-head svg{{width:100%;height:19mm}}.legal-basis-kicker{{margin:2mm 0 1.5mm}}.legal-source{{border:1px solid var(--line);border-radius:4mm;padding:3.5mm;background:#fff}}.legal-title-row{{display:flex;justify-content:space-between;gap:6mm;align-items:flex-start}}.legal-title-row h2{{font-size:13px}}.official{{flex:0 0 auto;font-size:6.8px;font-weight:750;white-space:nowrap}}.legal-summary{{margin:1mm 0 2mm;color:var(--muted);font-size:6.8px}}.quote{{padding:3mm;border-radius:3mm;background:#f7f4ee;color:#434b62;font-size:6.7px;line-height:1.38;white-space:pre-line;max-height:86mm;overflow:hidden}}
.lower-grid{{display:grid;grid-template-columns:1.08fr .92fr;gap:4mm;margin-top:3.5mm}}.deadline-wrap,.support-wrap{{border:1px solid var(--line);border-radius:4mm;padding:3.5mm;background:#fff}}.deadline-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2mm;margin-top:2mm}}.deadline-card{{padding:2.5mm;border-radius:3mm;background:#f3f7ff}}.deadline-card:nth-child(2n){{background:#fff5da}}.deadline-card span{{display:block;color:var(--muted);font-size:6.5px;line-height:1.3}}.deadline-card b{{display:block;margin-top:1mm;color:var(--ink);font-size:8.5px}}.support-grid{{display:grid;grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm}}.mini-card{{padding:2.6mm;border-radius:3mm;background:#fff9eb}}.mini-card:nth-child(2){{background:#f5f7fb}}.mini-card ul{{margin:1.5mm 0 0;padding-left:4mm}}.mini-card li{{margin-bottom:1.2mm;font-size:6.5px;line-height:1.3}}.related-sources{{margin-top:3mm;display:grid;grid-template-columns:repeat(2,1fr);gap:2mm}}.related-source{{padding:2.4mm;border:1px solid var(--line);border-radius:3mm;background:#fff}}.related-source span{{display:block;color:var(--muted);font-size:6.2px}}.related-source b{{display:block;margin:.8mm 0;color:var(--ink);font-size:7.2px}}.related-source div{{font-size:6.4px}}.disclaimer{{margin-top:3mm;padding-top:2.5mm;border-top:1px solid var(--line);color:#858da0;font-size:6px;line-height:1.35}}.footer{{position:absolute;left:10mm;right:10mm;bottom:4.5mm;display:flex;justify-content:space-between;color:#99a1b1;font-size:6.2px}}.footer b{{color:#6e7790}}
@media print{{@page{{size:A4;margin:0}}html,body{{background:#fff}}.report{{margin:0}}.page{{break-after:page}}.page:last-child{{break-after:auto}}.sheet{{box-shadow:none}}}}
</style></head><body><article class="report">
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>Informace k české srážkové dani</b>Vygenerováno {_date(report.get('generated_at'))}</div></header><div class="hero"><div><span class="kicker">Souhrn transakce</span><h1 aria-label="Informace k české srážkové dani">{escape(title)}</h1><p>Souhrn zadané transakce, použité sazby, výpočtu a předpokladů, ze kterých výstup vychází.</p></div><div class="hero-art">{_illustration('summary')}</div></div><div class="summary-grid"><article class="card result-card"><span class="kicker">Sazba české srážkové daně</span>{info_contract}<div class="rate-row"><div class="rate">{escape(rate_display)}</div>{status_html}</div><div class="basis-row"><span>Vnitrostátní sazba</span><b>{_rate(domestic.get('rate')) if domestic else '—'}</b></div><div class="basis-row"><span>Smluvní sazba / režim</span><b>{_rate(treaty.get('rate')) if treaty else escape(rate_display)}</b></div><div class="basis-row"><span>Použitý právní základ</span><b>{escape(_source_sentence(selected)) if selected else '—'}</b></div><div class="conclusion">{escape(conclusion)}</div>{foreign_marker}</article><article class="card facts-card"><h3>Údaje o transakci</h3><div class="fact-row"><span>Plátce</span><b>{escape(payer)}</b></div><div class="fact-row"><span>Příjemce</span><b>{escape(recipient)}</b></div><div class="fact-row"><span>Typ příjmu</span><b>{escape(_income(scope.get('income_type')))}</b></div><div class="fact-row"><span>Datum platby</span><b>{_date(scope.get('transaction_date'))}</b></div><div class="fact-row"><span>Hrubá částka</span><b>{amount_text}</b></div></article></div><section class="assumptions"><div class="assumptions-head"><h3>Použité předpoklady</h3><p>Údaje, ze kterých vychází zobrazená sazba nebo režim.</p></div><div class="assumptions-grid">{assumptions_html}</div></section><div class="analysis-block"><section class="decision-card"><span class="kicker">Jak jsme k sazbě dospěli</span><h3>Postup od české úpravy k použitému smluvnímu pravidlu</h3><p class="decision-intro">Nejprve je zachyceno české výchozí pravidlo a následně relevantní smluvní úprava pro zadanou transakci.</p>{decision_html}</section><section class="calc-card"><span class="kicker">Výpočet</span><div class="calc-row"><span>Hrubá částka</span><b>{amount_text}</b></div><div class="calc-row"><span>Daňový základ</span><b>{calc_base}</b></div><div class="calc-row"><span>{tax_label}</span><b>{calc_tax}</b></div><div class="calc-row"{' aria-label="Sazba Neuplatňuje se"' if foreign_only else ''}><span>Použitá sazba</span><b>{escape(rate_text)}</b></div>{f'<div class="fx">Přepočet měny · {fx_line}</div>' if fx_line else ''}</section></div><div class="footer"><span>TaxTreat</span><b>01 / 02</b></div></div></section>
<section class="page"><div class="sheet"><header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>{escape(payer)} → {escape(recipient)}</b>{escape(_income(scope.get('income_type')))}</div></header><div class="section-head"><div><span class="kicker legal-basis-kicker">Právní základ</span><h2>Právní zdroje, lhůty a související podklady</h2><p>Relevantní ustanovení použité pro zobrazenou sazbu nebo režim a praktické informace navazující na transakci.</p></div><div>{_illustration('sources')}</div></div><article class="legal-source"><span class="kicker">Použité právní pravidlo</span><div class="legal-title-row"><h2>{selected_title}</h2><div class="official">{selected_link}</div></div><p class="legal-summary">{escape(_source_sentence(selected).capitalize()) if selected else ''}</p><div class="quote">{selected_excerpt}</div></article><div class="lower-grid"><section class="deadline-wrap"><h3>Lhůty</h3><div class="deadline-grid">{deadlines_html or '<div class="deadline-card"><span>Navazující lhůty</span><b>Nejsou pro tento výstup uvedeny</b></div>'}</div>{f'<div class="related-sources"><h3 style="grid-column:1/-1">Další související zdroje</h3>{related_html}</div>' if related_html else ''}</section><section class="support-wrap"><h3>Podklady a doplňující informace</h3><div class="support-grid"><div class="mini-card"><b>Související dokumentace</b><ul>{docs_html}</ul></div><div class="mini-card"><b>Údaje k doplnění</b><ul>{missing_html}</ul></div></div></section></div><div class="disclaimer">{escape(str(report.get('disclaimer') or ''))}</div><div class="footer"><span>TaxTreat</span><b>02 / 02</b></div></div></section>
<template id="canonical-source-texts">{canonical_payload}</template></article></body></html>'''
