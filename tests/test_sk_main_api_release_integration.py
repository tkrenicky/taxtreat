from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _production_payload():
    return {
        "source_country": "SK",
        "recipient_country": "AT",
        "income_type": "dividend",
        "transaction_date": "2026-08-19",
        "facts": {
            "recipient_entity_type": "corporate",
            "distribution_category_is_section_3_1_f": False,
            "distribution_is_tax_deductible_for_payer": False,
        },
    }


def test_production_analysis_rejects_unreleased_slovak_source_country_before_cz_runtime():
    response = client.post("/analysis", json=_production_payload())

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "SOURCE_COUNTRY_NOT_RELEASED"
    assert detail["source_country"] == "SK"
    assert detail["release_status"] == "pre_release"
    assert "source_country_runtime_release_false" in detail["release_blockers"]


def test_slovak_prerelease_api_is_explicitly_candidate_only():
    response = client.post(
        "/analysis/pre-release/sk",
        json={
            "recipient_country": "AT",
            "income_type": "dividend",
            "facts": {
                "recipient_entity_type": "corporate",
                "distribution_category_is_section_3_1_f": False,
                "distribution_is_tax_deductible_for_payer": False,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "REVIEW_REQUIRED"
    assert payload["candidate_only"] is True
    assert payload["requires_review"] is True
    assert payload["final_rate_percent"] is None
    assert payload["czech_runtime_fallback_used"] is False
    assert payload["runtime_released"] is False
    assert payload["api_contract"] == "candidate_evidence_only"
    assert payload["production_endpoint"] is False


def test_slovak_prerelease_release_gate_endpoint_is_closed():
    response = client.get("/analysis/pre-release/sk/release-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is False
    assert payload["code"] == "SOURCE_COUNTRY_NOT_RELEASED"
    assert payload["release_status"] == "pre_release"
