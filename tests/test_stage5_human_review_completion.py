import copy
import json
from pathlib import Path

import pytest

from taxtreat.consolidation.human_review_completion import (
    validate_human_review_completion,
)


ROOT = Path(__file__).parents[1]
BASE = ROOT / "data/legal_reviews/global_cz_outbound"

QUEUE = json.loads(
    (BASE / "cz_country_qa_queue.json").read_text(encoding="utf-8")
)

RECORD = json.loads(
    (BASE / "stage5_human_review_completion.json").read_text(
        encoding="utf-8"
    )
)


REMEDIATION = json.loads(
    (
        ROOT
        / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json"
    ).read_text(encoding="utf-8")
)
REMEDIATION_PAIRS = {
    f"CZ-{row['country']}"
    for row in REMEDIATION["corrections"]
}


def _hash_aligned_record():
    record = copy.deepcopy(RECORD)
    queue_hashes = {
        row["treaty_pair_id"]: row["package_sha256"]
        for row in QUEUE["packages"]
    }
    for row in record["packages"]:
        current = queue_hashes[row["treaty_pair_id"]]
        row["package_sha256"] = current
        correction = row.get("post_review_correction")
        if isinstance(correction, dict):
            correction["corrected_package_sha256"] = current
    return record


def test_historical_primary_review_covers_exact_101_303_universe_but_is_stale_after_semantic_rehash():
    assert len(QUEUE["packages"]) == 101
    assert RECORD["summary"]["primary_human_review_complete_packages"] == 101
    assert RECORD["summary"]["primary_human_review_complete_scopes"] == 303

    with pytest.raises(ValueError, match="stale package hash"):
        validate_human_review_completion(QUEUE, RECORD)


def test_semantic_rehash_invalidates_exactly_the_40_remediation_packages():
    queue_hashes = {
        row["treaty_pair_id"]: row["package_sha256"]
        for row in QUEUE["packages"]
    }
    record_hashes = {
        row["treaty_pair_id"]: row["package_sha256"]
        for row in RECORD["packages"]
    }
    mismatched = {
        pair_id
        for pair_id in queue_hashes
        if queue_hashes[pair_id] != record_hashes[pair_id]
    }

    assert len(mismatched) == 40
    assert mismatched == REMEDIATION_PAIRS


def test_independent_qa_remains_real_and_pending():
    assert RECORD["summary"]["independent_qa_required_packages"] == 7
    assert RECORD["summary"]["independent_qa_complete_packages"] == 0
    assert RECORD["summary"]["independent_qa_pending_packages"] == 7

    assert RECORD["independent_qa"]["status"] == "pending"
    assert RECORD["independent_qa"][
        "same_person_as_primary_reviewer_forbidden"
    ] is True


def test_review_completion_does_not_verify_or_release_scopes():
    assert RECORD["summary"]["verified_scopes"] == 0
    assert RECORD["summary"]["production_approved_scopes"] == 0
    assert RECORD["summary"]["production_released_scopes"] == 0

    assert RECORD["safety"][
        "primary_review_completion_does_not_mark_rules_verified"
    ] is True

    assert RECORD["safety"][
        "primary_review_completion_does_not_open_source_release"
    ] is True


def test_stale_hash_is_rejected():
    changed = copy.deepcopy(RECORD)
    changed["packages"][0]["package_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="stale package hash"):
        validate_human_review_completion(QUEUE, changed)


def test_fake_independent_completion_is_rejected():
    changed = _hash_aligned_record()
    changed["summary"]["independent_qa_complete_packages"] = 7

    with pytest.raises(ValueError, match="fail closed"):
        validate_human_review_completion(QUEUE, changed)


def test_fake_production_release_is_rejected():
    changed = _hash_aligned_record()
    changed["summary"]["production_released_scopes"] = 303

    with pytest.raises(ValueError, match="fail closed"):
        validate_human_review_completion(QUEUE, changed)

def test_post_review_corrections_preserve_historical_review_hashes():
    expected_reviewed = {
        "CZ-AT":
            "27df6afe79bbcf08fea08e9aa2f974e38db73249d3d229b1a15e82b510b3fc55",
        "CZ-BD":
            "94ebe6924727e60eca34ee2ca176b3d4698ef378320ec73afcc23314359ea383",
        "CZ-KP":
            "ca4aaf3640b7f2bfeb75e9f03180548d332126f364530bac0be60271af1f611b",
        "CZ-MY":
            "91cd868803d6a0787cd04739189b2268c1883de1bbdb689d98d1a3ffab32814a",
    }

    by_pair = {
        row["treaty_pair_id"]: row
        for row in RECORD["packages"]
    }

    queue_by_pair = {
        row["treaty_pair_id"]: row
        for row in QUEUE["packages"]
    }

    for pair_id, reviewed_hash in expected_reviewed.items():
        node = by_pair[pair_id]

        assert (
            node["reviewed_package_sha256"]
            == reviewed_hash
        )

        # This committed lineage is historical. Semantic remediation
        # created a newer current package hash which deliberately cannot
        # inherit the prior review.
        assert node["package_sha256"] != queue_by_pair[pair_id]["package_sha256"]
        assert node["package_sha256"] != node["reviewed_package_sha256"]

        correction = node["post_review_correction"]

        assert (
            correction["status"]
            == "pending_stage6_human_resolution"
        )

        assert (
            correction[
                "correction_requires_primary_human_resolution"
            ]
            is True
        )

        assert (
            correction["production_approval_allowed"]
            is False
        )


def test_post_review_correction_lineage_remains_fail_closed():
    lineage = RECORD[
        "post_review_correction_lineage"
    ]

    assert lineage["changed_package_count"] == 4

    assert lineage["changed_pairs"] == [
        "CZ-AT",
        "CZ-BD",
        "CZ-KP",
        "CZ-MY",
    ]

    assert (
        lineage["historical_review_hashes_preserved"]
        is True
    )

    assert lineage["production_approval_created"] is False
    assert lineage["rule_promotion_created"] is False
    assert lineage["source_release_created"] is False


def test_fake_post_review_correction_release_is_rejected():
    changed = _hash_aligned_record()

    node = next(
        row
        for row in changed["packages"]
        if row["treaty_pair_id"] == "CZ-AT"
    )

    node[
        "post_review_correction"
    ][
        "production_approval_allowed"
    ] = True

    with pytest.raises(
        ValueError,
        match="fail closed",
    ):
        validate_human_review_completion(
            QUEUE,
            changed,
        )
