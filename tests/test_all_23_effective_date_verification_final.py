import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_effective_date_verification_final.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_effective_dates_are_complete():
    payload = load()

    assert payload["treaty_partner_count"] == 23

    assert payload[
        "verified_entry_into_force_count"
    ] == 23

    assert payload[
        "verified_czech_withholding_date_count"
    ] == 23

    assert payload[
        "pending_czech_withholding_date_count"
    ] == 0

    assert payload[
        "pending_czech_withholding_pairs"
    ] == []

    assert payload[
        "verification_summary"
    ]["entry_into_force_complete"] is True

    assert payload[
        "verification_summary"
    ]["czech_withholding_dates_complete"] is True


def test_japan_effective_date_is_verified():
    payload = load()

    japan = next(
        record
        for record in payload["records"]
        if record["treaty_pair_id"] == "CZ-JP"
    )

    assert japan[
        "entry_into_force_date"
    ] == "1978-11-25"

    assert japan[
        "czech_withholding_effective_from"
    ] == "1979-01-01"

    assert japan[
        "czech_withholding_effective_date_verified"
    ] is True

    assert japan[
        "czech_withholding_verification_status"
    ] == (
        "verified_from_article_28_"
        "first_tax_year_following_entry"
    )

    source = japan[
        "czech_withholding_official_source"
    ]

    assert source["instrument"] == "46/1979 Sb."
    assert source["article"] == 28
    assert source["effective_from"] == "1979-01-01"


def test_all_records_have_verified_dates():
    payload = load()

    for record in payload["records"]:
        assert record[
            "entry_into_force_verified"
        ] is True

        assert record[
            "entry_into_force_date"
        ]

        assert record[
            "czech_withholding_effective_date_verified"
        ] is True

        assert record[
            "czech_withholding_effective_from"
        ]


def test_remaining_legal_layers_stay_fail_closed():
    payload = load()

    summary = payload[
        "verification_summary"
    ]

    assert summary[
        "subsequent_treaty_overlay_review_complete"
    ] is False

    assert summary[
        "protocol_review_complete"
    ] is False

    assert summary[
        "mli_review_complete"
    ] is False

    assert summary[
        "domestic_conditions_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
