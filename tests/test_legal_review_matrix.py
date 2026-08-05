from __future__ import annotations

from taxtreat.tools.build_legal_review_matrix import (
    build_matrix,
)


def test_matrix_contains_all_batch_packets() -> None:
    payload = build_matrix()

    assert payload["summary"]["rows"] == 30
    assert payload["summary"]["countries"] == 10
    assert len(payload["rows"]) == 30


def test_matrix_contains_candidate_data() -> None:
    payload = build_matrix()

    for row in payload["rows"]:
        assert row["base_treaty"]["publication"]
        assert row["base_treaty"]["source_id"]
        assert row["base_treaty"]["article_number"] in {
            10,
            11,
            12,
        }
        assert row["domestic_and_eu"][
            "domestic_rate_candidate"
        ]


def test_matrix_remains_fail_closed() -> None:
    payload = build_matrix()

    assert payload["policy"]["candidate_data_only"] is True
    assert payload["policy"]["fail_closed"] is True

    for row in payload["rows"]:
        assert row["status"] == "awaiting_primary_review"
        assert row["approval_eligible"] is False
        assert row["promotable_to_active_rules"] is False
        assert row["review"]["reviewer_id"] is None
        assert row["review"]["review_outcome"] is None
        assert row["review"][
            "proposed_rule_snapshot"
        ] is None


def test_rates_are_candidate_values_only() -> None:
    payload = build_matrix()

    for row in payload["rows"]:
        assert row["base_treaty"][
            "verification_status"
        ] == "needs_review"

        assert row["domestic_and_eu"][
            "verification_status"
        ] == "needs_review"
