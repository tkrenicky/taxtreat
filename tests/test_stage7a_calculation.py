from __future__ import annotations

from datetime import date
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
    _parse_date,
    build_withholding_compliance_schedule,
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
EUR_AMOUNT = {
    "amount": "1000",
    "currency": "EUR",
    "payment_date": "2026-08-12",
    "accounting_date": "2026-08-10",
    "exchange_rate": {
        "source": "CNB",
        "currency": "EUR",
        "czk_per_unit": "24.85",
        "effective_date": "2026-08-10",
        "source_url": "https://www.cnb.cz/example",
    },
}


def test_czk_tax_is_rounded_down_to_whole_crowns():
    calculation = build_withholding_tax_calculation(
        {"amount": "100000.55", "currency": "czk"},
        decision_status="FINAL",
        rate_percent=Decimal("15"),
    )

    assert calculation == {
        "schema_version": 2,
        "status": "CALCULATED",
        "reason": None,
        "gross_amount": "100000.55",
        "transaction_currency": "CZK",
        "gross_amount_czk": "100000.55",
        "tax_currency": "CZK",
        "rate_percent": "15",
        "withholding_tax_czk": "15000",
        "net_amount_czk": "85000.55",
        "rounding_policy": "section_36_3_whole_crown_down",
        "exchange_rate": None,
    }


def test_foreign_amount_uses_cnb_rate_from_earlier_event_date():
    calculation = build_withholding_tax_calculation(
        EUR_AMOUNT,
        decision_status="FINAL",
        rate_percent=Decimal("15"),
    )

    assert calculation["gross_amount"] == "1000"
    assert calculation["transaction_currency"] == "EUR"
    assert calculation["gross_amount_czk"] == "24850.00"
    assert calculation["withholding_tax_czk"] == "3727"
    assert calculation["net_amount_czk"] == "21123.00"
    assert calculation["tax_currency"] == "CZK"
    assert calculation["exchange_rate"] == {
        "source": "CNB",
        "currency": "EUR",
        "czk_per_unit": "24.85",
        "effective_date": "2026-08-10",
        "payment_date": "2026-08-12",
        "accounting_date": "2026-08-10",
        "date_selection": "earlier_of_payment_or_accounting",
        "source_url": "https://www.cnb.cz/example",
    }


def test_non_final_result_never_calculates_candidate_tax():
    calculation = build_withholding_tax_calculation(
        EUR_AMOUNT,
        decision_status="REVIEW_REQUIRED",
        rate_percent=None,
    )

    assert calculation["status"] == "NOT_CALCULATED"
    assert calculation["reason"] == "final_rate_unavailable"
    assert calculation["withholding_tax_czk"] is None
    assert build_withholding_tax_calculation(
        None,
        decision_status="FINAL",
        rate_percent=15,
    ) is None


@pytest.mark.parametrize(
    ("amount", "reason"),
    [
        (
            {"amount": "1000", "currency": "EUR"},
            "exchange_rate_reference_dates_incomplete",
        ),
        (
            {
                "amount": "1000",
                "currency": "EUR",
                "payment_date": "2026-08-12",
                "accounting_date": "2026-08-10",
            },
            "exchange_rate_evidence_missing",
        ),
        (
            {
                **EUR_AMOUNT,
                "exchange_rate": {
                    **EUR_AMOUNT["exchange_rate"],
                    "effective_date": "2026-08-12",
                },
            },
            "exchange_rate_date_mismatch",
        ),
        (
            {
                **EUR_AMOUNT,
                "exchange_rate": {
                    **EUR_AMOUNT["exchange_rate"],
                    "source": "ECB",
                },
            },
            "exchange_rate_source_not_cnb",
        ),
        (
            {
                **EUR_AMOUNT,
                "exchange_rate": {
                    **EUR_AMOUNT["exchange_rate"],
                    "currency": "USD",
                },
            },
            "exchange_rate_currency_mismatch",
        ),
    ],
)
def test_foreign_currency_conversion_fails_closed(amount, reason):
    calculation = build_withholding_tax_calculation(
        amount,
        decision_status="FINAL",
        rate_percent=15,
    )

    assert calculation["status"] == "NOT_CALCULATED"
    assert calculation["reason"] == reason
    assert calculation["withholding_tax_czk"] is None


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


@pytest.mark.parametrize("rate", ["invalid", "0", "-1"])
def test_invalid_direct_exchange_rate_fails_closed(rate):
    amount = {
        **EUR_AMOUNT,
        "exchange_rate": {
            **EUR_AMOUNT["exchange_rate"],
            "czk_per_unit": rate,
        },
    }

    with pytest.raises(ValueError):
        build_withholding_tax_calculation(
            amount,
            decision_status="FINAL",
            rate_percent=15,
        )


def test_api_normalizes_currency_but_does_not_calculate_review_rate():
    response = client.post("/analysis", json=BASE_REQUEST)

    assert response.status_code == 200
    calculation = response.json()["withholding_tax_calculation"]
    assert calculation["status"] == "NOT_CALCULATED"
    assert calculation["transaction_currency"] == "CZK"
    assert calculation["withholding_tax_czk"] is None


def test_api_calculates_foreign_amount_only_from_mocked_final_result(
    monkeypatch,
):
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
    request = {
        **BASE_REQUEST,
        "transaction_amount": EUR_AMOUNT,
    }

    response = client.post("/analysis/report", json=request)

    assert response.status_code == 200
    payload = response.json()
    calculation = payload["report"]["result"][
        "withholding_tax_calculation"
    ]
    assert calculation["status"] == "CALCULATED"
    assert calculation["gross_amount_czk"] == "24850.00"
    assert calculation["withholding_tax_czk"] == "2485"
    assert calculation["net_amount_czk"] == "22365.00"
    assert calculation["exchange_rate"]["effective_date"] == "2026-08-10"
    assert "Srážková daň" in payload["html"]
    assert "2485" in payload["html"]
    assert "1 EUR = 24.85 CZK" in payload["html"]


def test_report_exposes_non_calculation_reason():
    response = client.post("/analysis/report", json=BASE_REQUEST)

    assert response.status_code == 200
    assert "final_rate_unavailable" in response.json()["html"]


@pytest.mark.parametrize(
    "transaction_amount",
    [
        {"amount": "0", "currency": "CZK"},
        {"amount": "-1", "currency": "CZK"},
        {"amount": "100", "currency": "CZ"},
        {"amount": "100", "currency": "12A"},
        {
            **EUR_AMOUNT,
            "exchange_rate": {
                **EUR_AMOUNT["exchange_rate"],
                "source": "ECB",
            },
        },
        {
            **EUR_AMOUNT,
            "exchange_rate": {
                **EUR_AMOUNT["exchange_rate"],
                "source_url": "http://invalid.example",
            },
        },
    ],
)
def test_api_rejects_invalid_transaction_amount(transaction_amount):
    response = client.post(
        "/analysis",
        json={**BASE_REQUEST, "transaction_amount": transaction_amount},
    )

    assert response.status_code == 422


def test_calculation_accepts_an_already_parsed_event_date():
    event_date = date(2026, 8, 12)

    assert _parse_date(event_date) is event_date


def test_tax_and_notification_are_due_at_end_of_following_month():
    schedule = build_withholding_compliance_schedule(
        "2026-08-12",
        income_type="dividend",
        decision_status="FINAL",
        rate_percent=10,
    )

    assert schedule == {
        "schema_version": 1,
        "status": "READY",
        "reference_date": "2026-08-12",
        "reference_date_basis": "earlier_of_payment_or_payable_recognition",
        "tax_remittance_deadline": "2026-09-30",
        "notification_deadline": "2026-09-30",
        "notification_regime": "withheld_income_same_as_remittance",
        "dividend_timing_review_required": True,
    }


def test_zero_rate_dividend_has_annual_notification_deadline():
    schedule = build_withholding_compliance_schedule(
        date(2026, 8, 12),
        income_type="dividend",
        decision_status="FINAL",
        rate_percent=0,
    )

    assert schedule["tax_remittance_deadline"] is None
    assert schedule["notification_deadline"] == "2027-02-01"
    assert schedule["notification_regime"] == (
        "exempt_or_treaty_non_taxable_annual"
    )


def test_non_final_result_keeps_compliance_dates_pending():
    schedule = build_withholding_compliance_schedule(
        "2026-08-12",
        income_type="dividend",
        decision_status="REVIEW_REQUIRED",
        rate_percent=None,
    )

    assert schedule["status"] == "PENDING_FINAL_TREATMENT"
    assert schedule["tax_remittance_deadline"] is None
    assert schedule["notification_deadline"] is None


def test_analysis_api_exposes_compliance_schedule():
    response = client.post("/analysis", json=BASE_REQUEST)

    assert response.status_code == 200
    schedule = response.json()["withholding_compliance_schedule"]
    assert schedule["reference_date"] == "2026-08-12"
    assert schedule["status"] == "PENDING_FINAL_TREATMENT"


@pytest.mark.parametrize("rate", ["invalid", -1, 101])
def test_compliance_schedule_rejects_invalid_final_rate(rate):
    with pytest.raises(ValueError):
        build_withholding_compliance_schedule(
            "2026-08-12",
            income_type="dividend",
            decision_status="FINAL",
            rate_percent=rate,
        )


def test_compliance_schedule_requires_a_reference_date():
    with pytest.raises(ValueError):
        build_withholding_compliance_schedule(
            None,
            income_type="dividend",
            decision_status="FINAL",
            rate_percent=10,
        )


def test_zero_rate_interest_keeps_notification_scope_open():
    schedule = build_withholding_compliance_schedule(
        "2026-08-12",
        income_type="interest",
        decision_status="FINAL",
        rate_percent=0,
    )

    assert schedule["status"] == "REVIEW_NOTIFICATION_SCOPE"
    assert schedule["notification_deadline"] is None
    assert schedule["notification_regime"] == (
        "income_classification_review_required"
    )
