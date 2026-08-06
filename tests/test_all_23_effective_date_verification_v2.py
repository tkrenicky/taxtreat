import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_effective_date_verification_v2.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_twenty_two_withholding_dates_are_verified():
    payload = load()

    assert payload[
        "verified_entry_into_force_count"
    ] == 23

    assert payload[
        "verified_czech_withholding_date_count"
    ] == 22

    assert payload[
        "pending_czech_withholding_date_count"
    ] == 1

    assert payload[
        "pending_czech_withholding_pairs"
    ] == ["CZ-JP"]


def test_newly_verified_dates_match_official_notices():
    payload = load()

    expected = {
        "CZ-CL": "2017-01-01",
        "CZ-CO": "2016-01-01",
        "CZ-GH": "2021-01-01",
        "CZ-LU": "2015-01-01",
        "CZ-PA": "2014-01-01",
        "CZ-SM": "2023-01-01",
        "CZ-SN": "2023-01-01",
        "CZ-XK": "2024-01-01",
    }

    records = {
        record["treaty_pair_id"]: record
        for record in payload["records"]
    }

    for pair_id, effective_date in expected.items():
        record = records[pair_id]

        assert record[
            "czech_withholding_effective_from"
        ] == effective_date

        assert record[
            "czech_withholding_effective_date_verified"
        ] is True

        assert record[
            "czech_withholding_verification_status"
        ] == (
            "verified_against_mf_effective_date_notice"
        )

        assert record[
            "czech_withholding_official_source"
        ]["authority"] == (
            "Ministerstvo financí České republiky"
        )


def test_japan_remains_fail_closed():
    payload = load()

    japan = next(
        record
        for record in payload["records"]
        if record["treaty_pair_id"] == "CZ-JP"
    )

    assert japan[
        "czech_withholding_effective_date_verified"
    ] is False

    assert japan[
        "czech_withholding_effective_from"
    ] is None

    assert payload["verification_summary"][
        "japan_application_notice_review_required"
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
