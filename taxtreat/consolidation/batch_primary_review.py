from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MATRIX = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_review_matrix.json"
)

DEFAULT_WORKSHEET = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_worksheet.json"
)

DEFAULT_DECISIONS = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_primary_review_decisions.json"
)

DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_primary_review_queue.json"
)

REVIEW_OUTCOMES = {
    "accepted_for_independent_approval",
    "returned_for_correction",
}

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

CONFIRMATION_FIELDS = (
    "treaty_rate_candidates_confirmed",
    "beneficial_owner_requirement_confirmed",
    "protocol_effects_confirmed",
    "mli_effects_confirmed",
    "domestic_rate_confirmed",
    "eu_relief_confirmed",
    "effective_date_confirmed",
    "anti_abuse_review_completed",
)


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_timestamp(
    value: Any,
    *,
    packet_id: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Review packet {packet_id} requires reviewed_at."
        )

    try:
        datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError(
            f"Review packet {packet_id} has invalid reviewed_at."
        ) from exc


def _collect_source_ids(value: Any) -> set[str]:
    result: set[str] = set()

    if isinstance(value, dict):
        for key, item in value.items():
            if (
                key.endswith("source_id")
                and isinstance(item, str)
                and item
            ):
                result.add(item)

            elif (
                key.endswith("source_ids")
                and isinstance(item, list)
            ):
                result.update(
                    source_id
                    for source_id in item
                    if isinstance(source_id, str)
                    and source_id
                )

            result.update(_collect_source_ids(item))

    elif isinstance(value, list):
        for item in value:
            result.update(_collect_source_ids(item))

    return result


def _worksheet_index(
    worksheet: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scopes = worksheet.get("scopes", [])

    result = {
        scope["packet_id"]: scope
        for scope in scopes
    }

    if len(result) != 3:
        raise ValueError(
            "Belgium worksheet must contain exactly three scopes."
        )

    return result


def _matrix_index(
    matrix: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = [
        row
        for row in matrix.get("rows", [])
        if row.get("recipient_country") == "BE"
    ]

    result = {
        row["packet_id"]: row
        for row in rows
    }

    if len(result) != 3:
        raise ValueError(
            "Batch 01 matrix must contain exactly three Belgian rows."
        )

    return result


def _decision_index(
    decisions: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for decision in decisions.get("decisions", []):
        packet_id = decision.get("packet_id")

        if not packet_id:
            raise ValueError(
                "Every primary-review decision requires packet_id."
            )

        if packet_id in result:
            raise ValueError(
                f"Duplicate primary-review decision: {packet_id}."
            )

        review_started = any(
            decision.get(field) not in (None, "", [], {})
            for field in (
                "reviewer_id",
                "reviewed_at",
                "review_outcome",
                "supporting_source_ids",
                "reviewer_notes",
                "proposed_rule_snapshot",
            )
        )

        confirmations = decision.get("confirmations")
        if isinstance(confirmations, dict):
            review_started = review_started or any(
                value is not None
                for value in confirmations.values()
            )

        responses = decision.get("question_responses")
        if isinstance(responses, list):
            review_started = review_started or any(
                isinstance(response, dict)
                and (
                    response.get("answer") is not None
                    or response.get("reviewer_note")
                    not in (None, "")
                )
                for response in responses
            )

        if not review_started:
            continue

        result[packet_id] = decision

    return result


def build_decision_template(
    *,
    matrix_path: str | Path = DEFAULT_MATRIX,
    worksheet_path: str | Path = DEFAULT_WORKSHEET,
) -> dict[str, Any]:
    matrix = _matrix_index(read_json(matrix_path))
    worksheet = _worksheet_index(read_json(worksheet_path))

    if set(matrix) != set(worksheet):
        raise ValueError(
            "Belgium worksheet and review matrix packets differ."
        )

    decisions = []

    for packet_id in sorted(matrix):
        row = matrix[packet_id]
        scope = worksheet[packet_id]

        decisions.append(
            {
                "packet_id": packet_id,
                "review_row_sha256": row[
                    "review_row_sha256"
                ],
                "income_type": row["income_type"],
                "reviewer_id": None,
                "reviewed_at": None,
                "review_outcome": None,
                "confirmations": {
                    field: None
                    for field in CONFIRMATION_FIELDS
                },
                "question_responses": [
                    {
                        "question": question,
                        "answer": None,
                        "reviewer_note": None,
                    }
                    for question in scope[
                        "review_questions"
                    ]
                ],
                "supporting_source_ids": [],
                "reviewer_notes": None,
                "proposed_rule_snapshot": None,
            }
        )

    return {
        "schema_version": 1,
        "dataset_release": (
            "batch-01-belgium-primary-review-2026-08-05.1"
        ),
        "country": "BE",
        "policy": {
            "human_review_only": True,
            "independent_approval_required": True,
            "automatic_promotion_prohibited": True,
            "fail_closed": True,
        },
        "decisions": decisions,
    }


def _validate_question_responses(
    decision: dict[str, Any],
    *,
    expected_questions: list[str],
    packet_id: str,
    accepted: bool,
) -> None:
    responses = decision.get("question_responses")

    if not isinstance(responses, list):
        raise ValueError(
            f"Review packet {packet_id} requires "
            "question_responses."
        )

    questions = [
        response.get("question")
        for response in responses
        if isinstance(response, dict)
    ]

    if questions != expected_questions:
        raise ValueError(
            f"Review packet {packet_id} question set differs "
            "from the worksheet."
        )

    for response in responses:
        answer = response.get("answer")
        note = response.get("reviewer_note")

        if answer not in {True, False}:
            raise ValueError(
                f"Review packet {packet_id} requires an answer "
                "to every review question."
            )

        if (
            not isinstance(note, str)
            or not note.strip()
        ):
            raise ValueError(
                f"Review packet {packet_id} requires a note "
                "for every review question."
            )

        if accepted and answer is not True:
            raise ValueError(
                f"Review packet {packet_id} cannot be accepted "
                "while a review question is not confirmed."
            )


def _apply_decision(
    packet: dict[str, Any],
    worksheet_scope: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    packet_id = packet["packet_id"]

    if (
        decision.get("review_row_sha256")
        != packet["review_row_sha256"]
    ):
        raise ValueError(
            f"Review packet {packet_id} is bound to a stale "
            "review-row hash."
        )

    reviewer_id = decision.get("reviewer_id")

    if (
        not isinstance(reviewer_id, str)
        or not reviewer_id.strip()
    ):
        raise ValueError(
            f"Review packet {packet_id} requires reviewer_id."
        )

    _parse_timestamp(
        decision.get("reviewed_at"),
        packet_id=packet_id,
    )

    review_outcome = decision.get("review_outcome")

    if review_outcome not in REVIEW_OUTCOMES:
        raise ValueError(
            f"Review packet {packet_id} has invalid "
            "review_outcome."
        )

    accepted = (
        review_outcome
        == "accepted_for_independent_approval"
    )

    confirmations = decision.get("confirmations")

    if not isinstance(confirmations, dict):
        raise ValueError(
            f"Review packet {packet_id} requires confirmations."
        )

    if set(confirmations) != set(CONFIRMATION_FIELDS):
        raise ValueError(
            f"Review packet {packet_id} has an invalid "
            "confirmation field set."
        )

    if any(
        value not in {True, False}
        for value in confirmations.values()
    ):
        raise ValueError(
            f"Review packet {packet_id} requires every "
            "confirmation to be completed."
        )

    if accepted and not all(confirmations.values()):
        raise ValueError(
            f"Review packet {packet_id} cannot be accepted "
            "with an unconfirmed legal element."
        )

    _validate_question_responses(
        decision,
        expected_questions=worksheet_scope[
            "review_questions"
        ],
        packet_id=packet_id,
        accepted=accepted,
    )

    reviewer_notes = decision.get("reviewer_notes")

    if (
        not isinstance(reviewer_notes, str)
        or not reviewer_notes.strip()
    ):
        raise ValueError(
            f"Review packet {packet_id} requires reviewer_notes."
        )

    supporting_source_ids = decision.get(
        "supporting_source_ids"
    )

    if not isinstance(supporting_source_ids, list):
        raise ValueError(
            f"Review packet {packet_id} supporting_source_ids "
            "must be a list."
        )

    if len(supporting_source_ids) != len(
        set(supporting_source_ids)
    ):
        raise ValueError(
            f"Review packet {packet_id} has duplicate "
            "supporting_source_ids."
        )

    unknown_sources = (
        set(supporting_source_ids)
        - set(packet["available_source_ids"])
    )

    if unknown_sources:
        raise ValueError(
            f"Review packet {packet_id} refers to unknown "
            "supporting sources."
        )

    proposed_rule_snapshot = decision.get(
        "proposed_rule_snapshot"
    )

    if accepted:
        if not supporting_source_ids:
            raise ValueError(
                f"Review packet {packet_id} requires supporting "
                "sources before acceptance."
            )

        if (
            not isinstance(proposed_rule_snapshot, dict)
            or not proposed_rule_snapshot
        ):
            raise ValueError(
                f"Review packet {packet_id} requires a proposed "
                "rule snapshot before acceptance."
            )
    elif proposed_rule_snapshot is not None:
        raise ValueError(
            f"Review packet {packet_id} returned for correction "
            "cannot contain a proposed rule snapshot."
        )

    forbidden_approval_fields = {
        "approver_id",
        "approved_at",
        "approval_outcome",
    }.intersection(decision)

    if forbidden_approval_fields:
        raise ValueError(
            f"Review packet {packet_id} cannot contain "
            "independent-approval fields."
        )

    packet["reviewer_id"] = reviewer_id
    packet["reviewed_at"] = decision["reviewed_at"]
    packet["review_outcome"] = review_outcome
    packet["confirmations"] = confirmations
    packet["question_responses"] = decision[
        "question_responses"
    ]
    packet["supporting_source_ids"] = (
        supporting_source_ids
    )
    packet["reviewer_notes"] = reviewer_notes
    packet["proposed_rule_snapshot"] = (
        proposed_rule_snapshot
    )

    packet["status"] = (
        "awaiting_independent_approval"
        if accepted
        else "returned_for_correction"
    )

    packet["primary_review_completed"] = True
    packet["independent_approval_completed"] = False
    packet["promotable_to_active_rules"] = False


def _packet_sha256(packet: dict[str, Any]) -> str:
    canonical = json.dumps(
        packet,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def build_primary_review_queue(
    *,
    matrix_path: str | Path = DEFAULT_MATRIX,
    worksheet_path: str | Path = DEFAULT_WORKSHEET,
    decisions_path: str | Path = DEFAULT_DECISIONS,
) -> dict[str, Any]:
    matrix = _matrix_index(read_json(matrix_path))
    worksheet = _worksheet_index(read_json(worksheet_path))
    decisions = _decision_index(read_json(decisions_path))

    unknown_decisions = set(decisions) - set(matrix)

    if unknown_decisions:
        raise ValueError(
            "Primary-review decisions contain unknown packets."
        )

    packets = []

    for packet_id in sorted(matrix):
        row = matrix[packet_id]
        worksheet_scope = worksheet[packet_id]

        packet = {
            "packet_id": packet_id,
            "recipient_country": "BE",
            "income_type": row["income_type"],
            "review_row_sha256": row[
                "review_row_sha256"
            ],
            "available_source_ids": sorted(
                _collect_source_ids(row)
                | _collect_source_ids(
                    worksheet_scope
                )
            ),
            "review_questions": worksheet_scope[
                "review_questions"
            ],
            "reviewer_id": None,
            "reviewed_at": None,
            "review_outcome": None,
            "confirmations": None,
            "question_responses": None,
            "supporting_source_ids": [],
            "reviewer_notes": None,
            "proposed_rule_snapshot": None,
            "primary_review_completed": False,
            "independent_approval_completed": False,
            "promotable_to_active_rules": False,
            "status": "awaiting_primary_review",
        }

        decision = decisions.get(packet_id)

        if decision is not None:
            _apply_decision(
                packet,
                worksheet_scope,
                decision,
            )

        packet["primary_review_packet_sha256"] = (
            _packet_sha256(packet)
        )

        packets.append(packet)

    statuses = {
        "awaiting_primary_review": 0,
        "awaiting_independent_approval": 0,
        "returned_for_correction": 0,
    }

    for packet in packets:
        statuses[packet["status"]] += 1

    return {
        "schema_version": 1,
        "dataset_release": (
            "batch-01-belgium-primary-review-queue-"
            "2026-08-05.1"
        ),
        "country": "BE",
        "policy": {
            "human_primary_review_required": True,
            "independent_approval_required": True,
            "automatic_promotion_prohibited": True,
            "fail_closed": True,
        },
        "summary": {
            "total_packets": len(packets),
            **statuses,
            "promotable_packets": 0,
        },
        "packets": packets,
    }


def main() -> None:
    if not DEFAULT_DECISIONS.exists():
        write_json(
            DEFAULT_DECISIONS,
            build_decision_template(),
        )
        print(
            "Created empty Belgium primary-review "
            "decision template."
        )

    payload = build_primary_review_queue()
    write_json(DEFAULT_OUTPUT, payload)

    print("Belgium primary-review queue created.")
    print("Summary:", payload["summary"])


if __name__ == "__main__":
    main()
