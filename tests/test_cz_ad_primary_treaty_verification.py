import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

VERIFICATION_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "verified"
    / "cz_ad_primary_treaty_verification.json"
)


def load():
    return json.loads(
        VERIFICATION_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_andorra_primary_treaty_identity():
    payload = load()

    assert payload["treaty_pair_id"] == "CZ-AD"
    assert payload["source"]["source_title"] == (
        "46/2023 Sb. m. s."
    )
    assert payload["source"][
        "entry_into_force_date"
    ] == "2023-10-31"

    assert payload["application"][
        "withholding_tax_effective_from"
    ] == "2024-01-01"


def test_andorra_verified_rates():
    payload = load()

    dividends = payload[
        "income_articles"
    ]["dividends"]["treaty_rates"]

    assert [
        row["rate_percent"]
        for row in dividends
    ] == [5, 10]

    interest = payload[
        "income_articles"
    ]["interest"]["treaty_rates"]

    assert [
        row["rate_percent"]
        for row in interest
    ] == [0]

    royalties = payload[
        "income_articles"
    ]["royalties"]["treaty_rates"]

    assert [
        row["rate_percent"]
        for row in royalties
    ] == [5, 10]


def test_andorra_remains_fail_closed():
    payload = load()

    assert payload["verification_scope"][
        "primary_treaty_articles_10_to_12_verified"
    ] is True

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
