from __future__ import annotations

import json

from taxtreat.tools.build_legal_evidence_readiness import (
    OUTPUT,
    build_legal_evidence_readiness,
)


def test_readiness_map_covers_all_packets() -> None:
    payload = build_legal_evidence_readiness()

    assert payload["summary"]["total_packets"] == 294
    assert len(payload["packets"]) == 294

    packet_ids = [
        packet["packet_id"]
        for packet in payload["packets"]
    ]

    assert packet_ids == sorted(packet_ids)
    assert len(packet_ids) == len(set(packet_ids))


def test_readiness_remains_fail_closed() -> None:
    payload = build_legal_evidence_readiness()

    assert payload["policy"]["fail_closed"] is True
    assert payload["policy"]["queue_packets_are_not_modified"] is True
    assert payload["summary"]["unique_unresolved_sources"] == 25

    for packet in payload["packets"]:
        assert packet["legal_review_status"] == (
            "awaiting_primary_review"
        )
        assert packet["rule_snapshot_ids"] == []
        assert packet["approval_eligible"] is False
        assert packet["promotable_to_active_rules"] is False


def test_bound_hashes_match_required_sources() -> None:
    payload = build_legal_evidence_readiness()

    for packet in payload["packets"]:
        required = set(packet["required_evidence_source_ids"])
        bound = set(
            packet["verified_evidence_artifact_hashes"]
        )
        unresolved = set(
            packet["unresolved_evidence_source_ids"]
        )
        missing = set(packet["missing_manifest_source_ids"])

        assert bound.isdisjoint(unresolved)
        assert bound.isdisjoint(missing)
        assert unresolved.isdisjoint(missing)
        assert bound | unresolved | missing == required

        for digest in (
            packet["verified_evidence_artifact_hashes"].values()
        ):
            assert len(digest) == 64


def test_readiness_output_is_deterministic() -> None:
    first = build_legal_evidence_readiness()
    first_text = OUTPUT.read_text(encoding="utf-8")

    second = build_legal_evidence_readiness()
    second_text = OUTPUT.read_text(encoding="utf-8")

    assert first == second
    assert first_text == second_text
    assert json.loads(first_text) == first
