import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

REVIEW_ROOT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

INDEX_PATH = (
    REVIEW_ROOT
    / "remaining_13_primary_rate_confirmation_index.json"
)


def load(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_all_thirteen_records_exist():
    index = load(INDEX_PATH)

    assert index["treaty_partner_count"] == 13
    assert index["article_scope_count"] == 39
    assert len(index["records"]) == 13

    for record in index["records"]:
        assert (
            ROOT / record["output_path"]
        ).exists()


def test_all_records_remain_fail_closed():
    index = load(INDEX_PATH)

    for record in index["records"]:
        payload = load(
            ROOT / record["output_path"]
        )

        scope = payload["verification_scope"]

        assert scope[
            "nonzero_rate_evidence_confirmed"
        ] is True

        assert scope[
            "official_instrument_comparison_completed"
        ] is False

        assert scope[
            "transaction_decision_ready"
        ] is False

        assert payload[
            "legal_verification_completed"
        ] is False

        assert payload["production_ready"] is False
        assert payload["fail_closed"] is True


def test_zero_rates_are_not_overstated():
    index = load(INDEX_PATH)

    for record in index["records"]:
        payload = load(
            ROOT / record["output_path"]
        )

        for article in payload[
            "income_articles"
        ].values():
            if article["zero_rate_present"]:
                assert article[
                    "zero_rate_evidence_status"
                ] == (
                    "article_structure_recorded_"
                    "pending_official_comparison"
                )

                assert article[
                    "official_instrument_comparison_completed"
                ] is False


def test_chile_threshold_is_not_rate():
    index = load(INDEX_PATH)

    chile_record = next(
        row
        for row in index["records"]
        if row["treaty_pair_id"] == "CZ-CL"
    )

    chile = load(
        ROOT / chile_record["output_path"]
    )

    interest = chile[
        "income_articles"
    ]["interest"]

    assert interest["rates"] == [4, 15]
    assert 50 not in interest["rates"]

    assert interest[
        "excluded_numeric_conditions"
    ] == [50]
