from taxtreat.validation.quality_gate import validate_record


def test_valid_record():
    errors = validate_record({
        "payer": "CZ",
        "recipient": "DE",
        "income_type": "dividend",
        "domestic_rate": 15,
        "treaty_rate": 5,
        "effective_rate": 5,
        "treaty_article": "10(2)",
        "treaty_source": "DTT",
        "domestic_source": "ITA",
        "confidence": 100,
        "manual_review": False,
    })

    assert errors == []


def test_invalid_effective_rate():
    errors = validate_record({
        "payer": "CZ",
        "recipient": "DE",
        "income_type": "dividend",
        "domestic_rate": 15,
        "treaty_rate": 5,
        "effective_rate": 15,
        "treaty_article": "10(2)",
        "treaty_source": "DTT",
        "domestic_source": "ITA",
    })

    assert any("Effective rate" in e for e in errors)
