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


_POLISH_CSS = r"""
/* Round-3 release polish: legal/process timeline and balanced second-page rhythm. */
.flow {
    position: relative;
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    align-items: start;
    gap: 3mm;
    padding-top: .8mm;
}
.flow::before {
    content: "";
    position: absolute;
    left: 8%;
    right: 8%;
    top: 4.2mm;
    border-top: 1px solid #c8d1df;
    z-index: 0;
}
.flow-node {
    position: relative;
    z-index: 1;
    min-width: 0;
    padding: 0 1.2mm;
    border: 0;
    border-radius: 0;
    background: transparent;
    text-align: center;
}
.flow-node span {
    position: relative;
    z-index: 2;
    display: grid;
    place-items: center;
    width: 7mm;
    height: 7mm;
    margin: 0 auto 1.5mm;
    border: 1px solid #b8c3d2;
    border-radius: 50%;
    background: var(--paper);
    color: #6f7a8b;
    font-size: 5.8px;
    font-weight: 800;
    letter-spacing: .04em;
}
.flow-node b {
    display: block;
    margin: .4mm 0 .8mm;
    color: var(--navy);
    font-size: 7.2px;
}
.flow-node p {
    margin: 0;
    color: #555f6f;
    font-size: 6.1px;
    line-height: 1.32;
}
.flow-node:last-child {
    margin-top: -1.2mm;
    padding: 1.2mm 1.4mm 1.6mm;
    border: 0;
    border-radius: 2.2mm;
    background: var(--navy-soft);
}
.flow-node:last-child span {
    background: #f7faff;
    border-color: #aebfd8;
    color: var(--navy);
}
.flow-arrow,
.flow-principle {
    display: none !important;
}
/* Spread the existing page-2 content deliberately instead of leaving one trailing void. */
.page:nth-of-type(2) .sheet {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding-bottom: 16mm;
}
.page:nth-of-type(2) .header,
.page:nth-of-type(2) .section-head,
.page:nth-of-type(2) .legal-source,
.page:nth-of-type(2) .lower-grid,
.page:nth-of-type(2) .related-sources,
.page:nth-of-type(2) .hierarchy-note,
.page:nth-of-type(2) .disclaimer {
    flex: 0 0 auto;
}
.page:nth-of-type(2) .lower-grid,
.page:nth-of-type(2) .related-sources,
.page:nth-of-type(2) .hierarchy-note,
.page:nth-of-type(2) .disclaimer {
    margin-top: 0;
}
.page:nth-of-type(2) .related-sources {
    padding-top: 3.6mm;
    padding-bottom: 3.6mm;
}
.page:nth-of-type(2) .hierarchy-note {
    padding: 3.8mm 4mm;
}
.page:nth-of-type(2) .disclaimer {
    padding-top: 3.2mm;
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


def _apply_copy_polish(html: str) -> str:
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
            "Je-li relevantní, zohlední se modifikace smlouvy mnohostranným nástrojem (MLI) "
            "a test hlavního účelu (PPT)."
        ),
    }
    for current, revised in replacements.items():
        html = html.replace(current, revised)
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
    """Render the client report with the frozen round-3 release polish applied."""
    html = _render_client_report_html(report)
    html = _apply_copy_polish(html)
    html = _remove_duplicate_principle(html)
    html = _replace_disclaimer(html)
    return html.replace("</style>", _POLISH_CSS + "\n</style>", 1)
