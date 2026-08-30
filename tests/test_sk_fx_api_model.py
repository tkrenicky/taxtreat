from app.main import AnalysisPayload


def test_analysis_payload_accepts_slovak_ecb_exchange_rate_contract():
    payload = AnalysisPayload.model_validate({
        "source_country": "SK",
        "recipient_country": "US",
        "income_type": "royalty",
        "transaction_date": "2026-08-19",
        "transaction_amount": {
            "amount": "1000",
            "currency": "USD",
            "exchange_rate": {
                "source": "ECB",
                "currency": "USD",
                "foreign_units_per_eur": "1.1591",
                "effective_date": "2026-08-19",
                "source_url": "https://nbs.sk/",
            },
        },
    })

    dumped = payload.transaction_amount.model_dump(mode="json")
    assert dumped["exchange_rate"]["source"] == "ECB"
    assert dumped["exchange_rate"]["currency"] == "USD"
    assert dumped["exchange_rate"]["foreign_units_per_eur"] == "1.1591"
    assert "czk_per_unit" not in dumped["exchange_rate"]


def test_analysis_payload_still_accepts_czech_cnb_exchange_rate_contract():
    payload = AnalysisPayload.model_validate({
        "source_country": "CZ",
        "recipient_country": "US",
        "income_type": "royalty",
        "transaction_date": "2026-08-19",
        "transaction_amount": {
            "amount": "1000",
            "currency": "USD",
            "payment_date": "2026-08-19",
            "accounting_date": "2026-08-19",
            "exchange_rate": {
                "source": "CNB",
                "currency": "USD",
                "czk_per_unit": "21.5",
                "effective_date": "2026-08-19",
                "source_url": "https://www.cnb.cz/",
            },
        },
    })

    dumped = payload.transaction_amount.model_dump(mode="json")
    assert dumped["exchange_rate"]["source"] == "CNB"
    assert dumped["exchange_rate"]["czk_per_unit"] == "21.5"
