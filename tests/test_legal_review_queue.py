from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from taxtreat.consolidation.legal_review_queue import (
    build_legal_review_queue,
    write_legal_review_queue,
)


ROOT = Path(__file__).parents[1]
DATASET = ROOT / "data" / "legal_reviews" / "remaining_294_review_queue.json"
DECISIONS = ROOT / "data" / "legal_reviews" / "remaining_294_decisions.json"


def _payload():
    return json.loads(DATASET.read_text(encoding="utf-8"))


def _decision_file(tmp_path, decision):
    target = tmp_path / "decisions.json"
    target.write_text(
        json.dumps({"schema_version": 1, "decisions": [decision]}),
        encoding="utf-8",
    )
    return target


def _first_packet():
    return build_legal_review_queue()["packets"][0]


def _accepted_decision(packet):
    return {
        "packet_id": packet["packet_id"],
        "candidate_sha256": packet["candidate_sha256"],
        "reviewer_id": "reviewer-a",
        "reviewed_at": "2026-08-04T10:00:00Z",
        "review_outcome": "accepted_for_independent_approval",
    }


def test_review_queue_covers_every_non_pilot_scope_without_approval():
    payload = _payload()
    packets = payload["packets"]

    assert len(packets) == 294
    assert len({packet["packet_id"] for packet in packets}) == 294
    assert len({packet["recipient_country"] for packet in packets}) == 98
    assert {packet["recipient_country"] for packet in packets}.isdisjoint(
        {"AT", "CH"}
    )
    assert payload["summary"] == {
        "approval_eligible_packets": 0,
        "awaiting_independent_approval": 0,
        "awaiting_primary_review": 294,
        "independently_approved": 0,
        "primary_review_complete_missing_approval_prerequisites": 0,
        "promotable_packets": 0,
        "rejected": 0,
        "returned_for_correction": 0,
        "total_packets": 294,
        "verified_packets": 0,
    }
    assert all(
        packet["verification_status"] == "needs_review"
        and packet["packet_status"] == "awaiting_primary_review"
        and packet["approval_eligible"] is False
        and packet["promotable_to_active_rules"] is False
        and packet["reviewer_id"] is None
        and packet["approver_id"] is None
        for packet in packets
    )


def test_review_packet_keeps_candidate_binding_tasks_and_evidence_explicit():
    germany = next(
        packet
        for packet in _payload()["packets"]
        if packet["recipient_country"] == "DE"
        and packet["income_type"] == "dividend"
    )

    assert len(germany["candidate_sha256"]) == 64
    assert germany["separation_of_duties_required"] is True
    assert germany["source_artifacts_verified"] is False
    assert germany["rule_snapshot_ids"] == []
    assert {
        "CZ-ZDP-2026-04-01-OPEN-DATA",
        "EU-PSD-2011-96-CONSOLIDATED",
    }.issubset(germany["evidence_source_ids"])
    assert {
        check["check_id"] for check in germany["review_tasks"]
    }.issuperset(
        {
            "base_treaty_candidate_review",
            "domestic_rate_candidate_review",
            "independent_legal_review",
            "mli_wht_effect_candidate_review",
            "relief_candidate_review",
        }
    )
    assert all(check["status"] == "pending" for check in germany["review_tasks"])


def test_packet_hashes_and_generation_are_deterministic():
    payload = _payload()
    for packet in payload["packets"]:
        expected = packet.pop("review_packet_sha256")
        actual = hashlib.sha256(
            json.dumps(packet, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        assert actual == expected

    assert build_legal_review_queue() == _payload()


def test_primary_review_does_not_approve_without_artifacts_and_rules(tmp_path):
    packet = _first_packet()
    decision = {
        "packet_id": packet["packet_id"],
        "candidate_sha256": packet["candidate_sha256"],
        "reviewer_id": "reviewer-a",
        "reviewed_at": "2026-08-04T10:00:00Z",
        "review_outcome": "accepted_for_independent_approval",
    }

    payload = build_legal_review_queue(
        decisions_path=_decision_file(tmp_path, decision)
    )
    reviewed = payload["packets"][0]

    assert reviewed["packet_status"] == (
        "primary_review_complete_missing_approval_prerequisites"
    )
    assert reviewed["verification_status"] == "needs_review"
    assert reviewed["approval_eligible"] is False
    assert reviewed["promotable_to_active_rules"] is False


def test_independent_approval_requires_exact_candidate_and_all_prerequisites(
    tmp_path,
):
    packet = _first_packet()
    base = {
        "packet_id": packet["packet_id"],
        "candidate_sha256": packet["candidate_sha256"],
        "reviewer_id": "reviewer-a",
        "reviewed_at": "2026-08-04T10:00:00Z",
        "review_outcome": "accepted_for_independent_approval",
        "approver_id": "approver-b",
        "approved_at": "2026-08-04T11:00:00Z",
        "approval_outcome": "approved",
    }

    with pytest.raises(ValueError, match="before rule snapshots"):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, base)
        )

    stale = {**base, "candidate_sha256": "0" * 64}
    with pytest.raises(ValueError, match="stale candidate hash"):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, stale)
        )


def test_complete_independent_approval_is_the_only_promotable_path(tmp_path):
    packet = _first_packet()
    decision = {
        "packet_id": packet["packet_id"],
        "candidate_sha256": packet["candidate_sha256"],
        "reviewer_id": "reviewer-a",
        "reviewed_at": "2026-08-04T10:00:00Z",
        "review_outcome": "accepted_for_independent_approval",
        "rule_snapshot_ids": ["CZ-AD-DIV-SNAPSHOT-1"],
        "evidence_artifact_hashes": {
            source_id: "a" * 64 for source_id in packet["evidence_source_ids"]
        },
        "approver_id": "approver-b",
        "approved_at": "2026-08-04T11:00:00Z",
        "approval_outcome": "approved",
    }

    payload = build_legal_review_queue(
        decisions_path=_decision_file(tmp_path, decision)
    )
    approved = payload["packets"][0]

    assert approved["packet_status"] == "independently_approved"
    assert approved["verification_status"] == "verified"
    assert approved["approval_eligible"] is True
    assert approved["promotable_to_active_rules"] is True
    assert payload["summary"]["independently_approved"] == 1
    assert payload["summary"]["promotable_packets"] == 1


def test_same_person_cannot_review_and_approve(tmp_path):
    packet = _first_packet()
    decision = {
        "packet_id": packet["packet_id"],
        "candidate_sha256": packet["candidate_sha256"],
        "reviewer_id": "same-person",
        "reviewed_at": "2026-08-04T10:00:00Z",
        "review_outcome": "accepted_for_independent_approval",
        "rule_snapshot_ids": ["CZ-AD-DIV-SNAPSHOT-1"],
        "evidence_artifact_hashes": {
            source_id: "a" * 64 for source_id in packet["evidence_source_ids"]
        },
        "approver_id": "same-person",
        "approved_at": "2026-08-04T11:00:00Z",
        "approval_outcome": "approved",
    }

    with pytest.raises(ValueError, match="must be independent"):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, decision)
        )


def test_builder_rejects_incomplete_or_duplicate_inputs(tmp_path):
    chains = json.loads(
        (
            ROOT
            / "data"
            / "legal_consolidation"
            / "remaining_294_instrument_chains.json"
        ).read_text(encoding="utf-8")
    )
    chains["scopes"].pop()
    missing = tmp_path / "missing.json"
    missing.write_text(json.dumps(chains), encoding="utf-8")
    with pytest.raises(ValueError, match="Expected 294"):
        build_legal_review_queue(chains_path=missing)

    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    packet = _first_packet()
    decision = {
        "packet_id": packet["packet_id"],
        "candidate_sha256": packet["candidate_sha256"],
        "reviewer_id": "reviewer-a",
        "reviewed_at": "2026-08-04T10:00:00Z",
        "review_outcome": "returned_for_correction",
    }
    decisions["decisions"] = [decision, decision]
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(json.dumps(decisions), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate legal-review decision"):
        build_legal_review_queue(decisions_path=duplicate)


def test_writer_round_trip(tmp_path):
    target = tmp_path / "nested" / "review-queue.json"
    payload = build_legal_review_queue()
    write_legal_review_queue(payload, target)

    assert json.loads(target.read_text(encoding="utf-8")) == payload


@pytest.mark.parametrize(
    ("updates", "match"),
    [
        ({"reviewer_id": None}, "requires reviewer_id"),
        ({"reviewed_at": None}, "requires reviewed_at"),
        ({"reviewed_at": "not-a-date"}, "invalid reviewed_at"),
        ({"review_outcome": "invalid"}, "invalid review_outcome"),
        ({"rule_snapshot_ids": ["A", "A"]}, "duplicate rule_snapshot_ids"),
        ({"evidence_artifact_hashes": []}, "must be an object"),
        ({"evidence_artifact_hashes": {"SRC": "short"}}, "invalid evidence"),
        ({"approver_id": "approver-b"}, "incomplete approval fields"),
        (
            {
                "rule_snapshot_ids": ["RULE"],
                "evidence_artifact_hashes": {},
                "approval_outcome": "invalid",
            },
            "invalid approval_outcome",
        ),
    ],
)
def test_invalid_primary_review_records_fail_closed(tmp_path, updates, match):
    packet = _first_packet()
    decision = {**_accepted_decision(packet), **updates}

    with pytest.raises(ValueError, match=match):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, decision)
        )


def test_return_for_correction_is_recorded_without_approval(tmp_path):
    packet = _first_packet()
    decision = {
        **_accepted_decision(packet),
        "review_outcome": "returned_for_correction",
    }
    payload = build_legal_review_queue(
        decisions_path=_decision_file(tmp_path, decision)
    )

    assert payload["packets"][0]["packet_status"] == "returned_for_correction"
    assert payload["summary"]["returned_for_correction"] == 1

    decision["approver_id"] = "approver-b"
    with pytest.raises(ValueError, match="cannot carry approval fields"):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, decision)
        )


def test_complete_prerequisites_wait_for_independent_approval(tmp_path):
    packet = _first_packet()
    decision = {
        **_accepted_decision(packet),
        "rule_snapshot_ids": ["RULE"],
        "evidence_artifact_hashes": {
            source_id: "a" * 64 for source_id in packet["evidence_source_ids"]
        },
    }
    payload = build_legal_review_queue(
        decisions_path=_decision_file(tmp_path, decision)
    )

    assert payload["packets"][0]["packet_status"] == (
        "awaiting_independent_approval"
    )
    assert payload["summary"]["approval_eligible_packets"] == 1
    assert payload["summary"]["awaiting_independent_approval"] == 1


@pytest.mark.parametrize(
    ("updates", "match"),
    [
        ({"approver_id": None}, "requires approver_id"),
        ({"approved_at": None}, "requires approved_at"),
        ({"approved_at": "not-a-date"}, "invalid approved_at"),
    ],
)
def test_invalid_independent_approval_records_fail_closed(
    tmp_path,
    updates,
    match,
):
    packet = _first_packet()
    decision = {
        **_accepted_decision(packet),
        "rule_snapshot_ids": ["RULE"],
        "evidence_artifact_hashes": {
            source_id: "a" * 64 for source_id in packet["evidence_source_ids"]
        },
        "approver_id": "approver-b",
        "approved_at": "2026-08-04T11:00:00Z",
        "approval_outcome": "approved",
        **updates,
    }

    with pytest.raises(ValueError, match=match):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, decision)
        )


def test_independent_approver_can_reject_packet(tmp_path):
    packet = _first_packet()
    decision = {
        **_accepted_decision(packet),
        "rule_snapshot_ids": ["RULE"],
        "evidence_artifact_hashes": {
            source_id: "a" * 64 for source_id in packet["evidence_source_ids"]
        },
        "approver_id": "approver-b",
        "approved_at": "2026-08-04T11:00:00Z",
        "approval_outcome": "rejected",
    }
    payload = build_legal_review_queue(
        decisions_path=_decision_file(tmp_path, decision)
    )

    assert payload["packets"][0]["packet_status"] == "rejected"
    assert payload["packets"][0]["verification_status"] == "needs_review"
    assert payload["summary"]["rejected"] == 1


def test_builder_rejects_unknown_decision_and_missing_packet_id(tmp_path):
    packet = _first_packet()
    decision = {
        **_accepted_decision(packet),
        "packet_id": "CZ-ZZ-DIV-LEGAL-REVIEW",
    }
    with pytest.raises(ValueError, match="unknown packets"):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, decision)
        )

    decision.pop("packet_id")
    with pytest.raises(ValueError, match="requires packet_id"):
        build_legal_review_queue(
            decisions_path=_decision_file(tmp_path, decision)
        )


def test_builder_rejects_duplicate_and_non_fail_closed_chain_scopes(tmp_path):
    source_path = (
        ROOT
        / "data"
        / "legal_consolidation"
        / "remaining_294_instrument_chains.json"
    )
    chains = json.loads(source_path.read_text(encoding="utf-8"))
    chains["scopes"][-1] = chains["scopes"][0]
    duplicate = tmp_path / "duplicate-scopes.json"
    duplicate.write_text(json.dumps(chains), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate instrument-chain"):
        build_legal_review_queue(chains_path=duplicate)

    chains = json.loads(source_path.read_text(encoding="utf-8"))
    chains["scopes"][0]["candidate_chain_complete"] = False
    incomplete = tmp_path / "incomplete.json"
    incomplete.write_text(json.dumps(chains), encoding="utf-8")
    with pytest.raises(ValueError, match="not a complete fail-closed"):
        build_legal_review_queue(chains_path=incomplete)


def test_builder_rejects_domestic_scope_drift_and_unsupported_income(tmp_path):
    domestic_path = (
        ROOT
        / "data"
        / "legal_consolidation"
        / "cz_domestic_eu_candidates.json"
    )
    domestic = json.loads(domestic_path.read_text(encoding="utf-8"))
    domestic["scopes"][-1]["recipient_country"] = "ZZ"
    drift = tmp_path / "domestic-drift.json"
    drift.write_text(json.dumps(domestic), encoding="utf-8")
    with pytest.raises(ValueError, match="missing from domestic/EU"):
        build_legal_review_queue(domestic_eu_path=drift)

    chains_path = (
        ROOT
        / "data"
        / "legal_consolidation"
        / "remaining_294_instrument_chains.json"
    )
    chains = json.loads(chains_path.read_text(encoding="utf-8"))
    chains["scopes"][0]["income_type"] = "service"
    unsupported = tmp_path / "unsupported.json"
    unsupported.write_text(json.dumps(chains), encoding="utf-8")
    domestic = json.loads(domestic_path.read_text(encoding="utf-8"))
    matching = next(
        row
        for row in domestic["scopes"]
        if row["recipient_country"] == "AD"
        and row["income_type"] == "dividend"
    )
    matching["income_type"] = "service"
    unsupported_domestic = tmp_path / "unsupported-domestic.json"
    unsupported_domestic.write_text(json.dumps(domestic), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported review income type"):
        build_legal_review_queue(
            chains_path=unsupported,
            domestic_eu_path=unsupported_domestic,
        )
