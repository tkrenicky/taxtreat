import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_effective_date_evidence.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_treaties_are_present():
    payload = load()

    assert payload["treaty_partner_count"] == 23
    assert len(payload["records"]) == 23

    assert len({
        row["treaty_pair_id"]
        for row in payload["records"]
    }) == 23


def test_each_record_has_selected_source_article():
    payload = load()

    for record in payload["records"]:
        assert record[
            "selected_article_number"
        ] > 0

        assert record["article_text"]
        assert len(
            record["article_text_sha256"]
        ) == 64

        assert record["application_rule"][
            "classification"
        ]


def test_verified_dates_require_existing_evidence():
    payload = load()

    for record in payload["records"]:
        if record[
            "entry_into_force_verified"
        ]:
            assert record[
                "entry_into_force_date"
            ]

            assert record["date_source_path"]

        if record[
            "czech_withholding_effective_date_verified"
        ]:
            assert record[
                "czech_withholding_effective_from"
            ]

            assert record["date_source_path"]


def test_unresolved_dates_remain_fail_closed():
    payload = load()

    for record in payload["records"]:
        if record[
            "manual_date_verification_required"
        ]:
            assert not (
                record[
                    "entry_into_force_verified"
                ]
                and record[
                    "czech_withholding_effective_date_verified"
                ]
            )

        assert record["production_ready"] is False
        assert record["fail_closed"] is True

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True
