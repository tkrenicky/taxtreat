from pathlib import Path

from taxtreat.tools import acquire_at_instrument_chain_pilot as pilot


MACHINE = {
    "source_country": "AT",
    "status": "machine_source_inventory_not_reviewed",
    "records": [
        {
            "partner_label": "Algerien / Algeria",
            "release_universe_candidate": True,
            "treaty_links": ["https://www.ris.bka.gv.at/eli/bgbl/III/2006/176/20061116"],
            "mli_flag": False,
            "status_instrument_flag": False,
        }
    ],
}


class FakeResponse:
    def __init__(self, url: str, body: bytes, content_type: str):
        self.url = url
        self.content = body
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None


def test_ris_landing_page_discovers_german_and_english_treaty_text_pdfs_only(monkeypatch, tmp_path: Path):
    landing = "https://www.ris.bka.gv.at/eli/bgbl/III/2006/176/20061116"
    german = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/deutsch.pdf"
    english = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/english.pdf"
    french = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/francais.pdf"
    html = f"""
    <html><body>
      <a href="{german}">deutscher Vertragstext</a>
      <a href="{english}">englischer Vertragstext samt Protokoll</a>
      <a href="{french}">französischer Vertragstext</a>
      <a href="{german}">deutscher Vertragstext</a>
    </body></html>
    """.encode()

    def fake_get(url, timeout, headers):
        if url == landing:
            return FakeResponse(url, html, "text/html; charset=utf-8")
        if url in {german, english}:
            return FakeResponse(url, f"PDF:{url}".encode(), "application/pdf")
        raise AssertionError(f"Unexpected acquisition URL: {url}")

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    result = pilot.acquire_pilot(MACHINE, raw_dir=tmp_path, partners=("Algerien / Algeria",))
    sources = result["partners"][0]["sources"]

    assert result["schema_version"] == 3
    assert result["source_count"] == 3
    assert [row["final_url"] for row in sources] == [landing, german, english]
    assert sources[1]["discovered_from_url"] == landing
    assert sources[1]["discovery_method"] == "ris_treaty_text_attachment"
    assert sources[2]["discovered_from_url"] == landing
    assert all(row["legal_review_completed"] is False for row in sources)
    assert len(list(tmp_path.iterdir())) == 3


def test_attachment_discovery_ignores_non_html_and_non_ris_sources():
    assert pilot._discover_ris_treaty_text_attachments(
        b"pdf",
        "application/pdf",
        "https://www.ris.bka.gv.at/Dokumente/BgblPdf/base.pdf",
    ) == ()
    assert pilot._discover_ris_treaty_text_attachments(
        b'<a href="https://www.bmf.gv.at/dam/example.pdf">deutscher Vertragstext</a>',
        "text/html",
        "https://www.bmf.gv.at/example",
    ) == ()
