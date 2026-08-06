import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_effective_date_review.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_treaties_are_included():
    payload = load()

    assert payload["treaty_partner_count"] == 23
    assert len(payload["records"]) == 23

    assert len({
        row["treaty_pair_id"]
        for row in payload["records"]
    }) == 23


def test_candidate_articles_preserve_source_evidence():
    payload = load()

    for record in payload["records"]:
        for article in record[
            "application_article_candidates"
        ]:
            assert article["article_number"] > 0
            assert article["article_text"]
            assert article["matched_phrases"]

            assert len(
                article["article_text_sha256"]
            ) == 64


def test_no_effective_date_is_overstated():
    payload = load()

    for record in payload["records"]:
        assert record[
            "entry_into_force_date"
        ] is None

        assert record[
            "czech_withholding_effective_from"
        ] is None

        assert record[
            "entry_into_force_verified"
        ] is False

        assert record[
            "czech_withholding_effective_date_verified"
        ] is False

        assert record[
            "manual_review_required"
        ] is True


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
        assert record["production_ready"] is False
        assert record["fail_closed"] is True
