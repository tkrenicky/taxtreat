import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_authoritative_subsequent_instrument_inventory.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_23_pairs_are_authoritatively_inventoried():
    payload = load()

    assert payload[
        "treaty_pair_count"
    ] == 23

    assert payload[
        "authoritative_inventory_complete_count"
    ] == 23

    assert len(
        payload["records"]
    ) == 23

    assert len({
        record["treaty_pair_id"]
        for record in payload["records"]
    }) == 23

    for record in payload["records"]:
        assert record[
            "authoritative_inventory_complete"
        ] is True


def test_official_mf_snapshot_is_preserved():
    payload = load()
    source = payload["source"]

    html_path = (
        ROOT / source["html_path"]
    )

    text_path = (
        ROOT / source["text_path"]
    )

    url_path = (
        ROOT / source["url_path"]
    )

    assert html_path.is_file()
    assert text_path.is_file()
    assert url_path.is_file()

    assert hashlib.sha256(
        html_path.read_bytes()
    ).hexdigest() == source[
        "html_sha256"
    ]

    assert hashlib.sha256(
        text_path.read_bytes()
    ).hexdigest() == source[
        "text_sha256"
    ]


def test_protocol_pairs_remain_fail_closed():
    payload = load()

    for record in payload["records"]:
        if record[
            "protocol_reference_detected"
        ]:
            assert record[
                "protocol_text_comparison_complete"
            ] is False

            assert record[
                "protocol_rate_effect_confirmed"
            ] is False

        assert record[
            "production_ready"
        ] is False

        assert record[
            "fail_closed"
        ] is True


def test_final_legal_layer_remains_open():
    payload = load()

    assert payload[
        "authoritative_subsequent_instrument_inventory_complete"
    ] is True

    assert payload[
        "domestic_conditions_review_complete"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload[
        "production_ready"
    ] is False

    assert payload[
        "promotable_to_active_rules"
    ] is False
