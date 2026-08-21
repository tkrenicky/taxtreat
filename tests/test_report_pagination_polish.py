from taxtreat.services.reporting.report_pagination_polish import apply_report_pagination_polish


def _report():
    return {
        "scope": {"source_country": "CZ", "recipient_country": "AT", "income_type": "dividend"},
        "result": {"tax_treatment": "domestic_exemption"},
        "assumptions": {"transaction_facts": {"report_payer_name": "Demo CZ s.r.o.", "report_recipient_name": "Demo GmbH"}},
    }


def test_domestic_exemption_report_is_split_into_three_logical_pages():
    html = """<html><head></head><body><article class="report">
    <section class="page"><div class="sheet"><div class="flow-node"><p>Osvobození podle § 19 ZDP</p></div><div class="footer"><span>TaxTreat</span><b>01 / 02</b></div></div></section>
    <section class="page"><div class="sheet"><article class="legal-source">Legal</article><div class="lower-grid">Deadlines and documents</div><div class="related-sources">Sources</div><div class="hierarchy-note">Hierarchy</div><div class="disclaimer">Disclaimer</div><div class="footer"><span>TaxTreat</span><b>02 / 02</b></div></div></section>
    <template id="canonical-source-texts"></template></article></body></html>"""
    polished = apply_report_pagination_polish(html, _report())
    assert "01 / 03" in polished
    assert "02 / 03" in polished
    assert "03 / 03" in polished
    assert "tt-page-three" in polished
    assert polished.index("tt-page-three") < polished.index('template id="canonical-source-texts"')
    assert polished.count("Deadlines and documents") == 1
