import json
from pathlib import Path

ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)


def load(name):
    return json.loads(
        (ROOT / name).read_text(
            encoding="utf-8"
        )
    )


def test_plan_covers_all_treaty_partners():
    payload = load(
        "global_source_acquisition_plan.json"
    )

    assert payload[
        "treaty_partner_count"
    ] == 98

    assert len(
        payload["treaty_partners"]
    ) == 98

    assert len({
        row["treaty_pair_id"]
        for row in payload[
            "treaty_partners"
        ]
    }) == 98


def test_every_entry_has_explicit_status():
    payload = load(
        "global_source_acquisition_plan.json"
    )

    allowed = {
        "acquire_official_source",
        "resolve_source_identity",
        "repair_local_source_evidence",
        "replace_damaged_text_source",
        "verify_existing_clean_candidate",
        "rebuild_clean_text",
    }

    for row in payload[
        "treaty_partners"
    ]:
        assert (
            row["acquisition_status"]
            in allowed
        )
        assert row[
            "production_blockers"
        ]
        assert row[
            "production_ready"
        ] is False
        assert row[
            "fail_closed"
        ] is True


def test_damaged_text_is_rejected():
    payload = load(
        "global_source_acquisition_plan.json"
    )

    for row in payload[
        "treaty_partners"
    ]:
        if row[
            "parsed_text_quality"
        ]["status"] == (
            "rejected_encoding_damage"
        ):
            assert row[
                "acquisition_status"
            ] == (
                "replace_damaged_text_source"
            )
            assert (
                "parsed_text_encoding_damaged"
                in row[
                    "production_blockers"
                ]
            )


def test_at_and_ch_remain_rejected():
    payload = load(
        "global_source_acquisition_plan.json"
    )

    by_country = {
        row["partner_country"]: row
        for row in payload[
            "treaty_partners"
        ]
    }

    for country in ("AT", "CH"):
        assert by_country[country][
            "parsed_text_quality"
        ]["status"] == (
            "rejected_encoding_damage"
        )

        assert by_country[country][
            "acquisition_status"
        ] == (
            "replace_damaged_text_source"
        )


def test_summary_matches_plan():
    payload = load(
        "global_source_acquisition_plan.json"
    )
    summary = load(
        "global_source_acquisition_plan_summary.json"
    )

    assert summary[
        "treaty_partner_count"
    ] == 98

    assert sum(
        summary[
            "acquisition_status_counts"
        ].values()
    ) == 98

    assert sum(
        summary[
            "parsed_text_quality_counts"
        ].values()
    ) == 98


def test_nothing_is_promoted():
    payload = load(
        "global_source_acquisition_plan.json"
    )

    assert payload[
        "production_ready"
    ] is False
    assert payload[
        "fail_closed"
    ] is True
    assert payload[
        "promotable_to_active_rules"
    ] is False
