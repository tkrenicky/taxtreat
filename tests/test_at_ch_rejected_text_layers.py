import json
from pathlib import Path

ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "at_ch_clean_extraction"
)


def load():
    return json.loads(
        (
            ROOT
            / "at_ch_rejected_text_layers.json"
        ).read_text(encoding="utf-8")
    )


def test_both_text_layers_are_rejected():
    payload = load()

    assert set(payload["countries"]) == {
        "AT",
        "CH",
    }
    assert payload[
        "rejected_text_layer_count"
    ] == 2
    assert payload[
        "accepted_text_layer_count"
    ] == 0

    for country in ("AT", "CH"):
        row = payload["countries"][country]

        assert row["extraction_result"] == (
            "rejected_damaged_pdf_text_layer"
        )
        assert row[
            "suspicious_character_counts"
        ]
        assert row["articles_10_12_found"] == []


def test_rejected_text_cannot_support_rules():
    payload = load()

    for country in ("AT", "CH"):
        row = payload["countries"][country]

        assert row[
            "rejected_output_may_support_active_rule"
        ] is False
        assert row["legal_text_verified"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True
        assert (
            row["promotable_to_active_rules"]
            is False
        )


def test_replacement_requirements_are_strict():
    payload = load()

    for country in ("AT", "CH"):
        requirements = payload["countries"][
            country
        ]["required_replacement_source"]

        assert requirements[
            "official_source_required"
        ] is True
        assert requirements[
            "clean_text_layer_required"
        ] is True
        assert requirements[
            "document_hash_required"
        ] is True
        assert requirements[
            "articles_10_12_comparison_required"
        ] is True
        assert requirements[
            "protocol_overlay_required"
        ] is True
        assert requirements[
            "mli_overlay_required"
        ] is True


def test_old_parsed_files_are_not_authoritative():
    payload = load()

    assert payload[
        "existing_parsed_files_rejected_as_authoritative"
    ] == [
        "data/parsed/rakousko.json",
        "data/parsed/svycarsko.json",
    ]

    assert (
        payload["legal_verification_completed"]
        is False
    )
    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True
