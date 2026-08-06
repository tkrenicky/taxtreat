import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_mli_article_6_7_matching_verification.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_articles_6_and_7_remain_complete():
    payload = load()

    assert payload["mli_treaty_count"] == 12
    assert payload["article_6_applies_count"] == 12
    assert payload["article_7_ppt_applies_count"] == 12

    summary = payload["verification_summary"]

    assert summary[
        "article_6_matching_complete"
    ] is True

    assert summary[
        "article_7_matching_complete"
    ] is True


def test_article_8_is_not_overstated():
    payload = load()

    assert payload[
        "article_8_verified_count"
    ] == 0

    assert payload[
        "article_8_pending_matching_count"
    ] == 12

    assert payload[
        "verification_summary"
    ]["article_8_matching_complete"] is False

    for record in payload["records"]:
        article = record["article_8"]

        assert article["matching_outcome"] == (
            "pending_pair_specific_matching_review"
        )

        assert article[
            "minimum_365_day_holding_period_added"
        ] is None

        assert article[
            "effect_on_treaty_dividend_holding_period"
        ] == "not_yet_determined"

        assert article["verified"] is False

        assert len(
            article["required_evidence"]
        ) == 4


def test_article_8_blocks_transaction_decision():
    payload = load()

    for record in payload["records"]:
        consequences = record[
            "decision_consequences"
        ]

        assert consequences[
            "numeric_rate_lookup_may_proceed_without_article_8_overlay"
        ] is False

        assert consequences[
            "dividend_holding_period_requires_article_8_matching_review"
        ] is True

        assert consequences[
            "transaction_decision_ready"
        ] is False


def test_batch_remains_fail_closed():
    payload = load()

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
