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


def test_taiwan_is_inside_canonical_gate():
    release = get_canonical_source_release(
        "CZ-TW",
        gate_path=GATE_PATH,
    )

    assert release.partner_country == "TW"
    assert release.human_review_status == (
        "human_review_complete"
    )

    assert release.is_released is False


def test_all_packages_remain_fail_closed():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    assert all(
        release.release_status == "blocked"
        for release in gate.values()
    )

    assert all(
        release.active_rule_allowed is False
        for release in gate.values()
    )

    assert all(
        release.production_ready is False
        for release in gate.values()
    )

    assert all(
        release.fail_closed is True
        for release in gate.values()
    )

    assert all(
        release.is_released is False
        for release in gate.values()
    )


def test_seven_independent_qa_packages_remain_pending():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    pending = sorted(
        pair_id
        for pair_id, release in gate.items()
        if release.independent_qa_status
        == "pending"
    )

    assert pending == [
        "CZ-AT",
        "CZ-BD",
        "CZ-KP",
        "CZ-KZ",
        "CZ-MY",
        "CZ-SA",
        "CZ-SG",
    ]


def test_non_sample_packages_do_not_fake_independent_review():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    statuses = {
        release.independent_qa_status
        for release in gate.values()
    }

    assert statuses == {
        "pending",
        "not_required",
    }


def test_no_production_approval_or_promotion_created():
    gate = load_canonical_source_release_gate(
        GATE_PATH
    )

    assert all(
        release.production_approval_status
        == "not_approved"
        for release in gate.values()
    )

    assert all(
        release.rule_promotion_status
        == "not_promoted"
        for release in gate.values()
    )


def test_require_release_fails_closed():
    with pytest.raises(
        CanonicalSourceNotReleasedError
    ):
        require_canonical_released_source(
            "CZ-AT",
            gate_path=GATE_PATH,
        )


def test_unknown_pair_fails_closed():
    with pytest.raises(
        CanonicalSourceNotReleasedError
    ):
        get_canonical_source_release(
            "CZ-ZZ",
            gate_path=GATE_PATH,
        )
