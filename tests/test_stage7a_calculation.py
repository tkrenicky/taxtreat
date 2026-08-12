from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalDecisionResult,
)
from taxtreat.services.calculation import (
    build_withholding_tax_calculation,
)


client = TestClient(app)
BASE_REQUEST = {
    "source_country": "CZ",
    "recipient_country": "AT",
    "income_type": "dividend",
    "transaction_date": "2026-08-12",
    "transaction_amount": {
        "amount": "100000.55",
        "currency": "czk",
    },
}


def test_czk_tax_is_always_rounded_up_to_whole_crowns():
    calculation = build_withholding_tax_calculation(
        {"amount": "100000.55", "currency": "czk"},
        decision_status="FINAL",
        rate_percent=Decimal("15"),
    )

    assert calculation == {
        "schema_version": 1,
        "status": "CALCULATED",
        "reason": None,
        "gross_amount": "100000.55",
        "currency": "CZK",
        "rate_percent": "15",
        "estimated_tax_amount": "15001",
        "estimated_net_amount": "84999.55",
        "rounding_policy": "czk_whole_crown_up",
    }


def test_non_czk_tax_retains_two_decimal_half_up_rounding():
    calculation = build_withholding_tax_calculation(
        {"amount": "100.05", "currency": "EUR"},
        decision_status="FINAL",
        rate_percent=Decimal("15"),
    )

    assert calculation["estimated_tax_amount"] == "15.01"
    assert calculation["estimated_net_amount"] == "85.04"
    assert calculation["rounding_policy"] == "2_decimal_half_up"


def test_non_final_result_never_calculates_candidate_tax():
    calculation = build_withholding_tax_calculation(
        {"amount": "50000", "currency": "EUR"},
        decision_status="REVIEW_REQUIRED",
        rate_percent=None,
    )

    assert calculation["status"] == "NOT_CALCULATED"
    assert calculation["reason"] == "final_rate_unavailable"
    assert calculation["estimated_tax_amount"] is None
    assert build_withholding_tax_calculation(
        None,
        decision_status="FINAL",
        rate_percent=15,
    ) is None


@pytest.mark.parametrize("amount", ["invalid", "0", "-1"])
def test_invalid_direct_transaction_amount_fails_closed(amount):
    with pytest.raises(ValueError):
        build_withholding_tax_calculation(
            {"amount": amount, "currency": "CZK"},
            decision_status="FINAL",
            rate_percent=15,
        )


@pytest.mark.parametrize("rate", ["invalid", -1, 101])
def test_invalid_final_rate_fails_closed(rate):
    with pytest.raises(ValueError):
        build_withholding_tax_calculation(
            {"amount": "100", "currency": "CZK"},
            decision_status="FINAL",
            rate_percent=rate,
        )


def test_api_normalizes_currency_but_does_not_calculate_review_rate():
    response = client.post("/analysis", json=BASE_REQUEST)

    assert response.status_code == 200
    calculation = response.json()["withholding_tax_calculation"]
    assert calculation["status"] == "NOT_CALCULATED"
    assert calculation["currency"] == "CZK"
    assert calculation["estimated_tax_amount"] is None


def test_api_calculates_only_mocked_final_released_result(monkeypatch):
    monkeypatch.setattr(
        main,
        "analyze_transaction",
        lambda request: LegalDecisionResult(
            status=DecisionStatus.FINAL,
            rate=10.0,
            eligible=True,
            requires_review=False,
            selected_rule_id="TEST-FINAL-RULE",
            dataset_release="stage6-production-rules-2026-08-12.1",
        ),
    )

    response = client.post("/analysis/report", json=BASE_REQUEST)

    assert response.status_code == 200
    payload = response.json()
    calculation = payload["report"]["result"][
        "withholding_tax_calculation"
    ]
    assert calculation["status"] == "CALCULATED"
    assert calculation["estimated_tax_amount"] == "10001"
    assert calculation["estimated_net_amount"] == "89999.55"
    assert "Estimated withholding tax:" in payload["html"]
    assert "10001" in payload["html"]


def test_report_explains_why_review_amount_is_not_calculated():
    response = client.post("/analysis/report", json=BASE_REQUEST)

    assert response.status_code == 200
    assert "final released rate is unavailable" in response.json()["html"]


@pytest.mark.parametrize(
    "transaction_amount",
    [
        {"amount": "0", "currency": "CZK"},
        {"amount": "-1", "currency": "CZK"},
        {"amount": "100", "currency": "CZ"},
        {"amount": "100", "currency": "12A"},
    ],
)
def test_api_rejects_invalid_transaction_amount(transaction_amount):
    response = client.post(
        "/analysis",
        json={**BASE_REQUEST, "transaction_amount": transaction_amount},
    )

    assert response.status_code == 422
