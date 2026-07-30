from taxtreat.validation.confidence_engine import calculate_confidence


def test_complete_record():
    result = calculate_confidence({
        "treaty_rate": 5,
        "domestic_rate": 15,
        "treaty_source": "DTT",
        "domestic_source": "Income Tax Act",
        "treaty_article": "10(2)",
    })

    assert result["confidence"] == 100
    assert result["manual_review"] is False


def test_missing_sources():
    result = calculate_confidence({
        "treaty_rate": 5,
    })

    assert result["confidence"] < 100
    assert result["manual_review"] is True
    assert len(result["confidence_reasons"]) > 0
