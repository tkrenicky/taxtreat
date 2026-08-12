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


def test_taiwan_is_inside_released_canonical_gate():
    release = get_canonical_source_release(
        "CZ-TW",
        gate_path=GATE_PATH,
    )

    assert release.partner_country == "TW"
    assert release.human_review_status == (
        "human_review_complete"
    )
    assert release.is_released is True


def test_all_canonical_packages_are_released():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    assert all(
        release.release_status == "released"
        for release in gate.values()
    )
    assert all(
        release.active_rule_allowed is True
        for release in gate.values()
    )
    assert all(
        release.production_ready is True
        for release in gate.values()
    )
    assert all(
        release.fail_closed is False
        for release in gate.values()
    )
    assert all(
        release.release_blockers == ()
        for release in gate.values()
    )
    assert all(
        release.is_released is True
        for release in gate.values()
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


def test_production_approval_and_promotion_are_complete():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    assert all(
        release.production_approval_status
        == "production_approved"
        for release in gate.values()
    )
    assert all(
        release.rule_promotion_status
        == "promoted"
        for release in gate.values()
    )


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


def test_all_101_packages_are_production_approval_eligible_and_approved():
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    assert raw["counts"][
        "production_approval_eligible_packages"
    ] == 101

    assert raw["counts"][
        "production_approved_packages"
    ] == 101

    assert all(
        row["production_approval_eligible"] is True
        for row in raw["treaty_partners"]
    )

    assert all(
        row["production_approval_status"]
        == "production_approved"
        for row in raw["treaty_partners"]
    )


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


def test_final_gate_releases_complete_universe():
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    assert raw["counts"][
        "rule_promoted_packages"
    ] == 101
    assert raw["counts"][
        "released_packages"
    ] == 101
    assert raw["counts"][
        "released_scopes"
    ] == 303

    for row in raw["treaty_partners"]:
        assert row["release_blockers"] == []


def test_stage6c_all_101_packages_are_production_approved():
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    assert raw["counts"][
        "production_approval_eligible_packages"
    ] == 101

    assert raw["counts"][
        "production_approved_packages"
    ] == 101

    assert all(
        row["production_approval_status"]
        == "production_approved"
        for row in raw["treaty_partners"]
    )


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

    for row in raw["treaty_partners"]:
        event = row["release_evidence"][
            "production_approval_event"
        ]

        assert event is not None
        assert event["additional_human_review_claimed"] is False
        assert (
            event["package_sha256"]
            == row["package_sha256"]
        )


def test_stage6_final_runtime_state_is_released():
    raw = json.loads(
        GATE_PATH.read_text(encoding="utf-8")
    )

    assert raw["counts"][
        "rule_promoted_packages"
    ] == 101
    assert raw["counts"][
        "released_packages"
    ] == 101
    assert raw["counts"][
        "released_scopes"
    ] == 303

    for row in raw["treaty_partners"]:
        assert row["rule_promotion_status"] == "promoted"
        assert row["release_status"] == "released"
        assert row["active_rule_allowed"] is True
        assert row["production_ready"] is True
        assert row["fail_closed"] is False
        assert row["release_blockers"] == []


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

    for row in raw["treaty_partners"]:
        evidence = row["release_evidence"]
        promotion = evidence["rule_promotion_event"]
        release = evidence["source_release_event"]

        assert promotion is not None
        assert release is not None

        assert (
            promotion["package_sha256"]
            == row["package_sha256"]
        )
        assert (
            release["package_sha256"]
            == row["package_sha256"]
        )
        assert (
            promotion["rule_file_sha256"]
            == release["rule_file_sha256"]
        )

        assert row["fail_closed"] is False
        assert row["release_blockers"] == []
