import json
from datetime import date

from fastapi.testclient import TestClient

from app import main
from taxtreat.services.exchange_rates import (
    CnbRateUnavailableError,
    fetch_cnb_exchange_rate,
)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_cnb_rate_is_normalized_to_one_currency_unit():
    def opener(request, timeout):
        assert "date=2026-08-12" in request.full_url
        assert timeout == 10
        return _Response(
            {
                "rates": [
                    {
                        "validFor": "2026-08-12",
                        "amount": 100,
                        "currencyCode": "HUF",
                        "rate": 6.245,
                    }
                ]
            }
        )

    rate = fetch_cnb_exchange_rate(
        "huf",
        date(2026, 8, 12),
        opener=opener,
    )

    assert rate["currency"] == "HUF"
    assert rate["czk_per_unit"] == "0.06245"
    assert rate["quoted_amount"] == 100
    assert rate["published_for"] == "2026-08-12"
    assert rate["source_url"].startswith("https://www.cnb.cz/")


def test_cnb_rate_reports_missing_currency():
    def opener(_request, timeout):
        assert timeout == 10
        return _Response({"rates": []})

    try:
        fetch_cnb_exchange_rate(
            "EUR",
            date(2026, 8, 12),
            opener=opener,
        )
    except CnbRateUnavailableError as exc:
        assert "EUR" in str(exc)
    else:
        raise AssertionError("Missing CNB rate must fail closed.")


def test_cnb_endpoint_returns_structured_rate(monkeypatch):
    monkeypatch.setattr(
        main,
        "fetch_cnb_exchange_rate",
        lambda currency, rate_date: {
            "source": "CNB",
            "currency": currency,
            "czk_per_unit": "24.255",
            "effective_date": rate_date.isoformat(),
            "published_for": rate_date.isoformat(),
            "source_url": "https://www.cnb.cz/example",
        },
    )

    response = TestClient(main.app).get(
        "/exchange-rates/cnb?currency=EUR&date=2026-08-12"
    )

    assert response.status_code == 200
    assert response.json()["czk_per_unit"] == "24.255"


def test_cnb_endpoint_maps_upstream_failure_to_502(monkeypatch):
    def fail(_currency, _date):
        raise CnbRateUnavailableError("temporarily unavailable")

    monkeypatch.setattr(main, "fetch_cnb_exchange_rate", fail)
    response = TestClient(main.app).get(
        "/exchange-rates/cnb?currency=EUR&date=2026-08-12"
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "CNB_RATE_UNAVAILABLE"
