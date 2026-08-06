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


def test_bosnia_rates():
    payload = load(
        "cz_ba_primary_treaty_verification.json"
    )

    articles = payload["income_articles"]

    assert articles["dividends"][
        "treaty_rates"
    ][0]["rate_percent"] == 5

    assert articles["interest"][
        "treaty_rates"
    ][0]["rate_percent"] == 0

    assert [
        row["rate_percent"]
        for row in articles["royalties"][
            "treaty_rates"
        ]
    ] == [0, 10]


def test_barbados_rates():
    payload = load(
        "cz_bb_primary_treaty_verification.json"
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

    assert articles["interest"][
        "standard_rate_percent"
    ] == 5

    assert [
        row["rate_percent"]
        for row in articles["royalties"][
            "treaty_rates"
        ]
    ] == [5, 10]


def test_bahrain_rates():
    payload = load(
        "cz_bh_primary_treaty_verification.json"
    )

    articles = payload["income_articles"]

    assert articles["dividends"][
        "treaty_rates"
    ][0]["rate_percent"] == 5

    assert articles["interest"][
        "treaty_rates"
    ][0]["rate_percent"] == 0

    assert articles["royalties"][
        "treaty_rates"
    ][0]["rate_percent"] == 10


def test_batch_remains_fail_closed():
    names = [
        "cz_ba_primary_treaty_verification.json",
        "cz_bb_primary_treaty_verification.json",
        "cz_bh_primary_treaty_verification.json",
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
