from __future__ import annotations

from taxtreat.tools.build_legal_review_batch import (
    COUNTRIES,
    build_batch,
)


def test_batch_contains_priority_countries() -> None:
    payload = build_batch()

    assert payload["countries"] == list(COUNTRIES)
    assert payload["summary"]["countries"] == 10
    assert payload["summary"]["packets"] == 30


def test_batch_remains_fail_closed() -> None:
    payload = build_batch()

    assert payload["policy"]["fail_closed"] is True
    assert payload["policy"]["no_automatic_legal_conclusions"] is True

    for packet in payload["packets"]:
        assert packet["status"] == "awaiting_primary_review"
        assert packet["proposed_conclusion"] is None
        assert packet["reviewer_id"] is None
        assert packet["rule_snapshot_ids"] == []
        assert packet["promotable_to_active_rules"] is False


def test_all_evidence_is_bound() -> None:
    payload = build_batch()

    for packet in payload["packets"]:
        assert packet["evidence"]

        for evidence in packet["evidence"]:
            assert evidence["source_id"]
            assert evidence["sha256"]
            assert len(evidence["sha256"]) == 64
            assert evidence["artifact_status"] in {
                "existing_verified_artifact",
                "verified_pdf",
                "verified_html",
            }


def test_review_checklist_is_complete() -> None:
    payload = build_batch()

    for packet in payload["packets"]:
        assert len(packet["review_checklist"]) == 12
        assert all(
            item["status"] == "pending"
            for item in packet["review_checklist"]
        )
