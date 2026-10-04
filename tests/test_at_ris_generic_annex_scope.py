from taxtreat.tools.acquire_at_instrument_chain_pilot import _discover_ris_treaty_text_attachments


def test_generic_numbered_annex_fallback_is_limited_to_eli_publication_pages():
    annex = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/anlage1.pdf"
    html = f'<html><body><a href="{annex}" title="Signiertes PDF-Dokument: Anlage 1"></a></body></html>'.encode()

    assert _discover_ris_treaty_text_attachments(
        html,
        "text/html; charset=utf-8",
        "https://www.ris.bka.gv.at/eli/bgbl/II/2014/385/20141229",
    ) == (annex,)

    assert _discover_ris_treaty_text_attachments(
        html,
        "text/html; charset=utf-8",
        "https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20005944",
    ) == ()
