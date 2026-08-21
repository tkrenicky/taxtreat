from __future__ import annotations

import re
from html import escape
from typing import Any


_ZDP_URL = "https://e-sbirka.gov.cz/sb/1992/586"
_AT_EN_TREATY_URL = "https://www.bmf.gv.at/dam/jcr:8100aa41-e177-4705-8b4b-5f1178ffc0b1/MLI%20Tschechien%20englisch.pdf"


def _facts(report: dict[str, Any]) -> dict[str, Any]:
    return ((report.get("assumptions") or {}).get("transaction_facts") or {})


def _is_english(report: dict[str, Any]) -> bool:
    return str(_facts(report).get("__report_language") or "cs").lower() == "en"


def _scope(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("scope") or {}


def _result(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("result") or {}


def _is_cz_dividend_exemption(report: dict[str, Any]) -> bool:
    scope = _scope(report)
    result = _result(report)
    return (
        str(scope.get("source_country") or "CZ").upper() == "CZ"
        and str(scope.get("income_type") or "") == "dividend"
        and str(result.get("tax_treatment") or "") == "domestic_exemption"
    )


def _treaty_source(report: dict[str, Any]) -> dict[str, Any] | None:
    for source in report.get("official_sources") or []:
        if source.get("legal_layer") == "treaty":
            return source
    return None


def _article(source: dict[str, Any] | None) -> str:
    if not source:
        return ""
    article = str(source.get("article") or source.get("paragraph") or "").strip()
    if not article:
        return ""
    if article.lower().startswith(("art", "čl")):
        return article
    return f"čl. {article}"


def _replace_first(html: str, pattern: str, replacement: str, flags: int = 0) -> str:
    return re.sub(pattern, replacement, html, count=1, flags=flags)


def _primary_section19_block(english: bool) -> str:
    if english:
        return f'''
<article class="legal-source tt-section19-primary">
  <span class="kicker">PRIMARY LEGAL RULE APPLIED</span>
  <div class="legal-title-row">
    <h2>Section 19 of the Czech Income Taxes Act — domestic dividend exemption</h2>
    <div class="official"><a href="{_ZDP_URL}">Official Czech source · e-Sbírka ↗</a></div>
  </div>
  <div class="quote">
    <strong>English reading aid:</strong> a profit share paid by a Czech subsidiary to its qualifying parent company is exempt where the statutory parent/subsidiary conditions are met.
    The relevant conditions are set out principally in Section 19(1)(ze), Section 19(3)(a)–(c), Section 19(4) and Section 19(6); Section 19(8) is additionally relevant for Switzerland, Norway, Iceland and Liechtenstein.
  </div>
  <div class="transaction-gloss"><b>Connection to this transaction:</b> TaxTreat concluded from the entered facts that the domestic exemption conditions are satisfied. Czech withholding tax therefore does not apply.</div>
  <p class="legal-note">The English text above is a reading aid. The linked Czech statutory text is the official source.</p>
</article>'''
    return f'''
<article class="legal-source tt-section19-primary">
  <span class="kicker">POUŽITÉ PRÁVNÍ PRAVIDLO</span>
  <div class="legal-title-row">
    <h2>§ 19 ZDP — vnitrostátní osvobození podílu na zisku</h2>
    <div class="official"><a href="{_ZDP_URL}">Oficiální zdroj · e-sbirka.gov.cz ↗</a></div>
  </div>
  <div class="quote">
    <strong>Relevantní výňatek z § 19 odst. 1 písm. ze) bodu 1:</strong>
    „příjmy z podílu na zisku, vyplácené dceřinou společností, která je poplatníkem uvedeným v § 17 odst. 3, mateřské společnosti“.
    Navazující podmínky vyplývají zejména z § 19 odst. 3 písm. a) až c), § 19 odst. 4 a § 19 odst. 6 ZDP; pro Švýcarsko, Norsko, Island a Lichtenštejnsko také z § 19 odst. 8 ZDP.
  </div>
  <div class="transaction-gloss"><b>Vazba na tuto transakci:</b> Ze zadaných údajů TaxTreat vyhodnotil, že jsou podmínky vnitrostátního osvobození splněny. Česká srážková daň se proto neuplatní.</div>
  <p class="legal-note">Zobrazen je výňatek relevantní pro posuzovanou platbu; úplné znění je dostupné prostřednictvím odkazu na oficiální zdroj.</p>
</article>'''


def _secondary_treaty_block(report: dict[str, Any], original_block: str, english: bool) -> str:
    treaty = _treaty_source(report)
    if not treaty:
        return ""
    article = _article(treaty) or ("Article 10" if english else "čl. 10")
    country = str(_scope(report).get("recipient_country") or "").upper()
    if english:
        extra = ""
        if country == "AT":
            extra = f'<p class="legal-note"><a href="{_AT_EN_TREATY_URL}">Official English synthesised Austria–Czech treaty text ↗</a></p>'
        return f'''
<article class="legal-source tt-treaty-secondary">
  <span class="kicker">SECONDARY TREATY PROTECTION</span>
  <div class="legal-title-row"><h2>{escape(article)} — treaty limitation of Czech taxing rights</h2></div>
  <div class="quote"><strong>Role in this result:</strong> the treaty is not the primary legal basis for the exemption. It is shown as a secondary limitation of Czech taxing rights.</div>
  {extra}
</article>'''
    return f'''
<article class="legal-source tt-treaty-secondary">
  <span class="kicker">SEKUNDÁRNÍ SMLUVNÍ OCHRANA</span>
  <div class="legal-title-row"><h2>{escape(article)} — omezení českého práva zdanit podle SZDZ</h2></div>
  <div class="quote"><strong>Role v tomto výsledku:</strong> smlouva není primárním právním titulem osvobození. Je zobrazena pouze jako sekundární omezení českého práva zdanit.</div>
</article>'''


def apply_domestic_exemption_polish(html: str, report: dict[str, Any]) -> str:
    if not html or not _is_cz_dividend_exemption(report):
        return html

    english = _is_english(report)
    regime = "Exempt under Section 19" if english else "Osvobození podle § 19 ZDP"
    no_tax = "Does not apply" if english else "Neuplatňuje se"
    primary_ref = "Section 19 of the Czech Income Taxes Act" if english else "§ 19 ZDP"

    # Headline and summary: an exemption is a legal regime, not a 0% rate.
    html = html.replace("Shrnutí transakce, použité sazby a výpočtu srážkové daně.", "Shrnutí transakce, použitého daňového režimu a výpočtu české srážkové daně.")
    html = html.replace('<span class="kicker">Sazba české srážkové daně</span>', '<span class="kicker">Česká srážková daň</span>')
    html = html.replace('<div class="rate">0 %</div>', f'<div class="rate tt-exemption-result">{no_tax}</div>')
    html = html.replace('<span>Použitá sazba</span><b>0 %</b>', f'<span>Daňový režim</span><b>{regime}</b>')
    html = html.replace('<span>Použitá sazba</span><b>Neuplatňuje se</b>', f'<span>Daňový režim</span><b>{regime}</b>')

    # Summary legal hierarchy.
    html = re.sub(
        r'<div class="basis-row"><span>Použitý právní základ</span><b>.*?</b></div>',
        f'<div class="basis-row"><span>Použitý právní základ</span><b>{primary_ref}</b></div>',
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<div class="basis-row"><span>Smluvní sazba</span><b>.*?</b></div>',
        '<div class="basis-row"><span>Smluvní ochrana</span><b>Sekundární</b></div>',
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<div class="conclusion">.*?</div>',
        '<div class="conclusion">Při splnění uvedených předpokladů se použije vnitrostátní osvobození podle § 19 ZDP a česká srážková daň se neuplatní.</div>',
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<div class="path-note">.*?</div>',
        '<div class="path-note">Výchozí vnitrostátní režim podle § 36 ZDP → osvobození podle § 19 ZDP. SZDZ je v tomto výsledku pouze sekundární ochranou.</div>',
        html,
        count=1,
        flags=re.DOTALL,
    )

    # Calculation and flow: no fictitious 0% rate.
    html = html.replace('<span>Konečná sazba</span>', '<span>Konečný režim</span>')
    html = html.replace('<b>Konečná sazba</b>', '<b>Konečný režim</b>')
    html = html.replace('<p>0 %</p>', f'<p>{regime}</p>')
    html = html.replace('<p>0%</p>', f'<p>{regime}</p>')

    # Replace the primary treaty legal-source card with Section 19 and retain treaty only as secondary context.
    match = re.search(r'<article class="legal-source">.*?</article>', html, flags=re.DOTALL)
    if match:
        original = match.group(0)
        replacement = _primary_section19_block(english) + _secondary_treaty_block(report, original, english)
        html = html[: match.start()] + replacement + html[match.end() :]

    # Clarify hierarchy note.
    hierarchy = (
        "The Czech domestic exemption under Section 19 is the primary legal basis for this result. The treaty is displayed only as a secondary limitation of Czech taxing rights."
        if english
        else "V tomto výsledku je primárním právním titulem vnitrostátní osvobození podle § 19 ZDP. Smlouva je zobrazena pouze jako sekundární omezení českého práva zdanit."
    )
    html = re.sub(
        r'(<div class="hierarchy-note"><b>.*?</b>).*?(</div>)',
        rf'\1{hierarchy}\2',
        html,
        count=1,
        flags=re.DOTALL,
    )

    # Professional print treatment: preserve color, prevent split cards/diagram, avoid oversized exemption text.
    css = r'''
<style id="tt-domestic-exemption-print-polish">
.tt-exemption-result{font-size:30px!important;line-height:1.05!important;max-width:100%!important}
.tt-section19-primary,.tt-treaty-secondary{margin-top:4mm}
.tt-section19-primary{border-color:#b8d4ca!important;background:#eef6f2!important}
.tt-treaty-secondary{background:#f7f8fb!important}
@media print{
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
  .summary-grid,.assumptions,.calc-card,.flow-wrap,.legal-source,.lower-grid,.related-sources,.hierarchy-note{break-inside:avoid!important;page-break-inside:avoid!important}
  .flow-wrap{break-before:auto!important;page-break-before:auto!important}
  .page{break-after:page!important;page-break-after:always!important}
  .page:last-of-type{break-after:auto!important;page-break-after:auto!important}
}
</style>
'''
    html = html.replace("</head>", css + "</head>", 1)
    return html
