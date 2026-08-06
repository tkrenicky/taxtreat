import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_mli_withholding_entry_effect_verification_final.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_mli_entry_effect_dates_are_complete():
    payload = load()

    assert payload["mli_treaty_count"] == 12

    assert payload[
        "verified_withholding_entry_effect_count"
    ] == 12

    assert payload[
        "pending_withholding_entry_effect_count"
    ] == 0

    assert len(
        payload["verified_pairs"]
    ) == 12

    assert payload["pending_pairs"] == []

    assert payload[
        "verification_summary"
    ]["mli_withholding_entry_effect_complete"] is True


def test_cyprus_is_verified_from_mf_notice():
    payload = load()

    cyprus = next(
        record
        for record in payload["records"]
        if record["treaty_pair_id"] == "CZ-CY"
    )

    assert cyprus[
        "mli_withholding_effective_from"
    ] == "2021-01-01"

    assert cyprus[
        "mli_withholding_entry_effect_verified"
    ] is True

    assert cyprus[
        "matching_outcome"
    ] == (
        "verified_against_czech_mf_"
        "consolidated_mli_notice"
    )

    source = cyprus[
        "article_35_7_source"
    ]

    assert source[
        "authority"
    ] == "Ministerstvo financí České republiky"

    assert source[
        "publication"
    ] == "Finanční zpravodaj č. 32/2020"

    assert source[
        "notice_number"
    ] == 42

    assert source[
        "effective_from"
    ] == "2021-01-01"


def test_all_records_have_verified_effective_date():
    payload = load()

    for record in payload["records"]:
        assert record[
            "mli_withholding_entry_effect_verified"
        ] is True

        assert record[
            "mli_withholding_effective_from"
        ]


def test_remaining_layers_stay_fail_closed():
    payload = load()

    summary = payload[
        "verification_summary"
    ]

    assert summary[
        "article_6_matching_complete"
    ] is True

    assert summary[
        "article_7_matching_complete"
    ] is True

    assert summary[
        "article_8_matching_complete"
    ] is True

    assert summary[
        "mli_withholding_entry_effect_complete"
    ] is True

    assert summary[
        "bilateral_protocol_review_complete"
    ] is False

    assert summary[
        "domestic_conditions_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True
