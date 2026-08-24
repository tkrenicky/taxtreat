from pathlib import Path

import pytest

from taxtreat.tools import acquire_at_instrument_chain_pilot as pilot


MACHINE = {
    "source_country": "AT",
    "status": "machine_source_inventory_not_reviewed",
    "records": [
        {
            "partner_label": "Deutschland / Germany",
            "release_universe_candidate": True,
            "treaty_links": [
                "https://www.ris.bka.gv.at/Dokumente/BgblPdf/base.pdf",
                "https://www.ris.bka.gv.at/GeltendeFassung.wxe?x=1",
            ],
            "mli_flag": False,
            "status_instrument_flag": False,
        },
        {
            "partner_label": "Tschechische Republik / Czech Republic",
            "release_universe_candidate": True,
            "treaty_links": [
                "https://www.bmf.gv.at/dam/example/MLI_Tschechien_synthesised.pdf"
            ],
            "mli_flag": True,
            "status_instrument_flag": False,
        },
    ],
}


class FakeResponse:
    def __init__(self, url: str, body: bytes, content_type: str = "application/pdf"):
        self.url = url
        self.content = body
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None


def test_classify_official_link_distinguishes_synthesized_current_and_published_sources():
    assert pilot.classify_official_link(
        "https://www.bmf.gv.at/dam/example/DBA_X_synthesised.pdf"
    ) == "synthesized_mli_text"
    assert pilot.classify_official_link(
        "https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen"
    ) == "current_consolidated_view"
    assert pilot.classify_official_link(
        "https://www.ris.bka.gv.at/Dokumente/BgblPdf/2002_182_3/2002_182_3.pdf"
    ) == "published_instrument_or_protocol"


def test_acquisition_hashes_official_sources_but_keeps_chain_and_articles_unreviewed(monkeypatch, tmp_path: Path):
    def fake_get(url, timeout, headers):
        assert timeout == 30
        assert headers["User-Agent"].startswith("TaxTreat")
        return FakeResponse(url, f"source:{url}".encode())

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    result = pilot.acquire_pilot(
        MACHINE,
        raw_dir=tmp_path,
        partners=("Deutschland / Germany", "Tschechische Republik / Czech Republic"),
    )

    assert result["status"] == "instrument_chain_pilot_acquired_not_reviewed"
    assert result["pilot_partner_count"] == 2
    assert result["source_count"] == 3
    assert all(row["instrument_chain_resolved"] is False for row in result["partners"])
    assert all(row["article_extraction_released"] is False for row in result["partners"])
    assert all(
        source["legal_review_completed"] is False
        for row in result["partners"]
        for source in row["sources"]
    )
    assert len(list(tmp_path.iterdir())) == 3


def test_acquisition_rejects_non_official_source_and_cross_host_redirect(monkeypatch, tmp_path: Path):
    with pytest.raises(ValueError, match="Non-official"):
        pilot._validate_official_url("https://example.com/treaty.pdf")

    def redirected(url, timeout, headers):
        return FakeResponse("https://example.com/redirect.pdf", b"bad")

    monkeypatch.setattr(pilot.requests, "get", redirected)
    with pytest.raises(ValueError, match="Non-official"):
        pilot.acquire_pilot(
            MACHINE,
            raw_dir=tmp_path,
            partners=("Deutschland / Germany",),
        )


def test_acquisition_fails_closed_on_missing_current_partner_or_empty_links(tmp_path: Path):
    with pytest.raises(ValueError, match="missing from current Austrian treaty universe"):
        pilot.acquire_pilot(MACHINE, raw_dir=tmp_path, partners=("Missing / Missing",))

    broken = {
        "source_country": "AT",
        "status": "machine_source_inventory_not_reviewed",
        "records": [
            {
                "partner_label": "Deutschland / Germany",
                "release_universe_candidate": True,
                "treaty_links": [],
            }
        ],
    }
    with pytest.raises(ValueError, match="no treaty-text links"):
        pilot.acquire_pilot(broken, raw_dir=tmp_path, partners=("Deutschland / Germany",))
