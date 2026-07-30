from taxtreat.tools.fetch_official_sources import domain_allowed


def test_official_domains_are_allowed():
    assert domain_allowed("https://www.financnisprava.cz/example")
    assert domain_allowed("https://eur-lex.europa.eu/example")
    assert domain_allowed("https://www.bundesfinanzministerium.de/example")


def test_unapproved_domains_are_rejected():
    assert not domain_allowed("https://example.com/treaty")
    assert not domain_allowed("https://fake-oecd.org/document")
