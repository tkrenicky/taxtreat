import copy
import json
from pathlib import Path

import pytest

from taxtreat.engine.source_release_gate_v2 import (
    CanonicalSourceGateError,
    CanonicalSourceNotReleasedError,
    get_canonical_source_release,
    load_canonical_source_release_gate,
    require_canonical_released_source,
)


ROOT = Path(__file__).parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

GATE_PATH = (
    BASE
    / "production_source_release_gate_v2.json"
)

REVIEW_PATH = (
    BASE
    / "stage5_human_review_completion.json"
)


REMEDIATION_PATH = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "semantic_remediation_condition_candidates_20260829.json"
)


def _remediation_pairs():
    payload = json.loads(REMEDIATION_PATH.read_text(encoding="utf-8"))
    return {
        f"CZ-{row['country']}"
        for row in payload["corrections"]
    }


def test_canonical_gate_matches_101_303_reviewed_universe():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    review = json.loads(
        REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert len(gate) == 101

    assert set(gate) == {
        row["treaty_pair_id"]
        for row in review["packages"]
    }


def test_unaffected_pair_remains_inside_released_canonical_gate():
    release = get_canonical_source_release(
        "CZ-AT",
        gate_path=GATE_PATH,
    )

    assert release.partner_country == "AT"
    assert release.human_review_status == "human_review_complete"
    assert release.is_released is True



def test_semantic_remediation_pair_is_released_via_hash_bound_machine_evidence():
    release = get_canonical_source_release("CZ-TW", gate_path=GATE_PATH)

    assert release.human_review_status == "needs_review"
    assert release.production_approval_status == "production_approved"
    assert release.rule_promotion_status == "promoted"
    assert release.release_status == "released"
    assert release.active_rule_allowed is True
    assert release.production_ready is True
    assert release.fail_closed is False
    assert release.release_blockers == ()
    assert release.is_released is True

    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    row = next(item for item in raw["treaty_partners"] if item["treaty_pair_id"] == "CZ-TW")
    machine = row["release_evidence"]["semantic_remediation_machine_release"]
    assert machine["package_sha256"] == row["package_sha256"]
    assert machine["additional_human_review_claimed"] is False
    assert machine["release_status"] == "released_after_machine_validation"


def test_canonical_gate_releases_full_universe_after_machine_remediation():
    gate = load_canonical_source_release_gate(GATE_PATH)
    remediation = _remediation_pairs()

    released = {pair_id for pair_id, release in gate.items() if release.is_released}
    assert len(released) == 101
    assert released == set(gate)
    assert len(remediation) == 41

    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    rows = {row["treaty_pair_id"]: row for row in raw["treaty_partners"]}
    for pair_id, release in gate.items():
        assert release.release_status == "released"
        assert release.active_rule_allowed is True
        assert release.production_ready is True
        assert release.fail_closed is False
        assert release.release_blockers == ()
        if pair_id in remediation:
            machine = rows[pair_id]["release_evidence"]["semantic_remediation_machine_release"]
            assert machine["package_sha256"] == rows[pair_id]["package_sha256"]
            assert machine["additional_human_review_claimed"] is False

def test_seven_secondary_ai_qa_packages_are_complete():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    complete = sorted(
        pair_id
        for pair_id, release in gate.items()
        if release.secondary_ai_qa_status
        == "secondary_ai_crosscheck_complete"
    )

    assert complete == [
        "CZ-AT",
        "CZ-BD",
        "CZ-KP",
        "CZ-KZ",
        "CZ-MY",
        "CZ-SA",
        "CZ-SG",
    ]

    assert all(
        release.independent_qa_status
        == "not_required"
        for release in gate.values()
    )


def test_non_sample_packages_do_not_fake_secondary_qa():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    non_sample = [
        release
        for release in gate.values()
        if release.secondary_ai_qa_status
        == "not_selected"
    ]

    assert len(non_sample) == 94

    assert all(
        release.independent_qa_status
        == "not_required"
        for release in gate.values()
    )



def test_production_approval_and_promotion_match_current_hash_state():
    gate = load_canonical_source_release_gate(GATE_PATH)
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    rows = {row["treaty_pair_id"]: row for row in raw["treaty_partners"]}
    remediation = _remediation_pairs()

    for pair_id, release in gate.items():
        assert release.production_approval_status == "production_approved"
        assert release.rule_promotion_status == "promoted"
        if pair_id in remediation:
            machine = rows[pair_id]["release_evidence"]["semantic_remediation_machine_release"]
            assert machine["package_sha256"] == release.package_sha256

def test_require_release_accepts_released_pair():
    release = require_canonical_released_source(
        "CZ-AT",
        gate_path=GATE_PATH,
    )

    assert release.treaty_pair_id == "CZ-AT"
    assert release.is_released is True


def test_unknown_pair_fails_closed():
    with pytest.raises(
        CanonicalSourceNotReleasedError
    ):
        get_canonical_source_release(
            "CZ-ZZ",
            gate_path=GATE_PATH,
        )



def test_all_packages_are_approval_eligible_after_machine_remediation():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    remediation = _remediation_pairs()

    assert raw["counts"]["production_approval_eligible_packages"] == 101
    assert raw["counts"]["production_approved_packages"] == 101
    assert raw["counts"]["semantic_remediation_pending_packages"] == 0

    for row in raw["treaty_partners"]:
        assert row["production_approval_eligible"] is True
        assert row["production_approval_status"] == "production_approved"
        if row["treaty_pair_id"] in remediation:
            machine = row["release_evidence"]["semantic_remediation_machine_release"]
            assert machine["package_sha256"] == row["package_sha256"]
            assert machine["additional_human_review_claimed"] is False

def test_stage6b_qa_is_reflected_without_claiming_second_human_review():
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    assert raw["gate_semantics"][
        "secondary_ai_crosscheck_sample_complete"
    ] is True

    assert raw["gate_semantics"][
        "secondary_ai_is_not_human_review"
    ] is True

    assert raw["counts"][
        "secondary_ai_crosscheck_complete_packages"
    ] == 7

    assert raw["counts"][
        "secondary_ai_crosscheck_pending_packages"
    ] == 0

    assert raw["counts"][
        "human_resolution_complete_packages"
    ] == 5

    assert raw["counts"][
        "human_resolution_pending_packages"
    ] == 0


def test_current_package_hashes_are_used_after_stage6b_corrections():
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    queue = json.loads(
        (
            BASE / "cz_country_qa_queue.json"
        ).read_text(encoding="utf-8")
    )

    gate_hashes = {
        row["treaty_pair_id"]:
            row["package_sha256"]
        for row in raw["treaty_partners"]
    }

    queue_hashes = {
        row["treaty_pair_id"]:
            row["package_sha256"]
        for row in queue["packages"]
    }

    assert gate_hashes == queue_hashes



def test_final_gate_releases_only_hash_valid_universe():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    remediation = _remediation_pairs()

    assert raw["counts"]["rule_promoted_packages"] == 101
    assert raw["counts"]["released_packages"] == 101
    assert raw["counts"]["released_scopes"] == 303
    assert raw["counts"]["semantic_remediation_pending_packages"] == 0

    for row in raw["treaty_partners"]:
        assert row["release_blockers"] == []
        if row["treaty_pair_id"] in remediation:
            machine = row["release_evidence"]["semantic_remediation_machine_release"]
            assert machine["package_sha256"] == row["package_sha256"]


def test_semantic_rehashes_are_rebound_by_machine_validation():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    remediation = _remediation_pairs()
    rows = {row["treaty_pair_id"]: row for row in raw["treaty_partners"]}

    assert len(remediation) == 41
    for pair_id in remediation:
        row = rows[pair_id]
        assert row["production_approval_status"] == "production_approved"
        machine = row["release_evidence"]["semantic_remediation_machine_release"]
        assert machine["package_sha256"] == row["package_sha256"]
        assert machine["additional_human_review_claimed"] is False


def test_stage6c_approval_is_not_additional_human_review():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))

    assert raw["gate_semantics"]["production_approval_is_deterministic_governance_result"] is True
    assert raw["gate_semantics"]["production_approval_is_additional_human_review"] is False

    remediation = _remediation_pairs()
    for row in raw["treaty_partners"]:
        if row["treaty_pair_id"] in remediation:
            machine = row["release_evidence"]["semantic_remediation_machine_release"]
            assert machine["package_sha256"] == row["package_sha256"]
            assert machine["additional_human_review_claimed"] is False
        else:
            event = row["release_evidence"]["production_approval_event"]
            assert event is not None
            assert event["additional_human_review_claimed"] is False
            assert event["package_sha256"] == row["package_sha256"]


def test_stage6_runtime_state_releases_full_hash_valid_universe():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    remediation = _remediation_pairs()

    assert raw["counts"]["rule_promoted_packages"] == 101
    assert raw["counts"]["released_packages"] == 101
    assert raw["counts"]["released_scopes"] == 303

    for row in raw["treaty_partners"]:
        assert row["rule_promotion_status"] == "promoted"
        assert row["release_status"] == "released"
        assert row["active_rule_allowed"] is True
        assert row["production_ready"] is True
        assert row["fail_closed"] is False
        if row["treaty_pair_id"] in remediation:
            machine = row["release_evidence"]["semantic_remediation_machine_release"]
            assert machine["package_sha256"] == row["package_sha256"]

def test_secondary_ai_crosscheck_is_never_recorded_as_independent_human_qa():
    import json
    from pathlib import Path

    root = Path(__file__).parents[1]

    gate = json.loads(
        (
            root
            / "data"
            / "legal_reviews"
            / "global_cz_outbound"
            / "production_source_release_gate_v2.json"
        ).read_text(encoding="utf-8")
    )

    rows = gate["treaty_partners"]

    assert len(rows) == 101

    assert all(
        row["independent_qa_status"]
        == "not_required"
        for row in rows
    )

    ai_rows = [
        row
        for row in rows
        if row["secondary_ai_qa_status"]
        == "secondary_ai_crosscheck_complete"
    ]

    assert len(ai_rows) == 7

    assert gate["gate_semantics"][
        "secondary_ai_is_not_human_review"
    ] is True



def test_final_release_events_are_hash_bound():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    source_release = json.loads((BASE / "stage6_source_release.json").read_text(encoding="utf-8"))
    release_by_pair = {row["treaty_pair_id"]: row for row in source_release["records"]}
    remediation = _remediation_pairs()

    assert raw["fail_closed"] is True
    assert len(release_by_pair) == 101

    for row in raw["treaty_partners"]:
        current = release_by_pair[row["treaty_pair_id"]]
        assert current["package_sha256"] == row["package_sha256"]
        assert current["source_release_status"] == "released"
        if row["treaty_pair_id"] in remediation:
            machine = row["release_evidence"]["semantic_remediation_machine_release"]
            assert machine["package_sha256"] == row["package_sha256"]
            assert machine["additional_human_review_claimed"] is False
        else:
            evidence = row["release_evidence"]
            assert evidence["rule_promotion_event"]["package_sha256"] == row["package_sha256"]
            assert evidence["source_release_event"]["package_sha256"] == row["package_sha256"]

