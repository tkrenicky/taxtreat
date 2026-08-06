import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_mli_article_6_7_8_verification.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_twelve_mli_treaties_are_included():
    payload = load()

    assert payload["mli_treaty_count"] == 12
    assert len(payload["records"]) == 12

    assert len({
        record["treaty_pair_id"]
        for record in payload["records"]
    }) == 12


def test_article_6_preamble_applies_to_all():
    payload = load()

    assert payload[
        "article_6_applies_count"
    ] == 12

    for record in payload["records"]:
        article = record["article_6"]

        assert article[
            "matching_outcome"
        ] == "applies"

        assert article[
            "minimum_standard_component"
        ] is True

        assert article["verified"] is True


def test_article_7_ppt_applies_to_all():
    payload = load()

    assert payload[
        "article_7_ppt_applies_count"
    ] == 12

    for record in payload["records"]:
        article = record["article_7"]

        assert article[
            "matching_outcome"
        ] == (
            "article_7_paragraph_1_ppt_applies"
        )

        assert article["ppt_applies"] is True

        assert article[
            "simplified_limitation_on_benefits_applies"
        ] is False

        assert article["verified"] is True


def test_article_8_does_not_add_holding_period():
    payload = load()

    assert payload[
        "article_8_applies_count"
    ] == 0

    for record in payload["records"]:
        article = record["article_8"]

        assert article["matching_outcome"] == (
            "does_not_apply_under_czech_mli_position"
        )

        assert article[
            "minimum_365_day_holding_period_added"
        ] is False

        assert article[
            "effect_on_treaty_dividend_holding_period"
        ] == "none_via_mli_article_8"

        assert article["verified"] is True


def test_numeric_rates_are_not_replaced():
    payload = load()

    for record in payload["records"]:
        assert record["rate_impact"][
            "articles_10_11_12_numeric_rates_modified"
        ] is False

        assert record[
            "decision_consequences"
        ]["ppt_must_be_evaluated"] is True


def test_batch_remains_fail_closed():
    payload = load()

    summary = payload[
        "verification_summary"
    ]

    assert summary[
        "articles_6_7_8_review_complete"
    ] is True

    assert summary[
        "mli_entry_into_effect_review_complete"
    ] is False

    assert summary[
        "bilateral_protocol_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    for record in payload["records"]:
        assert record[
            "decision_consequences"
        ]["transaction_decision_ready"] is False

        assert record["production_ready"] is False
        assert record["fail_closed"] is True
