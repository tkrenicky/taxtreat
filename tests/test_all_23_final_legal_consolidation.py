import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_final_legal_consolidation.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_country_level_legal_review_is_complete():
    payload = load()

    assert payload["treaty_pair_count"] == 23

    assert payload[
        "country_level_legal_review_complete_count"
    ] == 23

    assert len(payload["records"]) == 23

    assert payload[
        "country_level_legal_verification_completed"
    ] is True


def test_belarus_protocol_overlay_is_recorded():
    payload = load()

    record = next(
        item
        for item in payload["records"]
        if item["treaty_pair_id"] == "CZ-BY"
    )

    protocol = record["protocol_conclusion"]

    assert protocol[
        "effective_from"
    ] == "2012-01-01"

    assert protocol[
        "articles_10_12_affected"
    ] is True

    assert protocol[
        "royalty_max_rate_percent"
    ] == 5.0

    assert protocol[
        "interest_special_exemptions_added"
    ] is True


def test_serbia_protocol_does_not_change_wht_rates():
    payload = load()

    record = next(
        item
        for item in payload["records"]
        if item["treaty_pair_id"] == "CZ-RS"
    )

    protocol = record["protocol_conclusion"]

    assert protocol[
        "effective_from"
    ] == "2012-01-01"

    assert protocol[
        "articles_10_12_affected"
    ] is False

    assert protocol[
        "conclusion"
    ] == "no_wht_rate_change"


def test_russia_is_hard_blocked_from_suspension():
    payload = load()

    record = next(
        item
        for item in payload["records"]
        if item["treaty_pair_id"] == "CZ-RU"
    )

    protocol = record["protocol_conclusion"]

    assert protocol[
        "suspension_effective_from"
    ] == "2023-08-11"

    assert 10 in protocol[
        "treaty_articles_suspended"
    ]

    assert 11 in protocol[
        "treaty_articles_suspended"
    ]

    assert 12 in protocol[
        "treaty_articles_suspended"
    ]

    assert record[
        "treaty_available_currently"
    ] is False

    assert record[
        "production_rule_status"
    ] == "hard_block_required"


def test_domestic_transaction_gates_remain_fail_closed():
    payload = load()

    gates = payload[
        "domestic_wht_gate_model"
    ]

    assert gates[
        "missing_input_outcome"
    ] == (
        "fail_closed_no_reduced_rate_or_exemption"
    )

    for record in payload["records"]:
        assert record[
            "domestic_wht_gate_model_complete"
        ] is True

        assert record[
            "transaction_level_inputs_still_required"
        ] is True

        assert record[
            "automatic_rate_without_inputs_allowed"
        ] is False

        assert record["fail_closed"] is True


def test_no_country_level_legal_prompts_remain():
    payload = load()

    assert payload[
        "protocol_review"
    ]["complete"] is True

    assert payload[
        "legal_review_semantics"
    ][
        "country_level_legal_review_complete"
    ] is True

    assert payload[
        "runtime_transaction_gate_required"
    ] is True

    assert payload[
        "automatic_unconditional_rate_allowed"
    ] is False
