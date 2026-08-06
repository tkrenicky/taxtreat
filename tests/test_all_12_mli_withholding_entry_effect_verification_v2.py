import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_mli_withholding_entry_effect_verification_v2.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_hong_kong_is_resolved():
    payload = load()

    hong_kong = next(
        record
        for record in payload["records"]
        if record["treaty_pair_id"] == "CZ-HK"
    )

    assert hong_kong[
        "article_35_7_notification_date"
    ] == "2023-02-21"

    assert hong_kong[
        "article_35_7_notification_verified"
    ] is True

    assert hong_kong[
        "mli_withholding_effective_from"
    ] == "2024-01-01"

    assert hong_kong[
        "mli_withholding_entry_effect_verified"
    ] is True


def test_cyprus_is_not_inferred_from_silence():
    payload = load()

    cyprus = next(
        record
        for record in payload["records"]
        if record["treaty_pair_id"] == "CZ-CY"
    )

    if cyprus[
        "article_35_7_notification_verified"
    ]:
        assert cyprus[
            "article_35_7_notification_date"
        ]

        assert cyprus[
            "mli_withholding_effective_from"
        ]

        assert cyprus[
            "mli_withholding_entry_effect_verified"
        ] is True
    else:
        assert cyprus[
            "article_35_7_notification_date"
        ] is None

        assert cyprus[
            "mli_withholding_effective_from"
        ] is None

        assert cyprus[
            "mli_withholding_entry_effect_verified"
        ] is False


def test_counts_are_consistent():
    payload = load()

    verified = [
        record
        for record in payload["records"]
        if record[
            "mli_withholding_entry_effect_verified"
        ]
    ]

    pending = [
        record
        for record in payload["records"]
        if not record[
            "mli_withholding_entry_effect_verified"
        ]
    ]

    assert len(verified) == payload[
        "verified_withholding_entry_effect_count"
    ]

    assert len(pending) == payload[
        "pending_withholding_entry_effect_count"
    ]

    assert len(verified) + len(pending) == 12


def test_remaining_layers_stay_fail_closed():
    payload = load()

    assert payload[
        "verification_summary"
    ]["bilateral_protocol_review_complete"] is False

    assert payload[
        "verification_summary"
    ]["domestic_conditions_review_complete"] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True
