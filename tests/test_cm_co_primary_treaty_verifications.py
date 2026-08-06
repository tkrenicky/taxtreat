import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

VERIFIED_ROOT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "verified"
)


def load(name):
    return json.loads(
        (VERIFIED_ROOT / name).read_text(
            encoding="utf-8"
        )
    )


def test_cameroon_rates():
    payload = load(
        "cz_cm_primary_treaty_verification.json"
    )

    articles = payload["income_articles"]

    assert articles["dividends"][
        "treaty_rates"
    ][0]["rate_percent"] == 10

    assert articles["interest"][
        "standard_rate_percent"
    ] == 10

    services = articles[
        "royalties_and_technical_services"
    ]

    assert services[
        "standard_rate_percent"
    ] == 10

    assert services["covered_categories"] == [
        "royalties",
        "technical services",
    ]


def test_cameroon_identity():
    payload = load(
        "cz_cm_primary_treaty_verification.json"
    )

    assert payload["source"][
        "entry_into_force_date"
    ] == "2025-07-07"

    assert payload["source"][
        "decisive_language_on_divergence"
    ] == "English"


def test_colombia_rates():
    payload = load(
        "cz_co_primary_treaty_verification.json"
    )

    articles = payload["income_articles"]

    assert [
        row["rate_percent"]
        for row in articles["dividends"][
            "treaty_rates"
        ]
    ] == [5, 15]

    assert articles["dividends"][
        "treaty_rates"
    ][0]["conditions"][
        "minimum_direct_holding_percent"
    ] == 25

    assert articles["dividends"][
        "source_state_special_rule"
    ]["rate_percent"] == 25

    assert articles["interest"][
        "standard_rate_percent"
    ] == 10

    assert articles["royalties"][
        "standard_rate_percent"
    ] == 10


def test_batch_remains_fail_closed():
    names = [
        "cz_cm_primary_treaty_verification.json",
        "cz_co_primary_treaty_verification.json",
    ]

    for name in names:
        payload = load(name)

        assert payload["verification_scope"][
            "primary_treaty_articles_10_to_12_verified"
        ] is True

        assert payload["verification_scope"][
            "czech_withholding_effective_date_verified"
        ] is False

        assert payload["verification_scope"][
            "mli_position_verified"
        ] is False

        assert payload["verification_scope"][
            "transaction_decision_ready"
        ] is False

        assert payload[
            "legal_verification_completed"
        ] is False

        assert payload["production_ready"] is False
        assert payload["fail_closed"] is True

        assert payload[
            "promotable_to_active_rules"
        ] is False
