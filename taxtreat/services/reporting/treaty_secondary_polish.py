from __future__ import annotations

import re
from html import escape
from typing import Any
from urllib.parse import urlparse


_AT_EN_TREATY_URL = "https://www.bmf.gv.at/dam/jcr:8100aa41-e177-4705-8b4b-5f1178ffc0b1/MLI%20Tschechien%20englisch.pdf"


def _facts(report: dict[str, Any]) -> dict[str, Any]:
    return ((report.get("assumptions") or {}).get("transaction_facts") or {})


def _english(report: dict[str, Any]) -> bool:
    return str(_facts(report).get("__report_language") or "cs").lower() == "en"


def _scope(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("scope") or {}


def _treaty(report: dict[str, Any]) -> dict[str, Any] | None:
    for source in report.get("official_sources") or []:
        if source.get("legal_layer") == "treaty":
            return source
    return None


def _article(source: dict[str, Any]) -> str:
    value = str(source.get("article") or source.get("paragraph") or "").strip()
    if not value:
        return ""
    if value.lower().startswith(("art", "čl")):
        return value
    return f"čl. {value}"


def _source_link(source: dict[str, Any]) -> str:
    url = str(source.get("source_url") or "").strip()
    if not url:
        return ""
    host = urlparse(url).netloc.replace("www.", "")
    label = f"Official source · {host}" if host else "Official source"
    return f'<a href="{escape(url, quote=True)}">{escape(label)} ↗</a>'


def _excerpt(source: dict[str, Any], limit: int = 1400) -> str:
    text = str(source.get("excerpt") or "").strip()
    if not text:
        return ""
    if len(text) > limit:
        head = text[:limit]
        cut = max(head.rfind(". "), head.rfind("; "), head.rfind(" "))
        text = (head[:cut] if cut > 600 else head).rstrip(" ,;:") + " …"
    return escape(text).replace("\n", "<br>")


def apply_treaty_secondary_polish(html: str, report: dict[str, Any]) -> str:
    if not html or str((report.get("result") or {}).get("tax_treatment") or "") != "domestic_exemption":
        return html
    source = _treaty(report)
    if not source:
        return html

    english = _english(report)
    article = _article(source) or ("Article 10" if english else "čl. 10")
    official_excerpt = _excerpt(source)
    source_link = _source_link(source)
    country = str(_scope(report).get("recipient_country") or "").upper()

    if english:
        english_link = ""
        if country == "AT":
            english_link = f'<a href="{_AT_EN_TREATY_URL}">Official English synthesised Austria–Czech treaty text ↗</a>'
        block = f'''
<article class="legal-source tt-treaty-secondary">
  <span class="kicker">SECONDARY TREATY PROTECTION</span>
  <div class="legal-title-row">
    <h2>{escape(article)} — treaty limitation of Czech taxing rights</h2>
    <div class="official">{english_link or source_link}</div>
  </div>
  <div class="quote"><strong>English reading aid:</strong> the dividends article limits Czech taxing rights. In this result, however, the treaty is not the primary legal basis because the Czech domestic exemption under Section 19 applies first.</div>
  {f'<details class="tt-official-language-excerpt"><summary>Official source excerpt</summary><div class="quote">{official_excerpt}</div></details>' if official_excerpt else ''}
  <p class="legal-note">{english_link or source_link}</p>
</article>'''
    else:
        block = f'''
<article class="legal-source tt-treaty-secondary">
  <span class="kicker">SEKUNDÁRNÍ SMLUVNÍ OCHRANA</span>
  <div class="legal-title-row">
    <h2>{escape(article)} — omezení českého práva zdanit podle SZDZ</h2>
    <div class="official">{source_link}</div>
  </div>
  <div class="quote">{official_excerpt or 'Samostatný výňatek smluvního ustanovení není v reportových datech k dispozici.'}</div>
  <div class="transaction-gloss"><b>Role v tomto výsledku:</b> smlouva není primárním právním titulem osvobození. Je zobrazena pouze jako sekundární omezení českého práva zdanit.</div>
</article>'''

    return re.sub(
        r'<article class="legal-source tt-treaty-secondary">.*?</article>',
        block,
        html,
        count=1,
        flags=re.DOTALL,
    )
