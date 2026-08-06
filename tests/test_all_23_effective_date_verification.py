import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_effective_date_verification.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_entry_into_force_dates_are_verified():
    payload = load()

    assert payload["treaty_partner_count"] == 23

    assert payload[
        "verified_entry_into_force_count"
    ] == 23

    assert payload[
        "verification_summary"
    ]["entry_into_force_complete"] is True

    for record in payload["records"]:
        assert record[
            "entry_into_force_verified"
        ] is True

        date.fromisoformat(
            record["entry_into_force_date"]
        )

        assert record["official_publication"]

        assert record[
            "entry_into_force_verification_status"
        ] == (
            "verified_against_mf_treaty_overview"
        )


def test_fourteen_withholding_dates_are_verified():
    payload = load()

    assert payload[
        "verified_czech_withholding_date_count"
    ] == 14

    assert payload[
        "pending_czech_withholding_date_count"
    ] == 9

    for record in payload["records"]:
        if record[
            "czech_withholding_effective_date_verified"
        ]:
            entry = date.fromisoformat(
                record["entry_into_force_date"]
            )

            effective = date.fromisoformat(
                record[
                    "czech_withholding_effective_from"
                ]
            )

            assert effective == date(
                entry.year + 1,
                1,
                1,
            )


def test_unresolved_withholding_dates_are_not_invented():
    payload = load()

    pending = {
        record["treaty_pair_id"]
        for record in payload["records"]
        if not record[
            "czech_withholding_effective_date_verified"
        ]
    }

    assert pending == set(
        payload[
            "pending_czech_withholding_pairs"
        ]
    )

    assert len(pending) == 9

    for record in payload["records"]:
        if record["treaty_pair_id"] in pending:
            assert record[
                "czech_withholding_effective_from"
            ] is None


def test_batch_remains_fail_closed():
    payload = load()

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False

    for record in payload["records"]:
        assert record[
            "transaction_decision_ready"
        ] is False

        assert record["production_ready"] is False
        assert record["fail_closed"] is True
