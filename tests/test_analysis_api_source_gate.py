from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.main as main


def test_current_released_pair_can_reach_analysis():
    release = main.require_analysis_source_release(
        "CZ",
        "AT",
    )

    assert release.treaty_pair_id == "CZ-AT"
    assert release.release_status == "released"
    assert release.release_blockers == ()
    assert release.is_released is True


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
        "get_canonical_source_release",
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
        "get_canonical_source_release",
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


def test_analysis_reaches_decision_engine(
    monkeypatch,
):
    called = False
    original = main.analyze_transaction

    def observed_analysis(*args, **kwargs):
        nonlocal called
        called = True
        return original(*args, **kwargs)

    monkeypatch.setattr(
        main,
        "analyze_transaction",
        observed_analysis,
    )

    response = main.analyze(
        main.AnalysisPayload(
            source_country="CZ",
            recipient_country="CH",
            income_type="royalty",
            transaction_date="2026-08-06",
        )
    )

    assert called is True
    assert "status" in response
    assert "requires_review" in response


def test_released_source_handoff_preserves_needs_review(
    monkeypatch,
    tmp_path,
):
    captured = {}

    def candidate_analysis(request):
        captured["request"] = request
        return SimpleNamespace(
            status=SimpleNamespace(value="needs_review"),
            rate=None,
            candidate_rate=None,
            eligible=None,
            requires_review=True,
            selected_rule_id=None,
            candidate_rule_id=None,
            applied_rule_ids=[],
            overridden_rule_id=None,
            missing_facts=[],
            missing_legal_layers=["human_primary_legal_review"],
            failed_conditions=[],
            explanation="Candidate evidence remains under review.",
            citations=[],
            layer_results=[],
            dataset_release="candidate-test-release",
        )

    manifest = tmp_path / "release_manifest.json"
    manifest.write_text(
        '{"dataset_version": "test-manifest"}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        main,
        "require_analysis_source_release",
        lambda source, recipient: None,
    )
    monkeypatch.setattr(
        main,
        "analyze_transaction",
        candidate_analysis,
    )
    monkeypatch.setattr(
        main,
        "RELEASE_MANIFEST",
        manifest,
    )

    response = main.analyze(
        main.AnalysisPayload(
            source_country="cz",
            recipient_country="ae",
            income_type="dividend",
            transaction_date="2026-08-09",
        )
    )

    assert captured["request"].source_country == "CZ"
    assert captured["request"].recipient_country == "AE"
    assert response["status"] == "needs_review"
    assert response["rate"] is None
    assert response["requires_review"] is True
    assert response["dataset_version"] == (
        "stage6-source-release-2026-08-12.1"
    )
