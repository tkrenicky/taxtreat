import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_12_mli_article_8_reservation_verification.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_official_czech_position_is_preserved():
    payload = load()

    source = payload["official_source"]

    pdf_path = ROOT / source["pdf_path"]
    text_path = ROOT / source["text_path"]

    assert pdf_path.exists()
    assert text_path.exists()

    assert pdf_path.read_bytes().startswith(
        b"%PDF"
    )

    assert hashlib.sha256(
        pdf_path.read_bytes()
    ).hexdigest() == source["pdf_sha256"]

    assert hashlib.sha256(
        text_path.read_text(
            encoding="utf-8"
        ).encode("utf-8")
    ).hexdigest() == source["text_sha256"]


def test_article_8_reservation_is_complete():
    payload = load()

    assert payload["mli_treaty_count"] == 12

    assert payload[
        "article_8_verified_count"
    ] == 12

    assert payload[
        "article_8_applies_count"
    ] == 0

    assert payload[
        "article_8_non_application_count"
    ] == 12

    assert payload[
        "czech_entire_article_8_reservation_verified"
    ] is True

    assert payload[
        "verification_summary"
    ]["article_8_matching_complete"] is True


def test_article_8_does_not_modify_any_pair():
    payload = load()

    for record in payload["records"]:
        article = record["article_8"]

        assert article["verified"] is True

        assert article[
            "matching_outcome"
        ] == (
            "does_not_apply_due_to_"
            "czech_entire_article_reservation"
        )

        assert article[
            "minimum_365_day_holding_period_added"
        ] is False

        assert article[
            "partner_position_review_required"
        ] is False

        assert article[
            "legal_basis"
        ]["provision"] == "Article 8(8)"


def test_other_legal_layers_remain_pending():
    payload = load()

    summary = payload[
        "verification_summary"
    ]

    assert summary[
        "mli_entry_into_effect_review_complete"
    ] is False

    assert summary[
        "bilateral_protocol_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
