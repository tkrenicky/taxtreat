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
    annex = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/anlage1.pdf"
    html = f"""
    <html><body>
      <a href="{german}" title="Signiertes PDF-Dokument: deutscher Vertragstext"></a>
      <a href="{english}" title="Signiertes PDF-Dokument: englischer Vertragstext samt Protokoll"></a>
      <a href="{french}" title="Signiertes PDF-Dokument: französischer Vertragstext"></a>
      <a href="{annex}" title="Signiertes PDF-Dokument: Anlage 1"></a>
      <a href="{german}" title="Signiertes PDF-Dokument: deutscher Vertragstext"></a>
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

    assert result["schema_version"] == 5
    assert result["source_count"] == 3
    assert [row["final_url"] for row in sources] == [landing, german, english]
    assert sources[1]["discovered_from_url"] == landing
    assert sources[1]["discovery_method"] == "ris_treaty_text_attachment"
    assert sources[2]["discovered_from_url"] == landing
    assert all(row["legal_review_completed"] is False for row in sources)
    assert len(list(tmp_path.iterdir())) == 3


def test_ris_landing_page_discovers_text_oriented_german_html_companion(monkeypatch, tmp_path: Path):
    landing = "https://www.ris.bka.gv.at/eli/bgbl/III/2006/149/20060908"
    german_html = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2006_III_149/deutsch.html"
    german_pdf = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2006_III_149/deutsch.pdf"
    html = f"""
    <html><body>
      <a href="{german_html}" title="Web-Seite: deutscher Vertragstext"></a>
      <a href="{german_pdf}" title="Signiertes PDF-Dokument: deutscher Vertragstext"></a>
    </body></html>
    """.encode()

    def fake_get(url, timeout, headers):
        if url == landing:
            return FakeResponse(url, html, "text/html; charset=utf-8")
        if url == german_html:
            return FakeResponse(url, b"<html><body>Artikel 12 Lizenzgebuehren</body></html>", "text/html; charset=utf-8")
        if url == german_pdf:
            return FakeResponse(url, b"signed pdf", "application/pdf")
        raise AssertionError(f"Unexpected acquisition URL: {url}")

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    result = pilot.acquire_pilot(MACHINE, raw_dir=tmp_path, partners=("Algerien / Algeria",))
    assert [row["final_url"] for row in result["partners"][0]["sources"]] == [landing, german_html, german_pdf]


def test_ris_bgblpdf_viewer_discovers_canonical_publication_pdf(monkeypatch, tmp_path: Path):
    viewer = "https://www.ris.bka.gv.at/Dokument.wxe?Abfrage=BgblPdf&Dokumentnummer=2003_89_3"
    publication = "https://www.ris.bka.gv.at/Dokumente/BgblPdf/2003_89_3/2003_89_3.pdf"
    machine = {
        "source_country": "AT",
        "status": "machine_source_inventory_not_reviewed",
        "records": [{
            "partner_label": "Kirgisistan / Kyrgyzstan",
            "release_universe_candidate": True,
            "treaty_links": [viewer],
            "mli_flag": False,
            "status_instrument_flag": False,
        }],
    }
    html = f'<html><body><a href="{publication}" title="PDF-Dokument: BGBl. III Nr. 89/2003"></a></body></html>'.encode()

    def fake_get(url, timeout, headers):
        if url == viewer:
            return FakeResponse(url, html, "text/html; charset=utf-8")
        if url == publication:
            return FakeResponse(url, b"full treaty publication", "application/pdf")
        raise AssertionError(f"Unexpected acquisition URL: {url}")

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    result = pilot.acquire_pilot(machine, raw_dir=tmp_path, partners=("Kirgisistan / Kyrgyzstan",))
    assert result["source_count"] == 2
    assert result["partners"][0]["sources"][1]["final_url"] == publication


def test_ris_unlabeled_numbered_annexes_are_bounded_fallback(monkeypatch, tmp_path: Path):
    landing = "https://www.ris.bka.gv.at/eli/bgbl/II/2014/385/20141229"
    annexes = [f"https://www.ris.bka.gv.at/Dokumente/BgblAuth/example/anlage{i}.pdf" for i in range(1, 9)]
    machine = {
        "source_country": "AT",
        "status": "machine_source_inventory_not_reviewed",
        "records": [{
            "partner_label": "Taiwan / Taiwan",
            "release_universe_candidate": True,
            "treaty_links": [landing],
            "mli_flag": False,
            "status_instrument_flag": False,
        }],
    }
    html = "<html><body>" + "".join(
        f'<a href="{url}" title="Signiertes PDF-Dokument: Anlage {index}"></a>'
        for index, url in enumerate(annexes, 1)
    ) + "</body></html>"

    def fake_get(url, timeout, headers):
        if url == landing:
            return FakeResponse(url, html.encode(), "text/html; charset=utf-8")
        if url in set(annexes[:6]):
            return FakeResponse(url, f"PDF:{url}".encode(), "application/pdf")
        raise AssertionError(f"Unexpected acquisition URL: {url}")

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    result = pilot.acquire_pilot(machine, raw_dir=tmp_path, partners=("Taiwan / Taiwan",))
    sources = result["partners"][0]["sources"]
    assert result["source_count"] == 7
    assert [row["final_url"] for row in sources[1:]] == annexes[:6]


def test_ris_current_view_discovers_full_consolidated_pdf(monkeypatch, tmp_path: Path):
    current = "https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20005944"
    consolidated = "https://www.ris.bka.gv.at/GeltendeFassung/Bundesnormen/20005944/Doppelbesteuerung%20Albanien%2c%20Fassung%20vom%2024.08.2026.pdf"
    machine = {
        "source_country": "AT",
        "status": "machine_source_inventory_not_reviewed",
        "records": [{
            "partner_label": "Albanien / Albania",
            "release_universe_candidate": True,
            "treaty_links": [current],
            "mli_flag": True,
            "status_instrument_flag": False,
        }],
    }
    html = f'<html><body><a href="{consolidated}" title="PDF-Dokument: Doppelbesteuerung Albanien, Fassung vom 24.08.2026"></a></body></html>'.encode()

    def fake_get(url, timeout, headers):
        if url == current:
            return FakeResponse(url, html, "text/html; charset=utf-8")
        if url == consolidated:
            return FakeResponse(url, b"full consolidated treaty pdf", "application/pdf")
        raise AssertionError(f"Unexpected acquisition URL: {url}")

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    result = pilot.acquire_pilot(machine, raw_dir=tmp_path, partners=("Albanien / Albania",))
    sources = result["partners"][0]["sources"]
    assert result["source_count"] == 2
    assert sources[1]["final_url"] == consolidated
    assert sources[1]["role_candidate"] == "current_consolidated_view"
    assert sources[1]["discovered_from_url"] == current


def test_attachment_discovery_ignores_non_html_and_non_ris_sources():
    assert pilot._discover_ris_treaty_text_attachments(
        b"pdf", "application/pdf", "https://www.ris.bka.gv.at/Dokumente/BgblPdf/base.pdf"
    ) == ()
    assert pilot._discover_ris_treaty_text_attachments(
        b'<a href="https://www.bmf.gv.at/dam/example.pdf" title="deutscher Vertragstext"></a>',
        "text/html",
        "https://www.bmf.gv.at/example",
    ) == ()
