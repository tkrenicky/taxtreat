import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_mli_status_verification.json"
)

EXPECTED_MLI = {
    "CZ-BA",
    "CZ-BB",
    "CZ-BH",
    "CZ-CL",
    "CZ-CO",
    "CZ-CY",
    "CZ-GB",
    "CZ-HK",
    "CZ-JP",
    "CZ-LU",
    "CZ-PA",
    "CZ-PL",
}

EXPECTED_NO_MLI_LISTED = {
    "CZ-AD",
    "CZ-BW",
    "CZ-CM",
    "CZ-ET",
    "CZ-GH",
    "CZ-KR",
    "CZ-QA",
    "CZ-RW",
    "CZ-SM",
    "CZ-SN",
    "CZ-XK",
}


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_mli_statuses_are_classified():
    payload = load()

    assert payload["treaty_partner_count"] == 23

    assert payload[
        "mli_applicable_treaty_count"
    ] == 12

    assert payload[
        "no_mli_overlay_listed_count"
    ] == 11

    assert payload[
        "mli_status_verified_count"
    ] == 23

    assert set(
        payload["mli_applicable_pairs"]
    ) == EXPECTED_MLI

    assert set(
        payload["no_mli_overlay_listed_pairs"]
    ) == EXPECTED_NO_MLI_LISTED


def test_mli_pairs_preserve_official_source():
    payload = load()

    for record in payload["records"]:
        if record["mli_applies"]:
            assert record[
                "mli_status"
            ] == "mli_applies"

            assert record[
                "mli_status_verified"
            ] is True

            source = record[
                "mli_overlay_source"
            ]

            assert source[
                "czech_mf_source"
            ]["authority"] == (
                "Ministerstvo financí České republiky"
            )

            assert source["financial_gazette"]

            assert record[
                "article_7_ppt_review_status"
            ] == "pending_matching_review"


def test_non_mli_pairs_are_not_overstated():
    payload = load()

    for record in payload["records"]:
        if not record["mli_applies"]:
            assert record["mli_status"] == (
                "no_mli_overlay_listed_in_"
                "current_czech_mf_overview"
            )

            assert record[
                "bilateral_protocol_review_status"
            ] == "pending"

            assert record[
                "other_subsequent_instrument_review_status"
            ] == "pending"


def test_batch_remains_fail_closed():
    payload = load()

    summary = payload[
        "verification_summary"
    ]

    assert summary[
        "mli_applicability_review_complete"
    ] is True

    assert summary[
        "mli_article_matching_review_complete"
    ] is False

    assert summary[
        "bilateral_protocol_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    for record in payload["records"]:
        assert record[
            "transaction_decision_ready"
        ] is False

        assert record["production_ready"] is False
        assert record["fail_closed"] is True
