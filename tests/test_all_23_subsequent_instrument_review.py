import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_subsequent_instrument_review.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_23_pairs_are_included():
    payload = load()

    assert payload[
        "treaty_pair_count"
    ] == 23

    assert len(
        payload["records"]
    ) == 23

    assert len({
        record["treaty_pair_id"]
        for record in payload["records"]
    }) == 23


def test_mf_sources_are_locally_preserved():
    payload = load()

    for record in payload["records"]:
        for document in record[
            "official_mf_documents"
        ]:
            html_path = (
                ROOT
                / document["html_path"]
            )

            text_path = (
                ROOT
                / document["text_path"]
            )

            url_path = (
                ROOT
                / document["url_path"]
            )

            assert html_path.exists()
            assert text_path.exists()
            assert url_path.exists()

            assert hashlib.sha256(
                html_path.read_bytes()
            ).hexdigest() == document[
                "html_sha256"
            ]

            assert hashlib.sha256(
                text_path.read_bytes()
            ).hexdigest() == document[
                "text_sha256"
            ]


def test_protocol_detection_is_not_overstated():
    payload = load()

    semantics = payload[
        "semantics"
    ]

    assert semantics[
        "protocol_keyword_is_not_legal_conclusion"
    ] is True

    assert semantics[
        "absence_from_mf_web_is_not_proof_of_absence"
    ] is True

    assert semantics[
        "each_detected_instrument_requires_comparison"
    ] is True

    for record in payload["records"]:
        assert record[
            "absence_of_protocol_proven"
        ] is False

        assert record[
            "subsequent_instrument_review_complete"
        ] is False

        assert record[
            "rates_confirmed_after_subsequent_instruments"
        ] is False


def test_inventory_remains_fail_closed():
    payload = load()

    assert payload[
        "subsequent_instrument_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload[
        "production_ready"
    ] is False

    assert payload[
        "fail_closed"
    ] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
