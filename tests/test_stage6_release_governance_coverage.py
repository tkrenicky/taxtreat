from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from taxtreat.consolidation.human_review_completion import (
    validate_human_review_completion,
)
from taxtreat.consolidation.review_release_state import (
    assess_review_release_state,
)
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

GATE_PATH = BASE / "production_source_release_gate_v2.json"
QUEUE_PATH = BASE / "cz_country_qa_queue.json"
RECORD_PATH = BASE / "stage5_human_review_completion.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _gate_copy() -> dict:
    return _load(GATE_PATH)


def _queue_record() -> tuple[dict, dict]:
    """Return a hash-aligned fixture for defensive branch tests.

    The committed completion record intentionally remains bound to the
    pre-remediation package hashes. These tests mutate individual fields and
    therefore rebind only their in-memory copy so the intended validation
    branch is reached.
    """
    queue = _load(QUEUE_PATH)
    record = _load(RECORD_PATH)
    hashes = {
        package["treaty_pair_id"]: package["package_sha256"]
        for package in queue["packages"]
    }
    for package in record["packages"]:
        current_hash = hashes[package["treaty_pair_id"]]
        package["package_sha256"] = current_hash
        correction = package.get("post_review_correction")
        if isinstance(correction, dict):
            correction["corrected_package_sha256"] = current_hash
    return queue, record


def test_committed_completion_record_fails_closed_after_semantic_rehash():
    queue = _load(QUEUE_PATH)
    record = _load(RECORD_PATH)

    with pytest.raises(
        ValueError,
        match="stale package hash",
    ):
        validate_human_review_completion(queue, record)


# ---------------------------------------------------------------------------
# Stage 6 canonical gate configuration failures
# ---------------------------------------------------------------------------


def test_v2_gate_missing_file_fails_closed(tmp_path):
    with pytest.raises(
        CanonicalSourceGateError,
        match="Canonical production gate missing",
    ):
        load_canonical_source_release_gate(
            tmp_path / "missing.json"
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda data: data.update(schema_version=999),
            "schema version 2",
        ),
        (
            lambda data: data.update(fail_closed=False),
            "must be fail-closed",
        ),
        (
            lambda data: data.update(treaty_partner_count=100),
            "101 packages",
        ),
        (
            lambda data: data["universe"].update(scope_count=300),
            "303 scopes",
        ),
        (
            lambda data: data.update(treaty_partners=None),
            "requires treaty_partners",
        ),
    ],
)
def test_v2_gate_rejects_invalid_top_level_configuration(
    tmp_path,
    mutation,
    message,
):
    data = _gate_copy()
    mutation(data)

    path = tmp_path / "gate.json"
    _write(path, data)

    with pytest.raises(
        CanonicalSourceGateError,
        match=message,
    ):
        load_canonical_source_release_gate(path)


def test_v2_gate_rejects_duplicate_pair(tmp_path):
    data = _gate_copy()
    data["treaty_partners"][1]["treaty_pair_id"] = (
        data["treaty_partners"][0]["treaty_pair_id"]
    )

    path = tmp_path / "duplicate.json"
    _write(path, data)

    with pytest.raises(
        CanonicalSourceGateError,
        match="Duplicate treaty pair",
    ):
        load_canonical_source_release_gate(path)


@pytest.mark.parametrize(
    "bad_hash",
    [
        "",
        "abc",
        None,
    ],
)
def test_v2_gate_rejects_invalid_package_hash(
    tmp_path,
    bad_hash,
):
    data = _gate_copy()
    data["treaty_partners"][0]["package_sha256"] = bad_hash

    path = tmp_path / "bad-hash.json"
    _write(path, data)

    with pytest.raises(
        CanonicalSourceGateError,
        match="invalid package hash",
    ):
        load_canonical_source_release_gate(path)


def test_v2_gate_rejects_wrong_unique_package_count(tmp_path):
    data = _gate_copy()

    data["treaty_partners"] = data["treaty_partners"][:-1]
    data["treaty_partner_count"] = 101

    path = tmp_path / "short.json"
    _write(path, data)

    with pytest.raises(
        CanonicalSourceGateError,
        match="does not contain 101 unique packages",
    ):
        load_canonical_source_release_gate(path)


def test_v2_gate_unknown_pair_fails_closed():
    with pytest.raises(
        CanonicalSourceNotReleasedError,
        match="No canonical release record",
    ):
        get_canonical_source_release(
            "CZ-ZZ",
            gate_path=GATE_PATH,
        )


def test_v2_gate_can_represent_explicit_fully_released_state(
    tmp_path,
):
    data = _gate_copy()

    row = next(
        item
        for item in data["treaty_partners"]
        if item["independent_qa_status"] == "not_required"
    )

    row["production_approval_status"] = "production_approved"
    row["rule_promotion_status"] = "promoted"
    row["release_status"] = "released"
    row["active_rule_allowed"] = True
    row["production_ready"] = True
    row["fail_closed"] = False
    row["release_blockers"] = []

    path = tmp_path / "released.json"
    _write(path, data)

    release = require_canonical_released_source(
        row["treaty_pair_id"],
        gate_path=path,
    )

    assert release.is_released is True
    assert release.treaty_pair_id == row["treaty_pair_id"]


# ---------------------------------------------------------------------------
# Stage 5 completion record defensive branches
# ---------------------------------------------------------------------------


def test_completion_rejects_wrong_queue_size():
    queue, record = _queue_record()
    queue["packages"] = queue["packages"][:-1]

    with pytest.raises(
        ValueError,
        match="101 packages",
    ):
        validate_human_review_completion(queue, record)


def test_completion_rejects_wrong_record_size():
    queue, record = _queue_record()
    record["packages"] = record["packages"][:-1]

    with pytest.raises(
        ValueError,
        match="101 packages",
    ):
        validate_human_review_completion(queue, record)


def test_completion_rejects_mismatched_country_universe():
    queue, record = _queue_record()

    changed = copy.deepcopy(record)
    changed["packages"][0]["treaty_pair_id"] = "CZ-ZZ"

    with pytest.raises(
        ValueError,
        match="does not match the country-package universe",
    ):
        validate_human_review_completion(queue, changed)


def test_completion_requires_real_reviewer_id():
    queue, record = _queue_record()
    record["reviewer_id"] = ""

    with pytest.raises(
        ValueError,
        match="requires reviewer_id",
    ):
        validate_human_review_completion(queue, record)


@pytest.mark.parametrize(
    "value",
    [None, "", "not-a-date"],
)
def test_completion_requires_valid_completion_date(value):
    queue, record = _queue_record()
    record["review_completed_on"] = value

    with pytest.raises(
        ValueError,
        match="invalid review_completed_on",
    ):
        validate_human_review_completion(queue, record)


def test_completion_rejects_invalid_scope_count():
    queue, record = _queue_record()
    record["packages"][0]["scope_count"] = 2

    with pytest.raises(
        ValueError,
        match="invalid scope count",
    ):
        validate_human_review_completion(queue, record)


def test_completion_rejects_non_complete_primary_review():
    queue, record = _queue_record()
    record["packages"][0][
        "primary_human_review_status"
    ] = "pending"

    with pytest.raises(
        ValueError,
        match="is not complete",
    ):
        validate_human_review_completion(queue, record)


def test_completion_rejects_changed_independent_sample():
    queue, record = _queue_record()

    selected = record["independent_qa"]["selected_pairs"]
    record["independent_qa"]["selected_pairs"] = (
        selected[:-1] + ["CZ-ZZ"]
    )

    with pytest.raises(
        ValueError,
        match="does not match the deterministic queue",
    ):
        validate_human_review_completion(queue, record)


def test_completion_requires_exactly_seven_sample_packages():
    queue, record = _queue_record()

    removed_pair = record["independent_qa"][
        "selected_pairs"
    ][-1]

    record["independent_qa"]["selected_pairs"] = [
        pair
        for pair in record["independent_qa"]["selected_pairs"]
        if pair != removed_pair
    ]

    for package in queue["packages"]:
        if package["treaty_pair_id"] == removed_pair:
            package["human_qa"][
                "independent_sample_selected"
            ] = False

    with pytest.raises(
        ValueError,
        match="exactly seven",
    ):
        validate_human_review_completion(queue, record)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "country_packages",
            100,
            "101 countries",
        ),
        (
            "scopes",
            300,
            "303 scopes",
        ),
        (
            "primary_human_review_complete_packages",
            100,
            "All 101 primary reviews",
        ),
        (
            "primary_human_review_complete_scopes",
            300,
            "All 303 scopes",
        ),
        (
            "independent_qa_pending_packages",
            6,
            "Seven independent QA packages",
        ),
    ],
)
def test_completion_rejects_invalid_summary_counts(
    field,
    value,
    message,
):
    queue, record = _queue_record()
    record["summary"][field] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        validate_human_review_completion(queue, record)


# ---------------------------------------------------------------------------
# Review / approval state defensive branches
# ---------------------------------------------------------------------------


def _package() -> dict:
    queue = _load(QUEUE_PATH)
    return queue["packages"][0]


def _valid_review_event(package: dict) -> dict:
    return {
        "package_sha256": package["package_sha256"],
        "reviewer_id": "reviewer-A",
        "reviewed_at": "2026-08-11T12:00:00Z",
        "outcome": "accepted",
    }


def test_review_state_rejects_invalid_review_timestamp():
    package = _package()
    event = _valid_review_event(package)
    event["reviewed_at"] = "not-a-timestamp"

    with pytest.raises(
        ValueError,
        match="invalid reviewed_at",
    ):
        assess_review_release_state(
            package,
            human_review_event=event,
        )


def test_review_state_requires_production_approver():
    package = _package()
    review = _valid_review_event(package)

    approval = {
        "package_sha256": package["package_sha256"],
        "approver_id": "",
        "approved_at": "2026-08-11T13:00:00Z",
        "outcome": "approved",
    }

    with pytest.raises(
        ValueError,
        match="requires approver_id",
    ):
        assess_review_release_state(
            package,
            human_review_event=review,
            production_approval_event=approval,
        )


def test_review_state_rejects_invalid_approval_timestamp():
    package = _package()
    review = _valid_review_event(package)

    approval = {
        "package_sha256": package["package_sha256"],
        "approver_id": "approver-B",
        "approved_at": "bad-timestamp",
        "outcome": "approved",
    }

    with pytest.raises(
        ValueError,
        match="invalid approved_at",
    ):
        assess_review_release_state(
            package,
            human_review_event=review,
            production_approval_event=approval,
        )


def test_review_state_rejects_nonapproved_approval_outcome():
    package = _package()
    review = _valid_review_event(package)

    approval = {
        "package_sha256": package["package_sha256"],
        "approver_id": "approver-B",
        "approved_at": "2026-08-11T13:00:00Z",
        "outcome": "rejected",
    }

    with pytest.raises(
        ValueError,
        match="outcome='approved'",
    ):
        assess_review_release_state(
            package,
            human_review_event=review,
            production_approval_event=approval,
        )
