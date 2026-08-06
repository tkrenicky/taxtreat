import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

VERIFICATION_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "verified"
    / "cz_bw_primary_treaty_verification.json"
)


def load():
    return json.loads(
        VERIFICATION_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_botswana_identity_and_application():
    payload = load()

    assert payload["treaty_pair_id"] == "CZ-BW"

    assert payload["source"][
        "entry_into_force_date"
    ] == "2020-11-26"

    assert payload["application"][
        "czech_withholding_tax_effective_from"
    ] == "2021-01-01"


def test_botswana_income_article_rates():
    payload = load()
    articles = payload["income_articles"]

    assert articles["dividends"][
        "treaty_rates"
    ][0]["rate_percent"] == 5

    assert articles["interest"][
        "standard_rate_percent"
    ] == 7.5

    assert articles["interest"][
        "exemptions_present"
    ] is True

    assert articles[
        "royalties_and_technical_services"
    ]["standard_rate_percent"] == 7.5

    assert "technical services" in articles[
        "royalties_and_technical_services"
    ]["covered_categories"]


def test_botswana_overlay_remains_pending():
    payload = load()

    assert payload["overlay_review"][
        "mli_review_status"
    ] == "pending_pairwise_verification"

    assert payload["verification_scope"][
        "mli_position_verified"
    ] is False


def test_botswana_remains_fail_closed():
    payload = load()

    assert payload["verification_scope"][
        "primary_treaty_articles_10_to_12_verified"
    ] is True

    assert payload["verification_scope"][
        "domestic_conditions_verified"
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
