from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from fastapi import HTTPException

import app.main as app_main
from taxtreat.engine.source_release_gate_v2 import (
    DEFAULT_GATE_PATH,
    CanonicalSourceNotReleasedError,
    get_canonical_source_release,
    require_canonical_released_source,
)


ROOT = Path(__file__).parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

CANONICAL_GATE = (
    BASE
    / "production_source_release_gate_v2.json"
)

LEGACY_GATE = (
    BASE
    / "production_source_release_gate.json"
)


def test_runtime_imports_canonical_gate_not_legacy_gate():
    source = inspect.getsource(app_main)

    assert (
        "taxtreat.engine.source_release_gate_v2"
        in source
    )

    assert (
        "from taxtreat.engine.source_release_gate import"
        not in source
    )


def test_canonical_default_path_is_v2_gate():
    assert DEFAULT_GATE_PATH.resolve() == (
        CANONICAL_GATE.resolve()
    )


def test_canonical_gate_is_full_101_country_universe():
    raw = json.loads(
        CANONICAL_GATE.read_text(encoding="utf-8")
    )

    assert raw["treaty_partner_count"] == 101
    assert raw["universe"]["scope_count"] == 303

    pair_ids = {
        row["treaty_pair_id"]
        for row in raw["treaty_partners"]
    }

    assert len(pair_ids) == 101
    assert "CZ-TW" in pair_ids


def test_canonical_gate_has_stage6c_approval_but_no_release():
    raw = json.loads(
        CANONICAL_GATE.read_text(encoding="utf-8")
    )

    assert raw["counts"][
        "production_approved_packages"
    ] == 101

    assert raw["counts"][
        "rule_promoted_packages"
    ] == 0

    assert raw["counts"][
        "released_packages"
    ] == 0

    assert raw["counts"][
        "released_scopes"
    ] == 0


def test_all_canonical_packages_remain_runtime_blocked():
    raw = json.loads(
        CANONICAL_GATE.read_text(encoding="utf-8")
    )

    for row in raw["treaty_partners"]:
        assert (
            row["production_approval_status"]
            == "production_approved"
        )
        assert (
            row["rule_promotion_status"]
            == "not_promoted"
        )
        assert row["release_status"] == "blocked"
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True


@pytest.mark.parametrize(
    "pair_id",
    [
        "CZ-AT",
        "CZ-CH",
        "CZ-SG",
        "CZ-TW",
    ],
)
def test_runtime_gate_blocks_known_pairs_before_promotion(
    pair_id: str,
):
    release = get_canonical_source_release(pair_id)

    assert release.is_released is False

    with pytest.raises(
        CanonicalSourceNotReleasedError
    ):
        require_canonical_released_source(pair_id)


def test_api_release_guard_uses_canonical_blockers():
    release = get_canonical_source_release("CZ-AT")

    assert release.production_approval_status == (
        "production_approved"
    )

    assert release.rule_promotion_status == (
        "not_promoted"
    )

    with pytest.raises(HTTPException) as exc_info:
        app_main.require_analysis_source_release(
            "CZ",
            "AT",
        )

    exc = exc_info.value

    assert exc.status_code == 409

    assert exc.detail["code"] == (
        "SOURCE_NOT_RELEASED"
    )

    assert exc.detail["treaty_pair_id"] == "CZ-AT"

    assert exc.detail["release_status"] == "blocked"

    assert (
        "rule_promotion_missing"
        in exc.detail["release_blockers"]
    )

    assert (
        "source_release_not_opened"
        in exc.detail["release_blockers"]
    )

    assert (
        "production_approval_missing"
        not in exc.detail["release_blockers"]
    )


def test_unknown_cz_pair_still_fails_closed():
    with pytest.raises(HTTPException) as exc_info:
        app_main.require_analysis_source_release(
            "CZ",
            "ZZ",
        )

    exc = exc_info.value

    assert exc.status_code == 409

    assert exc.detail == {
        "code": "SOURCE_NOT_RELEASED",
        "treaty_pair_id": "CZ-ZZ",
        "release_status": "not_registered",
        "release_blockers": [
            "production_source_release_missing"
        ],
    }


def test_non_cz_source_is_outside_current_cz_gate_scope():
    assert (
        app_main.require_analysis_source_release(
            "DE",
            "AT",
        )
        is None
    )


def test_legacy_gate_file_is_not_runtime_authority():
    assert LEGACY_GATE.is_file()

    source = inspect.getsource(app_main)

    assert "production_source_release_gate.json" not in source
    assert "get_source_release(" not in source
