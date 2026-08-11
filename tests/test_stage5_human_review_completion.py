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


def test_completed_primary_review_covers_exact_101_303_universe():
    validate_human_review_completion(QUEUE, RECORD)

    assert RECORD["summary"][
        "primary_human_review_complete_packages"
    ] == 101

    assert RECORD["summary"][
        "primary_human_review_complete_scopes"
    ] == 303


def test_completion_record_is_bound_to_exact_current_package_hashes():
    queue_hashes = {
        row["treaty_pair_id"]: row["package_sha256"]
        for row in QUEUE["packages"]
    }

    record_hashes = {
        row["treaty_pair_id"]: row["package_sha256"]
        for row in RECORD["packages"]
    }

    assert record_hashes == queue_hashes


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
    changed = copy.deepcopy(RECORD)
    changed["summary"]["independent_qa_complete_packages"] = 7

    with pytest.raises(ValueError, match="fail closed"):
        validate_human_review_completion(QUEUE, changed)


def test_fake_production_release_is_rejected():
    changed = copy.deepcopy(RECORD)
    changed["summary"]["production_released_scopes"] = 303

    with pytest.raises(ValueError, match="fail closed"):
        validate_human_review_completion(QUEUE, changed)
