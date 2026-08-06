import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_partner_mli_position_sources.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_partner_positions_are_collected():
    payload = load()

    assert payload[
        "mli_partner_count"
    ] == 12

    assert payload[
        "official_position_pdf_count"
    ] == 12

    assert len(payload["records"]) == 12

    assert len({
        record["treaty_pair_id"]
        for record in payload["records"]
    }) == 12


def test_official_files_and_hashes_match():
    payload = load()

    for record in payload["records"]:
        source = record[
            "official_source"
        ]

        pdf_path = (
            ROOT / source["pdf_path"]
        )

        text_path = (
            ROOT / source["text_path"]
        )

        url_path = (
            ROOT / source["url_path"]
        )

        assert pdf_path.exists()
        assert text_path.exists()
        assert url_path.exists()

        assert pdf_path.read_bytes().startswith(
            b"%PDF"
        )

        assert hashlib.sha256(
            pdf_path.read_bytes()
        ).hexdigest() == source[
            "pdf_sha256"
        ]

        assert hashlib.sha256(
            text_path.read_text(
                encoding="utf-8"
            ).encode("utf-8")
        ).hexdigest() == source[
            "text_sha256"
        ]


def test_collection_is_not_overstated():
    payload = load()

    assert payload["semantics"][
        "source_collection_is_legal_matching"
    ] is False

    assert payload["semantics"][
        "article_35_matching_still_required"
    ] is True

    for record in payload["records"]:
        assert record[
            "entry_into_effect_legally_matched"
        ] is False

        assert record[
            "manual_article_35_comparison_required"
        ] is True


def test_batch_remains_fail_closed():
    payload = load()

    assert payload[
        "mli_entry_into_effect_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
