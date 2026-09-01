from dataclasses import dataclass

import app.sk_prerelease as api_module
from app.sk_prerelease import (
    SkPrereleaseAnalysisPayload,
    analyze_sk_prerelease,
    sk_prerelease_release_gate,
)


@dataclass
class _StubResult:
    def as_dict(self):
        return {
            "status": "REVIEW_REQUIRED",
            "source_country": "SK",
            "recipient_country": "AT",
            "income_type": "dividend",
            "candidate_only": True,
            "requires_review": True,
            "final_rate_percent": None,
            "czech_runtime_fallback_used": False,
            "runtime_released": False,
        }


def test_sk_prerelease_api_normalizes_scope_and_never_claims_production(monkeypatch):
    calls = []

    def fake_evaluator(**kwargs):
        calls.append(kwargs)
        return _StubResult()

    monkeypatch.setattr(api_module, "evaluate_sk_prerelease_candidate", fake_evaluator)
    payload = SkPrereleaseAnalysisPayload(
        recipient_country="at",
        income_type="DIVIDEND",
        facts={"recipient_entity_type": "corporate"},
    )

    response = analyze_sk_prerelease(payload)

    assert calls == [{
        "recipient_country": "AT",
        "income_type": "dividend",
        "facts": {"recipient_entity_type": "corporate"},
    }]
    assert response["status"] == "REVIEW_REQUIRED"
    assert response["candidate_only"] is True
    assert response["final_rate_percent"] is None
    assert response["czech_runtime_fallback_used"] is False
    assert response["runtime_released"] is False
    assert response["api_contract"] == "candidate_evidence_only"
    assert response["production_endpoint"] is False


def test_sk_release_gate_reports_released_source_country():
    response = sk_prerelease_release_gate()

    assert response["source_country"] == "SK"
    assert response["allowed"] is True
    assert response["code"] == "SOURCE_COUNTRY_RELEASED"
    assert response["release_status"] == "released"
    assert response["blockers"] == []


def test_preview_app_exposes_only_explicit_prerelease_paths():
    # OpenAPI is the public application contract and avoids depending on
    # FastAPI's internal representation of included routers.
    paths = set(api_module.preview_app.openapi()["paths"])

    assert "/analysis/pre-release/sk" in paths
    assert "/analysis/pre-release/sk/release-gate" in paths
    assert "/analysis" not in paths
