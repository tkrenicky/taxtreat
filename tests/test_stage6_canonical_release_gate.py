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


def test_semantic_remediation_pair_is_fail_closed():
    release = get_canonical_source_release(
        "CZ-TW",
        gate_path=GATE_PATH,
    )

    assert release.human_review_status == "needs_review"
    assert release.production_approval_status == "not_approved"
    assert release.rule_promotion_status == "not_promoted"
    assert release.release_status == "not_released"
    assert release.active_rule_allowed is False
    assert release.production_ready is False
    assert release.fail_closed is True
    assert "semantic_remediation_requires_hash_bound_human_review" in release.release_blockers
    assert release.is_released is False


def test_canonical_gate_releases_61_unchanged_packages_and_blocks_40_remediated_packages():
    gate = load_canonical_source_release_gate(GATE_PATH)
    remediation = _remediation_pairs()

    released = {
        pair_id
        for pair_id, release in gate.items()
        if release.is_released
    }
    blocked = set(gate) - released

    assert len(released) == 61
    assert len(blocked) == 40
    assert blocked == remediation

    for pair_id in released:
        release = gate[pair_id]
        assert release.release_status == "released"
        assert release.active_rule_allowed is True
        assert release.production_ready is True
        assert release.fail_closed is False
        assert release.release_blockers == ()

    for pair_id in blocked:
        release = gate[pair_id]
        assert release.release_status == "not_released"
        assert release.active_rule_allowed is False
        assert release.production_ready is False
        assert release.fail_closed is True
        assert release.release_blockers == (
            "semantic_remediation_requires_hash_bound_human_review",
        )


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
    remediation = _remediation_pairs()

    for pair_id, release in gate.items():
        if pair_id in remediation:
            assert release.production_approval_status == "not_approved"
            assert release.rule_promotion_status == "not_promoted"
        else:
            assert release.production_approval_status == "production_approved"
            assert release.rule_promotion_status == "promoted"


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


def test_only_unchanged_packages_remain_production_approval_eligible_and_approved():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    remediation = _remediation_pairs()

    assert raw["counts"]["production_approval_eligible_packages"] == 61
    assert raw["counts"]["production_approved_packages"] == 61
    assert raw["counts"]["semantic_remediation_pending_packages"] == 40

    for row in raw["treaty_partners"]:
        pair_id = row["treaty_pair_id"]
        if pair_id in remediation:
            assert row["production_approval_eligible"] is False
            assert row["production_approval_status"] == "not_approved"
        else:
            assert row["production_approval_eligible"] is True
            assert row["production_approval_status"] == "production_approved"


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

    assert raw["counts"]["rule_promoted_packages"] == 61
    assert raw["counts"]["released_packages"] == 61
    assert raw["counts"]["released_scopes"] == 183

    for row in raw["treaty_partners"]:
        if row["treaty_pair_id"] in remediation:
            assert row["release_blockers"] == [
                "semantic_remediation_requires_hash_bound_human_review"
            ]
        else:
            assert row["release_blockers"] == []


def test_stage6c_prior_approval_is_invalidated_for_semantically_rehashed_packages():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    remediation = _remediation_pairs()

    assert raw["counts"]["production_approval_eligible_packages"] == 61
    assert raw["counts"]["production_approved_packages"] == 61
    assert sum(
        row["production_approval_status"] == "not_approved"
        for row in raw["treaty_partners"]
    ) == 40
    assert {
        row["treaty_pair_id"]
        for row in raw["treaty_partners"]
        if row["production_approval_status"] == "not_approved"
    } == remediation


def test_stage6c_approval_is_not_additional_human_review():
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    assert raw["gate_semantics"][
        "production_approval_is_deterministic_governance_result"
    ] is True

    assert raw["gate_semantics"][
        "production_approval_is_additional_human_review"
    ] is False

    remediation = _remediation_pairs()
    for row in raw["treaty_partners"]:
        event = row["release_evidence"]["production_approval_event"]
        assert event is not None
        assert event["additional_human_review_claimed"] is False
        if row["treaty_pair_id"] in remediation:
            assert event["package_sha256"] != row["package_sha256"]
            semantic = row["release_evidence"]["semantic_remediation"]
            assert semantic["production_approval_allowed"] is False
            assert semantic["automatic_approval_forbidden"] is True
        else:
            assert event["package_sha256"] == row["package_sha256"]


def test_stage6_runtime_state_is_released_only_for_hash_valid_packages():
    raw = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    remediation = _remediation_pairs()

    assert raw["counts"]["rule_promoted_packages"] == 61
    assert raw["counts"]["released_packages"] == 61
    assert raw["counts"]["released_scopes"] == 183

    for row in raw["treaty_partners"]:
        if row["treaty_pair_id"] in remediation:
            assert row["rule_promotion_status"] == "not_promoted"
            assert row["release_status"] == "not_released"
            assert row["active_rule_allowed"] is False
            assert row["production_ready"] is False
            assert row["fail_closed"] is True
        else:
            assert row["rule_promotion_status"] == "promoted"
            assert row["release_status"] == "released"
            assert row["active_rule_allowed"] is True
            assert row["production_ready"] is True
            assert row["fail_closed"] is False


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
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    assert raw["fail_closed"] is True

    remediation = _remediation_pairs()
    for row in raw["treaty_partners"]:
        evidence = row["release_evidence"]
        promotion = evidence["rule_promotion_event"]
        release = evidence["source_release_event"]

        assert promotion is not None
        assert release is not None
        assert promotion["rule_file_sha256"] == release["rule_file_sha256"]

        if row["treaty_pair_id"] in remediation:
            # Prior release evidence is retained only as historical lineage;
            # it must not bind to or release the newly rehashed package.
            assert promotion["package_sha256"] != row["package_sha256"]
            assert release["package_sha256"] != row["package_sha256"]
            assert row["fail_closed"] is True
            assert row["release_blockers"]
        else:
            assert promotion["package_sha256"] == row["package_sha256"]
            assert release["package_sha256"] == row["package_sha256"]
            assert row["fail_closed"] is False
            assert row["release_blockers"] == []
