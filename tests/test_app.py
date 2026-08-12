from pathlib import Path
import pytest
import sqlite3


import app.main as main
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app
import app.main as api


client = TestClient(app)


def test_liveness_and_readiness_are_distinct():
    assert client.get("/").json() == {"name": "TaxTreat", "version": "0.2.0"}
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health").json() == {"status": "ok"}

    readiness = client.get("/health/ready")

    assert readiness.status_code == 200
    assert readiness.json() == {
        "status": "ready",
        "release": {
            "dataset_release":
                "stage6-source-release-2026-08-12.1",
            "released_packages": 101,
            "released_scopes": 303,
        },
    }


def test_readiness_fails_when_stage6_release_is_invalid(
    monkeypatch,
):
    def invalid_release():
        raise RuntimeError("Stage 6 release invalid.")

    monkeypatch.setattr(
        api,
        "validate_stage6_runtime_release",
        invalid_release,
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Stage 6 release invalid."
    )


def test_analysis_uses_released_canonical_path():
    response = client.post(
        "/analysis",
        json={
            "source_country": "CZ",
            "recipient_country": "CH",
            "income_type": "royalty",
            "transaction_date": "2026-08-06",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "requires_review" in payload


def test_analysis_requires_transaction_date():
    response = client.post(
        "/analysis",
        json={
            "source_country": "CZ",
            "recipient_country": "CH",
            "income_type": "royalties",
        },
    )
    assert response.status_code == 422


def test_all_registered_jurisdictions_are_exposed():
    response = client.get("/jurisdictions")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 100
    by_code = {row["iso2"]: row for row in payload["jurisdictions"]}
    assert len(by_code) == 100
    assert by_code["AT"]["review_ready_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["AT"]["base_candidate_income_types"] == []
    assert by_code["DE"]["review_ready_income_types"] == []
    assert by_code["DE"]["base_candidate_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["DE"]["domestic_candidate_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["DE"]["eu_relief_candidate_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["GB"]["eu_relief_candidate_income_types"] == []
    assert by_code["BY"]["protocol_candidate_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["DE"]["protocol_candidate_income_types"] == []
    assert by_code["DE"]["candidate_chain_assembled_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["DE"]["candidate_chain_blocked_income_types"] == []
    assert by_code["DE"]["candidate_review_queued_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["DE"]["candidate_review_approved_income_types"] == []
    assert by_code["AT"]["candidate_review_queued_income_types"] == []
    assert by_code["GR"]["manual_rate_extraction_income_types"] == []
    assert by_code["GR"]["candidate_chain_blocked_income_types"] == []
    assert by_code["GR"]["candidate_chain_assembled_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]
    assert by_code["CO"]["candidate_chain_blocked_income_types"] == []
    assert by_code["CO"]["candidate_chain_assembled_income_types"] == [
        "dividend",
        "interest",
        "royalty",
    ]


def test_released_registered_scope_reaches_decision_engine():
    response = client.post(
        "/analysis",
        json={
            "source_country": "CZ",
            "recipient_country": "CH",
            "income_type": "royalty",
            "transaction_date": "2026-08-06",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "REVIEW_REQUIRED"
    assert payload["rate"] is None
    assert payload["requires_review"] is True


def test_analysis_uses_stage6_release_not_legacy_manifest(
    monkeypatch,
):
    monkeypatch.setattr(
        main,
        "RELEASE_MANIFEST",
        Path("/nonexistent/release_manifest.json"),
    )

    response = client.post(
        "/analysis",
        json={
            "source_country": "CZ",
            "recipient_country": "CH",
            "income_type": "royalty",
            "transaction_date": "2026-08-06",
        },
    )

    assert response.status_code == 200
    assert response.json()["dataset_version"] == (
        "stage6-source-release-2026-08-12.1"
    )


class FakeConnection:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.closed = False

    def execute(self, query):
        if self.error:
            raise self.error
        return self

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


def test_treaties_success_and_database_failures(monkeypatch):
    connection = FakeConnection(rows=[{"id": 1}])
    monkeypatch.setattr(api, "get_db_connection", lambda: connection)
    assert client.get("/treaties").json() == [{"id": 1}]
    assert connection.closed is True

    def missing():
        raise FileNotFoundError("missing")

    monkeypatch.setattr(api, "get_db_connection", missing)
    assert client.get("/treaties").status_code == 503

    broken = FakeConnection(error=sqlite3.OperationalError("bad schema"))
    monkeypatch.setattr(api, "get_db_connection", lambda: broken)
    response = client.get("/treaties")
    assert response.status_code == 503
    assert "schema is not ready" in response.json()["detail"]
    assert broken.closed is True


def test_get_db_connection_checks_file(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "ROOT", tmp_path)
    with pytest.raises(FileNotFoundError):
        api.get_db_connection()

    db = tmp_path / "taxtreat.db"
    sqlite3.connect(db).close()
    connection = api.get_db_connection()
    assert connection.row_factory is sqlite3.Row
    connection.close()

