import hashlib
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_mli_withholding_entry_effect_verification.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_twelve_pairs_are_reviewed():
    payload = load()

    assert payload["mli_treaty_count"] == 12
    assert len(payload["records"]) == 12

    assert (
        payload[
            "verified_withholding_entry_effect_count"
        ]
        + payload[
            "pending_withholding_entry_effect_count"
        ]
        == 12
    )


def test_standard_dates_follow_article_35_rule():
    payload = load()

    for record in payload["records"]:
        later = date.fromisoformat(
            record[
                "later_entry_into_force_date"
            ]
        )

        standard = date.fromisoformat(
            record[
                "article_35_standard_withholding_date"
            ]
        )

        assert standard == date(
            later.year + 1,
            1,
            1,
        )


def test_verified_records_have_effective_date():
    payload = load()

    for record in payload["records"]:
        if record[
            "mli_withholding_entry_effect_verified"
        ]:
            assert record[
                "mli_withholding_effective_from"
            ]

            assert record[
                "article_35_7_special_reservation_detected"
            ] is False

            assert record["matching_outcome"] == (
                "verified_under_article_35_1_a_"
                "standard_calendar_year_rule"
            )
        else:
            assert record[
                "mli_withholding_effective_from"
            ] is None

            assert record[
                "article_35_7_special_reservation_detected"
            ] is True


def test_source_hashes_match():
    payload = load()

    for record in payload["records"]:
        evidence = record[
            "source_evidence"
        ]

        czech_path = (
            ROOT
            / evidence[
                "czech_position_text_path"
            ]
        )

        partner_path = (
            ROOT
            / evidence[
                "partner_position_text_path"
            ]
        )

        assert hashlib.sha256(
            czech_path.read_text(
                encoding="utf-8"
            ).encode("utf-8")
        ).hexdigest() == evidence[
            "czech_position_text_sha256"
        ]

        assert hashlib.sha256(
            partner_path.read_text(
                encoding="utf-8"
            ).encode("utf-8")
        ).hexdigest() == evidence[
            "partner_position_text_sha256"
        ]


def test_remaining_layers_stay_fail_closed():
    payload = load()

    summary = payload[
        "verification_summary"
    ]

    assert summary[
        "article_8_matching_complete"
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
