from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.main as main


def test_current_blocked_pair_cannot_reach_analysis():
    with pytest.raises(HTTPException) as exc_info:
        main.require_analysis_source_release(
            "CZ",
            "AT",
        )

    error = exc_info.value

    assert error.status_code == 409
    assert error.detail["code"] == "SOURCE_NOT_RELEASED"
    assert error.detail["treaty_pair_id"] == "CZ-AT"
    assert error.detail["release_status"] == "blocked"
    assert error.detail["release_blockers"]


def test_unknown_cz_pair_fails_closed():
    with pytest.raises(HTTPException) as exc_info:
        main.require_analysis_source_release(
            "cz",
            "zz",
        )

    error = exc_info.value

    assert error.status_code == 409
    assert error.detail["code"] == "SOURCE_NOT_RELEASED"
    assert error.detail["treaty_pair_id"] == "CZ-ZZ"
    assert error.detail["release_status"] == "not_registered"
    assert error.detail["release_blockers"] == [
        "production_source_release_missing"
    ]


def test_non_cz_source_remains_outside_current_gate():
    assert (
        main.require_analysis_source_release(
            "DE",
            "AT",
        )
        is None
    )


def test_released_pair_is_allowed(monkeypatch):
    release = SimpleNamespace(
        is_released=True,
        release_status="released",
        release_blockers=(),
    )

    monkeypatch.setattr(
        main,
        "get_source_release",
        lambda treaty_pair_id: release,
    )

    assert (
        main.require_analysis_source_release(
            "cz",
            "at",
        )
        is release
    )


def test_partial_release_is_blocked(monkeypatch):
    release = SimpleNamespace(
        is_released=False,
        release_status="verification_incomplete",
        release_blockers=(
            "protocol_overlay_verified",
            "mli_overlay_verified",
        ),
    )

    monkeypatch.setattr(
        main,
        "get_source_release",
        lambda treaty_pair_id: release,
    )

    with pytest.raises(HTTPException) as exc_info:
        main.require_analysis_source_release(
            "CZ",
            "AT",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["release_blockers"] == [
        "protocol_overlay_verified",
        "mli_overlay_verified",
    ]


def test_analysis_stops_before_decision_engine(
    monkeypatch,
):
    called = False

    def forbidden_analysis(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError(
            "Decision engine must not run"
        )

    monkeypatch.setattr(
        main,
        "analyze_transaction",
        forbidden_analysis,
    )

    payload = main.AnalysisPayload(
        source_country="CZ",
        recipient_country="CH",
        income_type="royalty",
        transaction_date="2026-08-06",
    )

    with pytest.raises(HTTPException) as exc_info:
        main.analyze(payload)

    assert exc_info.value.status_code == 409
    assert called is False
