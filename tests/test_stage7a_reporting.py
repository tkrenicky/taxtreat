from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from taxtreat.services.reporting import (
    DISCLAIMER,
    build_professional_report,
    render_report_html,
    stable_report_id,
)


client = TestClient(app)


REQUEST = {
    "source_country": "CZ",
    "recipient_country": "SG",
    "income_type": "dividend",
    "transaction_date": "2026-08-12",
    "facts": {},
    "determinations": {},
}


def test_stable_report_id_ignores_generation_time():
    analysis = {
        "status": "REVIEW_REQUIRED",
        "rate": None,
        "candidate_rate": 15.0,
        "selected_rule_id": None,
        "candidate_rule_id": "CZ-SG-DIVIDEND-DOMESTIC",
        "missing_facts": ["beneficial_owner"],
        "citations": [{"excerpt_sha256": "a" * 64}],
        "legal_dataset_release": "stage6-production-rules-2026-08-12.1",
        "dataset_version": "stage6-source-release-2026-08-12.1",
    }

    first = build_professional_report(
        REQUEST,
        analysis,
        generated_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
    )
    second = build_professional_report(
        REQUEST,
        analysis,
        generated_at=datetime(2026, 8, 13, tzinfo=timezone.utc),
    )

    assert first["report_id"] == second["report_id"]
    assert first["report_id"] == stable_report_id(REQUEST, analysis)
    assert first["generated_at"] != second["generated_at"]


def test_professional_report_preserves_review_required_semantics():
    response = client.post("/analysis/report", json=REQUEST)

    assert response.status_code == 200
    payload = response.json()
    report = payload["report"]

    assert report["schema_version"] == 1
    assert report["result"]["status"] == "REVIEW_REQUIRED"
    assert report["result"]["rate"] is None
    assert report["result"]["requires_review"] is True
    assert report["missing_facts"] == ["beneficial_owner"]
    assert report["legal_dataset_release"] == (
        "stage6-production-rules-2026-08-12.1"
    )
    assert report["source_release"] == (
        "stage6-source-release-2026-08-12.1"
    )
    assert report["disclaimer"] == DISCLAIMER
    assert "not tax advice" in report["disclaimer"]
    assert "<!doctype html>" in payload["html"]
    assert report["report_id"] in payload["html"]


def test_unknown_pair_report_remains_fail_closed():
    response = client.post(
        "/analysis/report",
        json={**REQUEST, "recipient_country": "ZZ"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "SOURCE_NOT_RELEASED",
        "treaty_pair_id": "CZ-ZZ",
        "release_status": "not_registered",
        "release_blockers": ["production_source_release_missing"],
    }


def test_html_renderer_escapes_untrusted_values():
    report = build_professional_report(
        {**REQUEST, "income_type": "<script>alert(1)</script>"},
        {
            "status": "OUT_OF_SCOPE",
            "citations": [],
            "dataset_version": "release",
        },
        generated_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
    )

    html = render_report_html(report)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
