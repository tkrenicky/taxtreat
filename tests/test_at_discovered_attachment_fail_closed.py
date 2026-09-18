from pathlib import Path

import pytest
import requests

from taxtreat.tools import acquire_at_instrument_chain_pilot as pilot


MACHINE = {
    "source_country": "AT",
    "status": "machine_source_inventory_not_reviewed",
    "records": [{
        "partner_label": "Albanien / Albania",
        "release_universe_candidate": True,
        "treaty_links": ["https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20005944"],
        "mli_flag": True,
        "status_instrument_flag": False,
    }],
}


def test_discovered_attachment_failure_is_recorded_without_releasing_partner(monkeypatch, tmp_path: Path):
    listed = MACHINE["records"][0]["treaty_links"][0]
    attachment = "https://www.ris.bka.gv.at/GeltendeFassung/Bundesnormen/20005944/current.pdf"

    def fake_fetch(url, *, timeout=30):
        if url == listed:
            html = f'<a href="{attachment}" title="PDF-Dokument: current treaty"></a>'.encode()
            return html, "text/html", listed
        if url == attachment:
            raise ValueError("Austrian treaty source unavailable after 3 attempts")
        raise AssertionError(url)

    monkeypatch.setattr(pilot, "_fetch_official_source", fake_fetch)
    result = pilot.acquire_pilot(MACHINE, raw_dir=tmp_path, partners=("Albanien / Albania",))
    partner = result["partners"][0]

    assert result["attachment_acquisition_failure_count"] == 1
    assert partner["source_count"] == 1
    assert partner["attachment_acquisition_complete"] is False
    assert partner["attachment_acquisition_failure_count"] == 1
    assert partner["attachment_acquisition_failures"][0]["listed_url"] == attachment
    assert partner["attachment_acquisition_failures"][0]["status"] == "discovered_attachment_not_acquired"
    assert partner["attachment_acquisition_failures"][0]["legal_review_completed"] is False
    assert partner["instrument_chain_resolved"] is False
    assert partner["article_extraction_released"] is False


def test_listed_primary_source_failure_remains_fatal(monkeypatch, tmp_path: Path):
    def fake_fetch(url, *, timeout=30):
        raise requests.ConnectionError("listed source unavailable")

    monkeypatch.setattr(pilot, "_fetch_official_source", fake_fetch)
    with pytest.raises(requests.ConnectionError, match="listed source unavailable"):
        pilot.acquire_pilot(MACHINE, raw_dir=tmp_path, partners=("Albanien / Albania",))
