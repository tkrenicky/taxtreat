import json
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
        "https://ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Artikel=12&Gesetzesnummer=20005011"
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

    assert result["schema_version"] == 6
    assert result["status"] == "instrument_chain_pilot_acquired_not_reviewed"
    assert result["pilot_partner_count"] == 2
    assert result["source_count"] == 3
    assert result["curated_royalty_source_override_count"] == 0
    assert all(row["instrument_chain_resolved"] is False for row in result["partners"])
    assert all(row["article_extraction_released"] is False for row in result["partners"])
    assert all(
        source["legal_review_completed"] is False
        for row in result["partners"]
        for source in row["sources"]
    )
    assert all(
        source["curated_royalty_source_override"] is False
        for row in result["partners"]
        for source in row["sources"]
    )
    assert len(list(tmp_path.iterdir())) == 3


def test_curated_royalty_override_is_acquired_as_official_unreleased_evidence(monkeypatch, tmp_path: Path):
    def fake_get(url, timeout, headers):
        content_type = "text/html" if "NormDokument.wxe" in url else "application/pdf"
        return FakeResponse(url, f"source:{url}".encode(), content_type)

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    override_url = "https://ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Artikel=12&Gesetzesnummer=20005011"
    result = pilot.acquire_pilot(
        MACHINE,
        raw_dir=tmp_path,
        partners=("Deutschland / Germany",),
        royalty_source_overrides={"Deutschland / Germany": (override_url,)},
    )

    assert result["curated_royalty_source_override_count"] == 1
    row = result["partners"][0]
    assert row["curated_royalty_source_override_count"] == 1
    override = next(source for source in row["sources"] if source["curated_royalty_source_override"])
    assert override["listed_url"] == override_url
    assert override["role_candidate"] == "current_consolidated_view"
    assert override["legal_review_completed"] is False
    assert row["instrument_chain_resolved"] is False
    assert row["article_extraction_released"] is False


def test_override_registry_rejects_non_official_or_released_rows(tmp_path: Path):
    path = tmp_path / "overrides.json"
    path.write_text(json.dumps({
        "source_country": "AT",
        "status": "curated_official_source_overrides_not_reviewed",
        "partners": {
            "Deutschland / Germany": [{
                "article_number": 12,
                "url": "https://example.com/article12",
                "legal_review_completed": False,
                "projection_released": False,
            }]
        },
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="Non-official"):
        pilot.load_royalty_source_overrides(path)

    path.write_text(json.dumps({
        "source_country": "AT",
        "status": "curated_official_source_overrides_not_reviewed",
        "partners": {
            "Deutschland / Germany": [{
                "article_number": 12,
                "url": "https://ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Artikel=12",
                "legal_review_completed": True,
                "projection_released": False,
            }]
        },
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="must remain unreleased"):
        pilot.load_royalty_source_overrides(path)


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


def test_acquisition_rejects_override_for_partner_outside_current_universe(tmp_path: Path):
    with pytest.raises(ValueError, match="outside current treaty universe"):
        pilot.acquire_pilot(
            MACHINE,
            raw_dir=tmp_path,
            partners=("Deutschland / Germany",),
            royalty_source_overrides={"Missing / Missing": ("https://ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Artikel=12",)},
        )
