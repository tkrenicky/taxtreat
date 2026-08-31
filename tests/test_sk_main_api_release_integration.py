from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from taxtreat.services.source_country_release_gate import SourceCountryReleaseDecision


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


def test_production_analysis_blocks_sk_until_structured_treaty_rules_exist():
    response = client.post("/analysis", json=_production_payload())

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "SOURCE_COUNTRY_RELEASE_EVIDENCE_INCOMPLETE"
    assert "structured_sk_treaty_rules_not_materialized" in detail["release_blockers"]


def test_released_non_cz_source_country_returns_release_decision_without_fallthrough(monkeypatch):
    expected = SourceCountryReleaseDecision(
        source_country="SK",
        allowed=True,
        code="SOURCE_COUNTRY_RELEASED",
        release_status="released",
        blockers=(),
    )
    monkeypatch.setattr(
        main_module,
        "require_source_country_analysis_release",
        lambda source: expected,
    )

    result = main_module.require_analysis_source_release("SK", "AT")

    assert result is expected


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


def test_slovak_release_gate_status_endpoint_reports_materialization_blocker():
    response = client.get("/analysis/pre-release/sk/release-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is False
    assert payload["code"] == "SOURCE_COUNTRY_RELEASE_EVIDENCE_INCOMPLETE"
    assert payload["release_status"] == "pre_release"
    assert "structured_sk_treaty_rules_not_materialized" in payload["blockers"]
