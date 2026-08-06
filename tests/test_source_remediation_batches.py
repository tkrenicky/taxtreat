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
        (ROOT / name).read_text(encoding="utf-8")
    )


def test_batches_cover_all_partners():
    payload = load(
        "source_remediation_batches.json"
    )

    rows = [
        row
        for batch in payload["batches"]
        for row in batch["treaty_pairs"]
    ]

    assert payload["treaty_partner_count"] == 98
    assert len(rows) == 98
    assert len({
        row["treaty_pair_id"]
        for row in rows
    }) == 98


def test_priority_order_is_valid():
    payload = load(
        "source_remediation_batches.json"
    )

    priorities = [
        batch["priority"]
        for batch in payload["batches"]
    ]

    assert priorities == sorted(priorities)
    assert priorities[0] == 1


def test_austria_and_switzerland_are_priority_one():
    payload = load(
        "source_remediation_batches.json"
    )

    rows = {
        row["partner_country"]: row
        for batch in payload["batches"]
        for row in batch["treaty_pairs"]
    }

    for country in ("AT", "CH"):
        assert rows[country]["priority"] == 1
        assert rows[country]["batch_type"] == (
            "rejected_ocr_source_replacement"
        )


def test_every_partner_remains_fail_closed():
    payload = load(
        "source_remediation_batches.json"
    )

    for batch in payload["batches"]:
        assert batch["fail_closed"] is True

        for row in batch["treaty_pairs"]:
            assert row["status"] == "not_started"
            assert row["required_actions"]
            assert row["fail_closed"] is True
            assert (
                row["promotable_to_active_rules"]
                is False
            )


def test_completion_criteria_are_strict():
    payload = load(
        "source_remediation_batches.json"
    )

    for batch in payload["batches"]:
        for row in batch["treaty_pairs"]:
            criteria = row["completion_criteria"]

            assert all(
                value is True
                for value in criteria.values()
            )


def test_summary_matches_batches():
    payload = load(
        "source_remediation_batches.json"
    )
    summary = load(
        "source_remediation_batches_summary.json"
    )

    assert summary["treaty_partner_count"] == 98
    assert summary["batch_count"] == len(
        payload["batches"]
    )

    assert sum(
        summary["batch_type_counts"].values()
    ) == 98
