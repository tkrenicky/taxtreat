import json
from urllib.error import HTTPError, URLError

from fastapi.testclient import TestClient

import app.main as app_main
from app.main import _normalize_ares_subject, app


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


def test_normalize_ares_subject_exposes_form_fields():
    payload = {
        "ico": "27082440",
        "obchodniJmeno": "Google Czech Republic, s.r.o.",
        "dic": "CZ27082440",
        "pravniForma": "112",
        "datumVzniku": "2003-10-08",
        "sidlo": {"textovaAdresa": "Stroupežnického 3191/17, 150 00 Praha 5"},
        "datoveSchranky": [{"datovaSchranka": "amqg4i4"}],
    }
    result = _normalize_ares_subject(payload)
    assert result["ico"] == "27082440"
    assert result["name"] == "Google Czech Republic, s.r.o."
    assert result["vat_id"] == "CZ27082440"
    assert result["address"] == "Stroupežnického 3191/17, 150 00 Praha 5"
    assert result["legal_form"] == "112"
    assert result["data_box"] == "amqg4i4"
    assert result["established_at"] == "2003-10-08"


def test_normalize_ares_subject_builds_address_and_accepts_plain_data_box():
    result = _normalize_ares_subject(
        {
            "ico": "12345678",
            "obchodniJmeno": "Test s.r.o.",
            "sidlo": {
                "nazevUlice": "Testovací",
                "cisloDomovni": 10,
                "cisloOrientacni": 2,
                "psc": 60200,
                "nazevObce": "Brno",
            },
            "datoveSchranky": ["abc123"],
        }
    )
    assert result["address"] == "Testovací 10/2, 60200 Brno"
    assert result["data_box"] == "abc123"


def test_ares_endpoint_returns_normalized_company(monkeypatch):
    monkeypatch.setattr(
        app_main,
        "urlopen",
        lambda request, timeout: DummyResponse(
            {
                "ico": "27082440",
                "obchodniJmeno": "Google Czech Republic, s.r.o.",
                "dic": "CZ27082440",
                "pravniForma": "112",
                "datumVzniku": "2003-10-08",
                "sidlo": {"textovaAdresa": "Stroupežnického 3191/17, Praha"},
                "datoveSchranky": [{"datovaSchranka": "amqg4i4"}],
            }
        ),
    )
    response = TestClient(app).get("/company-registry/ares/27082440")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "ARES"
    assert body["ico"] == "27082440"
    assert body["name"] == "Google Czech Republic, s.r.o."
    assert body["data_box"] == "amqg4i4"


def test_ares_endpoint_rejects_invalid_ico():
    response = TestClient(app).get("/company-registry/ares/123")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_ICO"


def test_ares_endpoint_maps_not_found(monkeypatch):
    def fail(request, timeout):
        raise HTTPError(request.full_url, 404, "not found", {}, None)

    monkeypatch.setattr(app_main, "urlopen", fail)
    response = TestClient(app).get("/company-registry/ares/12345678")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ARES_NOT_FOUND"


def test_ares_endpoint_maps_upstream_http_failure(monkeypatch):
    def fail(request, timeout):
        raise HTTPError(request.full_url, 500, "upstream error", {}, None)

    monkeypatch.setattr(app_main, "urlopen", fail)
    response = TestClient(app).get("/company-registry/ares/12345678")
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "ARES_UNAVAILABLE"


def test_ares_endpoint_maps_network_failure(monkeypatch):
    monkeypatch.setattr(
        app_main,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(URLError("offline")),
    )
    response = TestClient(app).get("/company-registry/ares/12345678")
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "ARES_UNAVAILABLE"


def test_ares_endpoint_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(
        app_main,
        "urlopen",
        lambda request, timeout: DummyResponse(b"not-json"),
    )
    response = TestClient(app).get("/company-registry/ares/12345678")
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "ARES_UNAVAILABLE"


def test_ares_endpoint_rejects_unexpected_payload(monkeypatch):
    monkeypatch.setattr(
        app_main,
        "urlopen",
        lambda request, timeout: DummyResponse({"obchodniJmeno": "Missing IČO"}),
    )
    response = TestClient(app).get("/company-registry/ares/12345678")
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "ARES_INVALID_RESPONSE"


def test_jurisdiction_catalog_contains_all_supported_destinations():
    response = TestClient(app).get("/jurisdictions")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 101
    codes = {item["iso2"] for item in body["jurisdictions"]}
    assert len(codes) == 101
    assert "KR" in codes
    assert "TW" in codes
