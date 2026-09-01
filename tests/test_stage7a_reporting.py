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

    assert report["schema_version"] == 4
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
    assert "neposkytuje doporučení ani právní či daňové poradenství" in report["disclaimer"]
    assert "<!doctype html>" in payload["html"]
    assert report["report_id"] not in payload["html"]


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


def test_report_risk_labels_cover_final_and_out_of_scope():
    final = build_professional_report(
        REQUEST,
        {
            "status": "FINAL",
            "rate": 10.0,
            "citations": [],
            "dataset_version": "release",
        },
    )
    out_of_scope = build_professional_report(
        REQUEST,
        {
            "status": "OUT_OF_SCOPE",
            "citations": [],
            "dataset_version": "release",
        },
    )

    assert "přiřadil právní pravidlo k údajům zadaným uživatelem" in final["risk_assessment"]
    assert "mimo aktuálně podporovaný rozsah" in (
        out_of_scope["risk_assessment"]
    )


def test_stage6_source_release_validation_branches(
    monkeypatch,
    tmp_path,
):
    from app import main

    path = tmp_path / "stage6_source_release.json"
    monkeypatch.setattr(main, "STAGE6_SOURCE_RELEASE", path)

    try:
        main.load_stage6_source_release()
    except RuntimeError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Missing manifest must fail closed.")

    invalid_payloads = [
        {
            "counts": {
                "released_packages": 100,
                "released_scopes": 303,
            },
            "dataset_release": "release",
        },
        {
            "counts": {
                "released_packages": 101,
                "released_scopes": 302,
            },
            "dataset_release": "release",
        },
        {
            "counts": {
                "released_packages": 101,
                "released_scopes": 303,
            },
        },
    ]

    for payload in invalid_payloads:
        path.write_text(
            __import__("json").dumps(payload),
            encoding="utf-8",
        )
        try:
            main.load_stage6_source_release()
        except RuntimeError:
            pass
        else:
            raise AssertionError(
                "Invalid Stage 6 manifest must fail closed."
            )


def test_runtime_readiness_rejects_incomplete_gate(monkeypatch):
    from app import main

    monkeypatch.setattr(
        main,
        "load_stage6_source_release",
        lambda: {"dataset_release": "release"},
    )
    monkeypatch.setattr(
        main,
        "load_canonical_source_release_gate",
        lambda: {},
    )

    try:
        main.validate_stage6_runtime_release()
    except RuntimeError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("Incomplete gate must fail closed.")


def test_calculated_czk_report_omits_exchange_rate_details():
    report = {
        "report_id": "report-czk",
        "generated_at": "2026-08-12T00:00:00Z",
        "legal_data_cutoff": "2026-08-12",
        "scope": {
            "source_country": "CZ",
            "recipient_country": "AT",
            "income_type": "dividend",
            "transaction_date": "2026-08-12",
        },
        "result": {
            "status": "FINAL",
            "rate": 15,
            "candidate_rate": 15,
            "withholding_tax_calculation": {
                "status": "CALCULATED",
                "gross_amount": "1000",
                "transaction_currency": "CZK",
                "gross_amount_czk": "1000.00",
                "withholding_tax_czk": "150",
                "net_amount_czk": "850.00",
                "rounding_policy": "down_to_whole_czk",
                "exchange_rate": None,
            },
        },
        "risk_assessment": "Final released rule.",
        "missing_facts": [],
        "official_sources": [],
        "legal_dataset_release": "rules",
        "source_release": "sources",
        "disclaimer": DISCLAIMER,
    }

    html = render_report_html(report)

    assert "<th>Srážková daň</th><td>150 Kč</td>" in html
    assert "Kurz ČNB" not in html


def test_report_distinguishes_foreign_taxation_from_zero_rate():
    report = build_professional_report(
        REQUEST,
        {
            "status": "FINAL",
            "rate": None,
            "candidate_rate": 0.0,
            "tax_treatment": "exclusive_foreign_taxation",
            "candidate_tax_treatment": "exclusive_foreign_taxation",
            "citations": [
                {
                    "legal_layer": "treaty",
                    "article": "10",
                    "source_url": "https://example.test/treaty",
                    "excerpt": "Příjem může být zdaněn pouze ve státě rezidence.",
                }
            ],
            "withholding_tax_calculation": {
                "status": "CALCULATED",
                "gross_amount": "1000",
                "transaction_currency": "CZK",
                "gross_amount_czk": "1000",
                "withholding_tax_czk": "0",
                "net_amount_czk": "1000.00",
                "tax_treatment": "exclusive_foreign_taxation",
                "exchange_rate": None,
            },
            "dataset_version": "release",
        },
    )

    html = render_report_html(report)

    assert report["result"]["rate"] is None
    assert report["result"]["tax_treatment"] == (
        "exclusive_foreign_taxation"
    )
    assert "pravidlo bez českého zdanění" in html
    assert "<th>Česká daň k odvodu</th><td>0 Kč</td>" in html
    assert "Sazba Neuplatňuje se" in html
    assert "Sazba české srážkové daně: 0" not in html
    assert "ZERO-treaty" not in html


def test_slovak_english_report_structured_copy_is_source_country_aware():
    request = {
        "source_country": "SK",
        "recipient_country": "AT",
        "income_type": "interest",
        "transaction_date": "2026-08-19",
        "facts": {},
        "determinations": {},
    }
    report = build_professional_report(
        request,
        {
            "status": "FINAL",
            "rate": None,
            "tax_treatment": "domestic_exemption",
            "citations": [
                {
                    "rule_id": "SK-DOMESTIC",
                    "legal_layer": "domestic",
                    "article": "13",
                    "source_url": "https://static.slov-lex.sk/example",
                }
            ],
            "dataset_version": "sk-release",
        },
        language="en",
    )

    assert "Slovak domestic rule" in report["risk_assessment"]
    assert "Czech domestic rule" not in report["risk_assessment"]


def test_slovak_english_report_does_not_reuse_cz_treaty_excerpt():
    request = {
        "source_country": "SK",
        "recipient_country": "AT",
        "income_type": "interest",
        "transaction_date": "2026-08-19",
        "facts": {},
        "determinations": {},
    }
    report = build_professional_report(
        request,
        {
            "status": "REVIEW_REQUIRED",
            "rate": None,
            "citations": [
                {
                    "rule_id": "SK-AT-INTEREST",
                    "legal_layer": "treaty",
                    "article": "11",
                    "source_url": "https://static.slov-lex.sk/sk-at",
                    "excerpt": "Slovak canonical treaty text",
                }
            ],
            "dataset_version": "sk-release",
        },
        language="en",
    )

    source = report["official_sources"][0]
    assert source["canonical_source_url"] == "https://static.slov-lex.sk/sk-at"
    assert source["excerpt"] is None
    assert source["excerpt_status"] == "english_excerpt_unavailable"
    assert source["excerpt_status_label"] == "English excerpt unavailable"
