import requests

import pytest

from taxtreat.tools import acquire_at_instrument_chain_pilot as pilot


class FakeResponse:
    url = "https://www.ris.bka.gv.at/Dokumente/BgblPdf/example.pdf"
    content = b"official treaty pdf"
    headers = {"content-type": "application/pdf"}

    def raise_for_status(self):
        return None


def test_fetch_retries_transient_read_timeout_then_succeeds(monkeypatch):
    attempts = []

    def fake_get(url, timeout, headers):
        attempts.append(url)
        if len(attempts) < 3:
            raise requests.ReadTimeout("temporary RIS latency")
        return FakeResponse()

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    content, content_type, final_url = pilot._fetch_official_source(
        "https://www.ris.bka.gv.at/Dokumente/BgblPdf/example.pdf"
    )
    assert len(attempts) == 3
    assert content == b"official treaty pdf"
    assert content_type == "application/pdf"
    assert final_url.endswith("example.pdf")


def test_fetch_fails_closed_after_transient_retry_budget(monkeypatch):
    attempts = []

    def fake_get(url, timeout, headers):
        attempts.append(url)
        raise requests.ConnectionError("RIS unavailable")

    monkeypatch.setattr(pilot.requests, "get", fake_get)
    with pytest.raises(ValueError, match="unavailable after 3 attempts"):
        pilot._fetch_official_source("https://www.ris.bka.gv.at/Dokumente/BgblPdf/example.pdf")
    assert len(attempts) == pilot.FETCH_ATTEMPTS
