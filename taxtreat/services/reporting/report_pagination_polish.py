from __future__ import annotations

import re
from html import escape
from typing import Any


def _is_domestic_exemption(report: dict[str, Any]) -> bool:
    scope = report.get("scope") or {}
    result = report.get("result") or {}
    return (
        str(scope.get("source_country") or "CZ").upper() == "CZ"
        and str(scope.get("income_type") or "") == "dividend"
        and str(result.get("tax_treatment") or "") == "domestic_exemption"
    )


def _facts(report: dict[str, Any]) -> dict[str, Any]:
    return ((report.get("assumptions") or {}).get("transaction_facts") or {})


def _english(report: dict[str, Any]) -> bool:
    return str(_facts(report).get("__report_language") or "cs").lower() == "en"


def _party_names(report: dict[str, Any]) -> tuple[str, str]:
    facts = _facts(report)
    return (
        str(facts.get("report_payer_name") or "Payer"),
        str(facts.get("report_recipient_name") or "Recipient"),
    )


def apply_report_pagination_polish(html: str, report: dict[str, Any]) -> str:
    if not html or not _is_domestic_exemption(report):
        return html

    english = _english(report)
    payer, recipient = _party_names(report)

    # Compact the flow result because the result is a legal regime, not a numeric rate.
    css = r'''
<style id="tt-three-page-print-polish">
@page{size:A4;margin:0}
@media print{
  html,body{margin:0!important;padding:0!important;background:#fff!important}
  .report{width:210mm!important;margin:0!important}
  .page{width:210mm!important;min-height:297mm!important;padding:0!important;break-after:page!important;page-break-after:always!important;background:#fff!important}
  .page:last-of-type{break-after:auto!important;page-break-after:auto!important}
  .sheet{box-sizing:border-box!important;min-height:297mm!important;padding:10mm 12mm 8mm!important;box-shadow:none!important;border-radius:0!important}
  .summary-grid,.assumptions,.calc-card,.flow-wrap,.legal-source,.lower-grid,.related-sources,.hierarchy-note{break-inside:avoid!important;page-break-inside:avoid!important}
}
.flow-node:last-child p{font-size:9px!important;line-height:1.25!important;font-family:var(--sans)!important}
.flow-wrap{padding:4.4mm 5mm 4mm!important}
.flow-head{margin-bottom:3.2mm!important}
.flow-node{padding:2.4mm 2.2mm!important}
.rate.tt-exemption-result{font-size:28px!important;line-height:1.02!important;margin-bottom:3mm!important}
.tt-section19-primary,.tt-treaty-secondary{break-inside:avoid!important;page-break-inside:avoid!important}
.tt-section19-primary .quote,.tt-treaty-secondary .quote{font-size:8px!important;line-height:1.48!important}
.tt-page3-title{margin:0;padding:5.5mm 0 5mm}
.tt-page3-title h2{margin:0 0 2mm;color:var(--navy);font:600 23px/1.25 var(--serif)}
.tt-page3-title p{margin:0;color:var(--label);font-size:9px;line-height:1.45}
</style>
'''
    html = html.replace("</head>", css + "</head>", 1)

    # Page 1 and page 2 are now part of a three-page report.
    html = html.replace("<b>01 / 02</b>", "<b>01 / 03</b>", 1)
    html = html.replace("<b>02 / 02</b>", "<b>02 / 03</b>", 1)

    # Move practical follow-up content from legal-source page to a dedicated third page.
    tail_pattern = re.compile(
        r'(?P<tail><div class="lower-grid">.*?<div class="disclaimer">.*?</div>)'
        r'(?P<footer><div class="footer"><span>TaxTreat</span><b>02 / 03</b></div>)',
        flags=re.DOTALL,
    )
    match = tail_pattern.search(html)
    if not match:
        return html

    tail = match.group("tail")
    html = html[: match.start("tail")] + match.group("footer") + html[match.end("footer") :]

    page3_title = (
        "Practical follow-up and supporting documents"
        if english
        else "Navazující povinnosti a podklady"
    )
    page3_copy = (
        "Deadlines, supporting documentation and additional legal sources relevant to the transaction."
        if english
        else "Lhůty, dokumentace a další právní zdroje relevantní pro posuzovanou transakci."
    )
    income = "Dividends" if english else "Dividendy"

    page3 = f'''
<section class="page tt-page-three"><div class="sheet">
  <header class="header"><div class="brand"><span class="shield">TT</span>TaxTreat</div><div class="head-meta"><b>{escape(payer)} → {escape(recipient)}</b>{income}</div></header>
  <div class="tt-page3-title"><span class="kicker">{'FOLLOW-UP' if english else 'NAVAZUJÍCÍ INFORMACE'}</span><h2>{page3_title}</h2><p>{page3_copy}</p></div>
  {tail}
  <div class="footer"><span>TaxTreat</span><b>03 / 03</b></div>
</div></section>
'''

    marker = '<template id="canonical-source-texts">'
    if marker in html:
        html = html.replace(marker, page3 + marker, 1)
    else:
        html = html.replace("</article></body>", page3 + "</article></body>", 1)
    return html
