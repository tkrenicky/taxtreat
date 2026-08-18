from __future__ import annotations

import re
from html import escape

from .client_report import render_report_html as _render_client_report_html


_FULL_DISCLAIMER = (
    "TaxTreat je informační nástroj. Automatizovaně zobrazuje informace odvozené "
    "z uvedených právních zdrojů a z údajů zadaných uživatelem. Neprovádí individuální "
    "právní ani daňové posouzení, neposkytuje doporučení ani právní či daňové poradenství "
    "a neurčuje, jak má uživatel v konkrétním případě postupovat. Uživatel odpovídá za "
    "správnost vstupních údajů a za vlastní posouzení použitelnosti zobrazených informací."
)


# Final client-facing visual specification supplied after the fourth design review.
# The dynamic report structure and tax/legal logic remain in client_report.py; this
# layer freezes the approved editorial styling and copy without touching decisions.
_FINAL_CSS = r"""
/* TaxTreat final client report — approved release design. */
:root{
  --page-bg:#EFEDE4;
  --paper:#FBFAF6;
  --card:#F4F5F8;
  --card-border:#E1E0D8;
  --navy:#1B2A4A;
  --navy-soft:rgba(27,42,74,0.62);
  --accent-fill:#E4EAF6;
  --accent-line:#C9D3E8;
  --body:#33394A;
  --label:#6B7280;
  --serif:Georgia,"Iowan Old Style","Palatino Linotype",serif;
  --sans:-apple-system,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
}
html,body{background:var(--page-bg);color:var(--body);font-family:var(--sans)}
.report{width:210mm;margin:14px auto}
.page{width:210mm;height:297mm;padding:6mm;background:var(--page-bg)}
.sheet{height:100%;padding:11mm 12mm 9mm;background:var(--paper);border:0;border-radius:4.5mm;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow:hidden}
a{color:var(--navy);text-decoration:none;border-bottom:0;font-weight:600}
.header{height:auto;min-height:10mm;margin:0 0 5mm;padding-bottom:4.5mm;border-bottom:1px solid var(--card-border);align-items:flex-start}
.brand{gap:2.5mm;color:var(--navy);font:700 19px/1 var(--serif);letter-spacing:0}
.shield{width:6.8mm;height:6.8mm;border:1.6px solid var(--navy);border-radius:1.8mm;color:var(--navy);font:700 8px/1 var(--sans)}
.head-meta{color:var(--label);font-size:8px;line-height:1.4}
.head-meta b{color:var(--navy);font-size:8.4px;font-weight:600}
.hero{margin:0;padding:5.5mm 0 5mm;background:transparent;border:0}
.hero .kicker,.section-head .kicker{margin-bottom:2mm;color:var(--navy-soft);font-size:7.1px;letter-spacing:.09em}
.hero h1{margin:0 0 2mm;color:var(--navy);font:600 27px/1.28 var(--serif);letter-spacing:0}
.hero p{max-width:145mm;margin:0;color:var(--label);font-size:8px;line-height:1.4}
.kicker{color:var(--navy-soft);font-size:6.6px;font-weight:700;letter-spacing:.08em}
h2,h3{color:var(--navy);font-family:var(--serif);letter-spacing:0}
h2{font-size:16px;font-weight:600}h3{font-size:11px;font-weight:600}

.key-facts{display:flex;gap:0;margin:0 0 5mm;border:1px solid var(--card-border);border-radius:3mm;background:transparent;overflow:hidden}
.key-fact{flex:1;padding:3.2mm 4mm;border-left:1px solid var(--card-border);background:transparent;white-space:nowrap}
.key-fact:first-child{border-left:0}
.key-fact span{color:var(--label);font-size:6.9px;text-transform:uppercase;letter-spacing:.04em}
.key-fact b{margin-top:.8mm;color:var(--navy);font-size:8.8px;font-weight:700}

.summary-grid{display:flex;gap:4.5mm;margin-bottom:4.5mm;align-items:stretch}
.summary-grid .result-card{flex:1.15}.summary-grid .facts-card{flex:1}
.card{padding:5mm;border:1px solid var(--card-border);border-radius:3mm;background:var(--card)}
.result-card{background:var(--accent-fill);border-color:var(--accent-line)}
.rate{margin:.7mm 0 3.6mm;color:var(--navy);font:700 34px/1.05 var(--serif);letter-spacing:0}
.basis-row,.fact-row,.calc-row,.assumption-row{padding:2mm 0;border-top:1px solid rgba(27,42,74,.10);font-size:8.1px}
.basis-row:first-of-type,.fact-row:first-of-type{border-top:0}
.basis-row span,.fact-row span,.calc-row span,.assumption-row span{color:var(--label)}
.basis-row b,.fact-row b,.calc-row b,.assumption-row b{color:var(--navy);font-weight:700;max-width:62%}
.conclusion{margin-top:3mm;padding-top:0;border-top:0;color:var(--body);font-size:8px;line-height:1.5}
.path-note{margin-top:3mm;padding:2.6mm 3.5mm;border-left:3px solid var(--navy);border-radius:0 2mm 2mm 0;background:rgba(255,255,255,.55);color:var(--navy);font-size:7.5px;line-height:1.45}
.facts-card h3{margin:0 0 2.5mm;color:var(--navy);font:600 15px/1.2 var(--serif)}

.assumptions{margin:0 0 4.5mm;padding:5mm;border:1px solid var(--card-border);border-radius:3mm;background:var(--card)}
.assumptions-head{margin-bottom:2.5mm}
.assumptions-head h3{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--navy-soft);font-family:var(--sans);font-weight:700}
.assumption-note{margin:1.6mm 0 0!important;color:var(--label);font-size:7.3px;font-style:italic;line-height:1.5}
.assumptions-grid{display:flex;flex-wrap:wrap;justify-content:space-between;column-gap:0}
.assumption-row{width:47%;font-size:7.7px}
.assumption-row:nth-child(-n+2){border-top:0}
.assumption-row b{color:var(--navy)}

.calc-card{margin:0 0 4.5mm;padding:5mm;border:1px solid var(--card-border);border-radius:3mm;background:var(--card)}
.calc-card>.kicker{margin-bottom:2mm}
.calc-grid{display:flex;flex-wrap:wrap;justify-content:space-between;column-gap:0}
.calc-row{width:47%;font-size:8.1px}
.calc-row:nth-child(-n+2){border-top:0}
.calc-row.net b{color:var(--navy);font-size:8.8px}
.fx{margin-top:2mm;padding-top:2mm;border-top:1px solid var(--card-border);color:var(--label);font-size:7.1px}

.flow-wrap{margin:0;padding:4.5mm 5.5mm 4mm;border:1px solid var(--card-border);border-radius:3mm;background:var(--card)}
.flow-head{display:flex;justify-content:space-between;align-items:baseline;gap:8mm;margin-bottom:4mm}
.flow-head h3{margin-top:.6mm;color:var(--navy);font:600 15px/1.2 var(--serif)}
.flow-head p{margin:0;color:var(--label);font-size:7.1px}
.flow{position:relative;display:flex;justify-content:space-between;gap:0;padding-top:3.5mm;break-inside:avoid;page-break-inside:avoid}
.flow::before{content:"";position:absolute;top:3.5mm;left:6mm;right:6mm;height:1.5px;border:0;background:var(--accent-line);z-index:0}
.flow-node{position:relative;z-index:1;flex:1;min-width:0;padding:0 2mm;border:0;border-radius:0;background:transparent;text-align:center}
.flow-node span{display:flex;align-items:center;justify-content:center;width:7mm;height:7mm;margin:-3.5mm auto 2.5mm;border:2px solid var(--navy);border-radius:50%;background:var(--paper);color:var(--navy);font:700 7px/1 var(--sans);letter-spacing:0}
.flow-node b{display:block;margin:0 0 1mm;color:var(--navy);font-size:7px;font-weight:700}
.flow-node p{margin:0;color:var(--label);font-size:6.9px;line-height:1.38}
.flow-node:last-child{margin-top:-2.5mm;padding:2.5mm 2mm 3mm;border-radius:2.5mm;background:var(--accent-fill)}
.flow-node:last-child span{margin-top:-3.5mm;background:var(--navy);color:#fff}
.flow-arrow,.flow-principle{display:none!important}

.section-head{margin:0;padding:5.5mm 0 5mm;background:transparent;border:0}
.section-head h2{margin:0 0 2mm;color:var(--navy);font:600 23px/1.25 var(--serif)}
.section-head p{margin:0;color:var(--label);font-size:8px}
.legal-source{padding:5mm;border:1px solid var(--card-border);border-radius:3mm;background:var(--card)}
.legal-title-row{display:flex;justify-content:space-between;gap:7mm;align-items:flex-start;margin:.8mm 0 3mm}
.legal-title-row h2{max-width:145mm;color:var(--navy);font:600 16px/1.35 var(--serif)}
.official{flex:0 0 auto;font-size:7px;white-space:nowrap}
.quote{padding:3.6mm 4mm;border-left:3px solid var(--navy);border-radius:0 2mm 2mm 0;background:var(--accent-fill);color:var(--body);font-size:7.7px;line-height:1.65}
.quote strong{color:var(--navy);font-weight:700}
.transaction-gloss{margin-top:3mm;padding:2.6mm 3.5mm;border-radius:2mm;background:rgba(27,42,74,.05);color:var(--body);font-size:7.2px;line-height:1.5}
.transaction-gloss b{color:var(--navy)}
.legal-note{margin:2mm 0 0;color:var(--label);font-size:7px}

.page:nth-of-type(2) .sheet{display:flex;flex-direction:column}
.page:nth-of-type(2) .section-head{flex:0 0 auto}
.page:nth-of-type(2) .legal-source{flex:0 0 auto}
.lower-grid{display:flex;gap:4.5mm;margin:5.5mm 0 0}
.deadline-wrap,.support-wrap{flex:1;padding:5mm;border:1px solid var(--card-border);border-radius:3mm;background:var(--card)}
.deadline-wrap h3,.support-wrap h3{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--navy-soft);font-family:var(--sans);font-weight:700}
.deadline-card{padding:3mm 0;border-top:1px solid var(--card-border)}
.deadline-card:first-of-type{border-top:0;padding-top:1.5mm}
.deadline-card span{color:var(--navy);font-size:7.5px;font-weight:700}
.deadline-card b{margin-top:.7mm;color:var(--navy);font:700 17px/1.2 var(--serif)}
.deadline-card p{margin:1mm 0 0;color:var(--label);font-size:6.9px;line-height:1.5}
.mini-card{margin-top:1.6mm;padding-top:1.6mm;border-top:0}
.mini-card b{color:var(--navy);font-size:7.5px}
.mini-card ul{margin:2.4mm 0 0;padding-left:4mm}
.mini-card li{margin-bottom:1.5mm;color:var(--body);font-size:7.2px;line-height:1.55}
.related-sources{margin-top:5.5mm;padding:4.5mm 5mm;border:1px solid var(--card-border);border-radius:3mm;background:var(--card)}
.related-sources h3{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--navy-soft);font-family:var(--sans);font-weight:700}
.related-source{display:flex;align-items:baseline;justify-content:space-between;gap:4mm;padding:2mm 0;border-top:1px solid var(--card-border);font-size:7.2px}
.related-source:first-of-type{margin-top:1.5mm;border-top:0}
.related-source span{color:var(--label);font-size:6.6px;text-transform:uppercase;letter-spacing:.04em}
.related-source b{flex:1;color:var(--navy);font-weight:700}
.hierarchy-note{margin-top:5.5mm;padding:4mm 5mm;border-left:3px solid var(--navy);border-radius:0 2mm 2mm 0;background:var(--accent-fill);color:var(--body);font-size:7.2px;line-height:1.6}
.hierarchy-note b{margin-bottom:1.3mm;color:var(--navy);font:600 13.5px/1.2 var(--serif)}
.disclaimer{margin-top:6.5mm;padding-top:3.5mm;border-top:1px solid var(--card-border);color:var(--label);font-size:6.5px;line-height:1.5}
.footer{left:12mm;right:12mm;bottom:7mm;color:var(--label);font-size:6.8px}
.footer b{color:var(--label)}

@media print{
  @page{size:A4;margin:0}
  html,body{background:#fff}
  .report{margin:0}
  .page{padding:0;background:#fff}
  .sheet{border-radius:0;box-shadow:none}
}
"""


def _replace_disclaimer(html: str) -> str:
    replacement = f'<div class="disclaimer">{escape(_FULL_DISCLAIMER)}</div>'
    return re.sub(
        r'<div class="disclaimer">.*?</div>',
        replacement,
        html,
        count=1,
        flags=re.DOTALL,
    )


def _apply_final_copy(html: str) -> str:
    replacements = {
        "Lhůta pro odvod daně plátcem.": (
            "Plátce je povinen sraženou daň odvést správci daně nejpozději do tohoto data."
        ),
        "Pro použitou sazbu byly zohledněny zejména tyto zadané údaje:": (
            "Použitá sazba vychází z těchto zadaných údajů:"
        ),
        "Nejbližší uvedená lhůta": "Nejbližší lhůta",
        "Vzniká česká srážková daň a jaký je výchozí režim?": (
            "Vzniká česká srážková daň? Jaký je její výchozí režim?"
        ),
        "Je-li relevantní, zohlední se modifikace smlouvy a anti-abuse test.": (
            "Je-li relevantní, zohlední se modifikace smlouvy a test hlavního účelu."
        ),
        "Je-li relevantní, zohlední se modifikace smlouvy mnohostranným nástrojem (MLI) a test hlavního účelu (PPT).": (
            "Je-li relevantní, zohlední se modifikace smlouvy a test hlavního účelu."
        ),
    }
    for current, revised in replacements.items():
        html = html.replace(current, revised)

    # The final design avoids repeating the role name inside a missing-name value.
    html = re.sub(
        r'(<span>Plátce</span><b>)Plátce – název neuveden(</b>)',
        r'\1Název neuveden\2',
        html,
        count=1,
    )
    html = re.sub(
        r'(<span>Příjemce</span><b>)Příjemce – název neuveden(</b>)',
        r'\1Název neuveden\2',
        html,
        count=1,
    )
    html = html.replace(
        "Výplata dividend: Plátce – název neuveden → Příjemce – název neuveden",
        "Výplata dividend: Plátce (název neuveden) → Příjemce (název neuveden)",
    )
    html = html.replace(
        "Úroková platba: Plátce – název neuveden → Příjemce – název neuveden",
        "Úroková platba: Plátce (název neuveden) → Příjemce (název neuveden)",
    )
    html = html.replace(
        "Licenční platba: Plátce – název neuveden → Příjemce – název neuveden",
        "Licenční platba: Plátce (název neuveden) → Příjemce (název neuveden)",
    )
    return html


def _remove_duplicate_principle(html: str) -> str:
    return re.sub(
        r'<div class="flow-principle">.*?</div>',
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )


def render_report_html(report):
    """Render the frozen final client report without altering tax/legal decisions."""
    html = _render_client_report_html(report)
    html = _apply_final_copy(html)
    html = _remove_duplicate_principle(html)
    html = _replace_disclaimer(html)
    return html.replace("</style>", _FINAL_CSS + "\n</style>", 1)
