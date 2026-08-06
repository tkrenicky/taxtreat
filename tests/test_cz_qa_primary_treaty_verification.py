import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "verified"
    / "cz_qa_primary_treaty_verification.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_qatar_identity_and_application():
    payload = load()

    assert payload["treaty_pair_id"] == "CZ-QA"

    assert payload["source"][
        "entry_into_force_date"
    ] == "2022-10-25"

    assert payload["application"][
        "czech_withholding_tax_effective_from"
    ] == "2023-01-01"

    assert payload["source"][
        "decisive_language_on_divergence"
    ] == "English"


def test_qatar_income_article_rates():
    articles = load()["income_articles"]

    assert [
        row["rate_percent"]
        for row in articles["dividends"][
            "treaty_rates"
        ]
    ] == [5, 10]

    assert articles["dividends"][
        "public_entity_exemption_present"
    ] is True

    assert articles["interest"][
        "treaty_rates"
    ][0]["rate_percent"] == 0

    assert articles["royalties"][
        "treaty_rates"
    ][0]["rate_percent"] == 10


def test_qatar_treaty_ppt():
    payload = load()

    assert payload["anti_abuse"][
        "principal_purpose_test_present"
    ] is True

    assert payload["anti_abuse"][
        "competent_authority_relief_present"
    ] is True

    assert payload["verification_scope"][
        "treaty_level_ppt_verified"
    ] is True


def test_qatar_remains_fail_closed():
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

    assert payload["legal_verification_completed"] is False
    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True
    assert payload["promotable_to_active_rules"] is False
