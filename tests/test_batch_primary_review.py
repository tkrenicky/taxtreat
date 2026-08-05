from __future__ import annotations

import json
from pathlib import Path

import pytest

from taxtreat.consolidation.batch_primary_review import (
    build_decision_template,
    build_primary_review_queue,
    read_json,
    write_json,
)


def _write_decisions(
    tmp_path: Path,
    decisions: list[dict],
) -> Path:
    target = tmp_path / "decisions.json"
    target.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decisions": decisions,
            }
        ),
        encoding="utf-8",
    )
    return target


def _completed_decision(
    template_decision: dict,
    *,
    outcome: str = (
        "accepted_for_independent_approval"
    ),
) -> dict:
    accepted = (
        outcome
        == "accepted_for_independent_approval"
    )

    decision = {
        **template_decision,
        "reviewer_id": "primary-reviewer-1",
        "reviewed_at": "2026-08-05T20:00:00Z",
        "review_outcome": outcome,
        "confirmations": {
            key: accepted
            for key in template_decision[
                "confirmations"
            ]
        },
        "question_responses": [
            {
                **response,
                "answer": accepted,
                "reviewer_note": "Reviewed manually.",
            }
            for response in template_decision[
                "question_responses"
            ]
        ],
        "supporting_source_ids": [],
        "reviewer_notes": "Primary legal review completed.",
        "proposed_rule_snapshot": None,
    }

    return decision


def test_empty_template_covers_three_belgian_scopes():
    payload = build_decision_template()

    assert payload["country"] == "BE"
    assert len(payload["decisions"]) == 3
    assert {
        decision["income_type"]
        for decision in payload["decisions"]
    } == {"dividend", "interest", "royalty"}

    assert all(
        decision["review_outcome"] is None
        and decision["reviewer_id"] is None
        for decision in payload["decisions"]
    )


def test_empty_queue_remains_fail_closed(tmp_path):
    decisions_path = _write_decisions(
        tmp_path,
        [],
    )

    payload = build_primary_review_queue(
        decisions_path=decisions_path
    )

    assert payload["summary"] == {
        "total_packets": 3,
        "awaiting_primary_review": 3,
        "awaiting_independent_approval": 0,
        "returned_for_correction": 0,
        "promotable_packets": 0,
    }

    assert all(
        packet["promotable_to_active_rules"] is False
        for packet in payload["packets"]
    )


def test_accepted_review_requires_all_answers_and_sources(
    tmp_path,
):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0]
    )

    decisions_path = _write_decisions(
        tmp_path,
        [decision],
    )

    with pytest.raises(
        ValueError,
        match="requires supporting sources",
    ):
        build_primary_review_queue(
            decisions_path=decisions_path
        )


def test_accepted_review_moves_only_to_independent_review(
    tmp_path,
):
    empty = build_primary_review_queue(
        decisions_path=_write_decisions(
            tmp_path,
            [],
        )
    )

    packet = empty["packets"][0]
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0]
    )

    decision["supporting_source_ids"] = [
        packet["available_source_ids"][0]
    ]
    decision["proposed_rule_snapshot"] = {
        "snapshot_id": "CZ-BE-PRIMARY-CANDIDATE-1",
        "candidate_only": True,
    }

    payload = build_primary_review_queue(
        decisions_path=_write_decisions(
            tmp_path,
            [decision],
        )
    )

    reviewed = payload["packets"][0]

    assert (
        reviewed["status"]
        == "awaiting_independent_approval"
    )
    assert reviewed["primary_review_completed"] is True
    assert (
        reviewed["independent_approval_completed"]
        is False
    )
    assert (
        reviewed["promotable_to_active_rules"]
        is False
    )


def test_returned_packet_remains_fail_closed(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )

    payload = build_primary_review_queue(
        decisions_path=_write_decisions(
            tmp_path,
            [decision],
        )
    )

    reviewed = payload["packets"][0]

    assert reviewed["status"] == "returned_for_correction"
    assert reviewed["promotable_to_active_rules"] is False


def test_stale_review_hash_is_rejected(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["review_row_sha256"] = "0" * 64

    with pytest.raises(
        ValueError,
        match="stale review-row hash",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_unknown_supporting_source_is_rejected(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0]
    )
    decision["supporting_source_ids"] = [
        "UNKNOWN-SOURCE"
    ]
    decision["proposed_rule_snapshot"] = {
        "candidate_only": True
    }

    with pytest.raises(
        ValueError,
        match="unknown supporting sources",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_primary_review_cannot_include_approval(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["approver_id"] = "approver-1"

    with pytest.raises(
        ValueError,
        match="cannot contain independent-approval",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_unfilled_decision_template_remains_awaiting_review(
    tmp_path,
):
    template = build_decision_template()

    payload = build_primary_review_queue(
        decisions_path=_write_decisions(
            tmp_path,
            template["decisions"],
        )
    )

    assert payload["summary"] == {
        "total_packets": 3,
        "awaiting_primary_review": 3,
        "awaiting_independent_approval": 0,
        "returned_for_correction": 0,
        "promotable_packets": 0,
    }


def test_partially_started_review_requires_reviewer(tmp_path):
    template = build_decision_template()
    decision = {
        **template["decisions"][0],
        "reviewed_at": "2026-08-05T20:00:00Z",
    }

    with pytest.raises(
        ValueError,
        match="requires reviewer_id",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_invalid_review_timestamp_is_rejected(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["reviewed_at"] = "not-a-date"

    with pytest.raises(
        ValueError,
        match="invalid reviewed_at",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_duplicate_decisions_are_rejected(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate primary-review decision",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision, decision],
            )
        )


def test_unknown_packet_is_rejected(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["packet_id"] = "CZ-BE-UNKNOWN"

    with pytest.raises(
        ValueError,
        match="unknown packets",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_acceptance_requires_all_confirmations(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0]
    )

    first_field = next(iter(decision["confirmations"]))
    decision["confirmations"][first_field] = False

    with pytest.raises(
        ValueError,
        match="unconfirmed legal element",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_duplicate_supporting_sources_are_rejected(
    tmp_path,
):
    empty = build_primary_review_queue(
        decisions_path=_write_decisions(
            tmp_path,
            [],
        )
    )
    source_id = empty["packets"][0][
        "available_source_ids"
    ][0]

    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0]
    )
    decision["supporting_source_ids"] = [
        source_id,
        source_id,
    ]
    decision["proposed_rule_snapshot"] = {
        "candidate_only": True,
    }

    with pytest.raises(
        ValueError,
        match="duplicate supporting_source_ids",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_returned_review_cannot_include_snapshot(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["proposed_rule_snapshot"] = {
        "candidate_only": True,
    }

    with pytest.raises(
        ValueError,
        match="cannot contain a proposed rule snapshot",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_json_helpers_round_trip(tmp_path):
    target = tmp_path / "nested" / "payload.json"
    payload = {
        "schema_version": 1,
        "country": "BE",
    }

    write_json(target, payload)

    assert target.is_file()
    assert read_json(target) == payload


def test_decision_without_packet_id_is_rejected(tmp_path):
    decision = {
        "reviewer_id": "reviewer-1",
        "reviewed_at": "2026-08-05T20:00:00Z",
        "review_outcome": "returned_for_correction",
    }

    with pytest.raises(
        ValueError,
        match="requires packet_id",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_confirmation_payload_must_be_object(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["confirmations"] = []

    with pytest.raises(
        ValueError,
        match="requires confirmations",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_confirmation_field_set_is_strict(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["confirmations"].pop(
        next(iter(decision["confirmations"]))
    )

    with pytest.raises(
        ValueError,
        match="invalid confirmation field set",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_every_confirmation_requires_boolean(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    first_field = next(iter(decision["confirmations"]))
    decision["confirmations"][first_field] = None

    with pytest.raises(
        ValueError,
        match="requires every confirmation",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_question_responses_must_be_list(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["question_responses"] = {}

    with pytest.raises(
        ValueError,
        match="requires question_responses",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_question_set_must_match_worksheet(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["question_responses"][0]["question"] = (
        "Altered question"
    )

    with pytest.raises(
        ValueError,
        match="question set differs",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_every_question_requires_boolean_answer(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["question_responses"][0]["answer"] = None

    with pytest.raises(
        ValueError,
        match="requires an answer",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_every_question_requires_note(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["question_responses"][0][
        "reviewer_note"
    ] = None

    with pytest.raises(
        ValueError,
        match="requires a note",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_accepted_review_requires_positive_answers(
    tmp_path,
):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0]
    )
    decision["question_responses"][0]["answer"] = False

    with pytest.raises(
        ValueError,
        match="review question is not confirmed",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_reviewer_notes_are_required(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["reviewer_notes"] = None

    with pytest.raises(
        ValueError,
        match="requires reviewer_notes",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )


def test_supporting_sources_must_be_list(tmp_path):
    template = build_decision_template()
    decision = _completed_decision(
        template["decisions"][0],
        outcome="returned_for_correction",
    )
    decision["supporting_source_ids"] = {}

    with pytest.raises(
        ValueError,
        match="must be a list",
    ):
        build_primary_review_queue(
            decisions_path=_write_decisions(
                tmp_path,
                [decision],
            )
        )
