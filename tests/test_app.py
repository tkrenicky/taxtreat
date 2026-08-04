import pytest
import sqlite3


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
    assert readiness.status_code == 503
    assert "Production gate failed" in readiness.json()["detail"]


def test_readiness_success(monkeypatch):
    monkeypatch.setattr(api, "validate_release", lambda **kwargs: {})
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_analysis_uses_canonical_fail_closed_path():
    response = client.post(
        "/analysis",
        json={
            "source_country": "CZ",
            "recipient_country": "CH",
            "income_type": "royalties",
            "transaction_date": "2026-08-03",
            "facts": {
                "recipient_is_treaty_resident": True,
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
                "arm_length_amount": True,
                "recipient_is_qualifying_company": False,
                "recipient_country_imposes_royalty_wht_on_nonresidents": False,
            },
            "determinations": {"treaty_ppt_passed": True},
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["rate"] is None
    assert result["candidate_rate"] == 5.0
    assert result["candidate_rule_id"] == "CZ-CH-ROY-PROTOCOL-5"
    assert result["legal_dataset_release"] == (
        "pilot-at-ch-2026-08-03-candidate.1"
    )
    assert result["citations"]
    assert any(row["layer"] == "mli" for row in result["layer_results"])
    assert result["requires_review"] is True
    assert result["dataset_version"] == "unreleased"


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


def test_pending_registered_scope_fails_closed_without_candidate_rate():
    response = client.post(
        "/analysis",
        json={
            "source_country": "CZ",
            "recipient_country": "DE",
            "income_type": "interest",
            "transaction_date": "2026-08-03",
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["rate"] is None
    assert result["candidate_rate"] is None
    assert result["missing_legal_layers"] == [
        "domestic",
        "eu_relief",
        "mli",
        "treaty_or_protocol",
    ]


def test_analysis_without_release_manifest_uses_unreleased(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "RELEASE_MANIFEST", tmp_path / "missing.json")
    response = client.post(
        "/analysis",
        json={
            "source_country": "CZ",
            "recipient_country": "DE",
            "income_type": "interest",
            "transaction_date": "2026-08-03",
        },
    )
    assert response.json()["dataset_version"] == "unreleased"


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
