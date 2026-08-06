import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "remaining_13_primary_instrument_comparison.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_remaining_scopes_are_included():
    payload = load()

    assert payload["treaty_partner_count"] == 13
    assert payload["article_scope_count"] == 39

    assert (
        payload[
            "fully_compared_article_scope_count"
        ]
        + payload[
            "partially_compared_article_scope_count"
        ]
        == 39
    )


def test_nonzero_only_scopes_are_completed():
    payload = load()

    for record in payload["records"]:
        for article in record[
            "income_articles"
        ].values():
            if not article[
                "zero_rate_present"
            ]:
                assert article[
                    "comparison_status"
                ] == (
                    "official_source_artifact_"
                    "comparison_completed"
                )

                assert article[
                    "nonzero_rates_verified"
                ] is True


def test_zero_rate_scopes_remain_partial():
    payload = load()

    partial = []

    for record in payload["records"]:
        for article in record[
            "income_articles"
        ].values():
            if article["zero_rate_present"]:
                partial.append(article)

                assert article[
                    "comparison_status"
                ] == (
                    "nonzero_components_verified_"
                    "zero_rate_pending"
                )

                assert article[
                    "zero_rate_verified"
                ] is False

    assert len(partial) == payload[
        "partially_compared_article_scope_count"
    ]


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

    for record in payload["records"]:
        assert record[
            "transaction_decision_ready"
        ] is False

        assert record["production_ready"] is False
        assert record["fail_closed"] is True
