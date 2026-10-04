from taxtreat.tools import acquire_at_instrument_chain_pilot as pilot


def test_relevant_ris_pdf_accepts_official_publication_and_language_variants():
    assert pilot._is_relevant_ris_pdf(
        "signiertes pdf-dokument: bgbl. iii nr. 52/2012",
        "/dokumente/bgblauth/bgbla_2012_iii_52/bgbla_2012_iii_52.pdf",
    ) is True
    assert pilot._is_relevant_ris_pdf(
        "signiertes pdf-dokument: englischer abkommenstext",
        "/dokumente/bgblauth/example/coo_english.pdf",
    ) is True
    assert pilot._is_relevant_ris_pdf(
        "signiertes pdf-dokument: abkommen samt protokoll in deutscher sprache",
        "/dokumente/bgblauth/example/coo_german.pdf",
    ) is True
    assert pilot._is_relevant_ris_pdf(
        "signiertes pdf-dokument: vertragstext in englischer sprache",
        "/dokumente/bgblauth/example/coo_english2.pdf",
    ) is True
    assert pilot._is_relevant_ris_pdf(
        "signiertes pdf-dokument: abkommen in deutscher sprachfassung",
        "/dokumente/bgblauth/example/coo_german2.pdf",
    ) is True
    assert pilot._is_relevant_ris_pdf(
        "pdf-dokument: current treaty",
        "/geltendefassung/bundesnormen/20000000/current.pdf",
    ) is True


def test_relevant_ris_pdf_rejects_unselected_language_or_unrelated_attachment():
    assert pilot._is_relevant_ris_pdf(
        "signiertes pdf-dokument: französischer vertragstext",
        "/dokumente/bgblauth/example/french.pdf",
    ) is False
    assert pilot._is_relevant_ris_pdf(
        "signiertes pdf-dokument: anlage 2",
        "/dokumente/bgblauth/example/anlage2.pdf",
    ) is False
