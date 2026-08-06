import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_mli_pair_evidence_pack.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_twelve_pairs_are_included():
    payload = load()

    assert payload["mli_treaty_count"] == 12
    assert len(payload["records"]) == 12

    assert len({
        record["treaty_pair_id"]
        for record in payload["records"]
    }) == 12


def test_official_references_are_consolidated():
    payload = load()

    assert payload[
        "official_czech_reference_count"
    ] == 12

    for record in payload["records"]:
        applicability = record[
            "mli_applicability"
        ]

        assert applicability[
            "mli_applies"
        ] is True

        assert applicability[
            "verified"
        ] is True

        assert applicability[
            "official_reference_present"
        ] is True

        reference = applicability[
            "czech_mf_reference"
        ]

        assert (
            reference["financial_gazette"]
            or reference["consolidated_notice"]
        )


def test_articles_6_and_7_remain_verified():
    payload = load()

    assert payload[
        "article_6_verified_count"
    ] == 12

    assert payload[
        "article_7_verified_count"
    ] == 12

    for record in payload["records"]:
        assert record["article_6"][
            "verified"
        ] is True

        assert record["article_7"][
            "verified"
        ] is True

        assert record["article_7"][
            "ppt_applies"
        ] is True


def test_article_8_remains_pending():
    payload = load()

    assert payload[
        "article_8_verified_count"
    ] == 0

    assert payload[
        "article_8_pending_matching_count"
    ] == 12

    assert payload[
        "article_8_matching_complete"
    ] is False

    for record in payload["records"]:
        article = record["article_8"]

        assert article["verified"] is False

        assert article[
            "matching_outcome"
        ] == (
            "pending_pair_specific_matching_review"
        )

        assert article[
            "minimum_365_day_holding_period_added"
        ] is None


def test_entry_into_effect_remains_pending():
    payload = load()

    assert payload[
        "mli_entry_into_effect_verified_count"
    ] == 0

    assert payload[
        "mli_entry_into_effect_pending_count"
    ] == 12

    assert payload[
        "mli_entry_into_effect_review_complete"
    ] is False

    for record in payload["records"]:
        entry = record[
            "mli_entry_into_effect"
        ]

        assert entry["verified"] is False

        assert entry[
            "withholding_tax_effective_from"
        ] is None


def test_batch_remains_fail_closed():
    payload = load()

    assert payload["semantics"][
        "official_reference_is_full_legal_comparison"
    ] is False

    assert payload["semantics"][
        "pair_specific_matching_required"
    ] is True

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
