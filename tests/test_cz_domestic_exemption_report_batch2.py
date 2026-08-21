from taxtreat.services.reporting.domestic_exemption_polish import apply_domestic_exemption_polish
from taxtreat.services.reporting.report_pagination_polish import apply_report_pagination_polish
from taxtreat.services.reporting.treaty_secondary_polish import apply_treaty_secondary_polish


def _report(language="cs"):
    return {
        "scope": {"source_country": "CZ", "recipient_country": "AT", "income_type": "dividend"},
        "result": {"tax_treatment": "domestic_exemption"},
        "assumptions": {"transaction_facts": {"__report_language": language, "report_payer_name": "Demo CZ s.r.o.", "report_recipient_name": "Demo GmbH"}},
        "official_sources": [{"legal_layer": "treaty", "article": "10", "excerpt": "Article 10 DIVIDENDY", "source_url": "https://example.test/treaty"}],
    }


def _html():
    return '''<html><head></head><body><article class="report">
<section class="page"><div class="sheet">
<div class="rate">0 %</div>
<div class="basis-row"><span>Smluvní sazba</span><b>0 %</b></div>
<div class="basis-row"><span>Použitý právní základ</span><b>čl. 10 smlouvy</b></div>
<div class="conclusion">Treaty conclusion</div><div class="path-note">Treaty path</div>
<div class="calc-row"><span>Použitá sazba</span><b>0 %</b></div>
<div class="flow-node"><b>Konečná sazba</b><p>0 %</p></div>
<div class="footer"><span>TaxTreat</span><b>01 / 02</b></div></div></section>
<section class="page"><div class="sheet"><article class="legal-source">Treaty primary</article>
<div class="lower-grid">Follow-up</div><div class="disclaimer">Disclaimer</div>
<div class="footer"><span>TaxTreat</span><b>02 / 02</b></div></div></section>
<template id="canonical-source-texts"></template></article></body></html>'''


def test_domestic_exemption_is_a_regime_not_zero_percent_rate():
    html = apply_domestic_exemption_polish(_html(), _report())
    assert '<div class="rate tt-exemption-result">Neuplatňuje se</div>' in html
    assert '<span>Daňový režim</span><b>Osvobození podle § 19 ZDP</b>' in html
    assert '<span>Použitý právní základ</span><b>§ 19 ZDP</b>' in html
    assert 'POUŽITÉ PRÁVNÍ PRAVIDLO' in html
    assert '§ 19 ZDP — vnitrostátní osvobození podílu na zisku' in html
    assert 'SEKUNDÁRNÍ SMLUVNÍ OCHRANA' in html


def test_treaty_excerpt_remains_secondary():
    html = apply_domestic_exemption_polish(_html(), _report())
    html = apply_treaty_secondary_polish(html, _report())
    assert 'Article 10 DIVIDENDY' in html
    assert 'smlouva není primárním právním titulem osvobození' in html


def test_domestic_exemption_report_uses_three_logical_pages():
    html = apply_domestic_exemption_polish(_html(), _report())
    html = apply_treaty_secondary_polish(html, _report())
    html = apply_report_pagination_polish(html, _report())
    assert '01 / 03' in html
    assert '02 / 03' in html
    assert '03 / 03' in html
    assert 'tt-page-three' in html
