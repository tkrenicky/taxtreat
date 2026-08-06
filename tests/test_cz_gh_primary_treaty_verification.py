import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

VERIFICATION_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "verified"
    / "cz_gh_primary_treaty_verification.json"
)


def load():
    return json.loads(
        VERIFICATION_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_ghana_identity():
    payload = load()

    assert payload["treaty_pair_id"] == "CZ-GH"

    assert payload["source"][
        "source_title"
    ] == "38/2020 Sb. m. s."


def test_ghana_income_article_rates():
    payload = load()
    articles = payload["income_articles"]

    assert articles["dividends"][
        "treaty_rates"
    ][0]["rate_percent"] == 6

    assert articles["interest"][
        "standard_rate_percent"
    ] == 10

    assert articles["interest"][
        "exemptions_present"
    ] is True

    assert articles[
        "royalties_and_services"
    ]["standard_rate_percent"] == 8

    assert "technical services" in articles[
        "royalties_and_services"
    ]["covered_categories"]


def test_ghana_pending_reviews_are_explicit():
    payload = load()

    assert payload["verification_scope"][
        "entry_into_force_verified"
    ] is False

    assert payload["verification_scope"][
        "czech_withholding_effective_date_verified"
    ] is False

    assert payload["verification_scope"][
        "mli_position_verified"
    ] is False

    assert payload["overlay_review"][
        "protocol_review_status"
    ] == "pending"


def test_ghana_remains_fail_closed():
    payload = load()

    assert payload["verification_scope"][
        "primary_treaty_articles_10_to_12_verified"
    ] is True

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
