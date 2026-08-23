import pytest

import taxtreat.services.source_country_release_gate as gate_module
from taxtreat.countries.registry import CountryConfig
from taxtreat.services.source_country_release_gate import (
    SourceCountryNotReleasedError,
    UnsupportedSourceCountryError,
    require_source_country_analysis_release,
)


def _released_sk_config():
    real = gate_module.get_country_config("SK")
    return CountryConfig(
        code=real.code,
        currency=real.currency,
        supported_income_types=real.supported_income_types,
        treaty_partner_registry=real.treaty_partner_registry,
        runtime_released=True,
        fx_provider=real.fx_provider,
        domestic_legal_source_url=real.domestic_legal_source_url,
        domestic_law_label=real.domestic_law_label,
        compliance_form_code=real.compliance_form_code,
        compliance_legal_reference=real.compliance_legal_reference,
        compliance_periodicity=real.compliance_periodicity,
        release_gate_strategy="source_country_manifest",
    )


def _flip_sk_runtime_flag(monkeypatch):
    config = _released_sk_config()
    original_get_country_config = gate_module.get_country_config
    monkeypatch.setattr(
        gate_module,
        "get_country_config",
        lambda code: config if code == "SK" else original_get_country_config(code),
    )


def test_sk_is_released_at_source_country_release_layer_before_analysis():
    decision = require_source_country_analysis_release("sk")

    assert decision.source_country == "SK"
    assert decision.allowed is True
    assert decision.code == "SOURCE_COUNTRY_RELEASED"
    assert decision.release_status == "released"
    assert decision.blockers == ()


def test_runtime_flag_alone_cannot_release_sk(tmp_path, monkeypatch):
    import json

    config = _released_sk_config()
    monkeypatch.setattr(gate_module, "get_country_config", lambda code: config)

    manifest = json.loads(
        gate_module._release_manifest_path("SK").read_text(encoding="utf-8")
    )
    manifest["release_eligible"] = False
    manifest["release_status"] = "pre_release"
    manifest["blockers"] = ["synthetic_release_not_completed"]

    manifest_path = tmp_path / "source_country_release_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr(
        gate_module,
        "_release_manifest_path",
        lambda code: manifest_path,
    )

    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("SK")

    decision = exc_info.value.decision
    assert decision.allowed is False
    assert decision.code == "SOURCE_COUNTRY_RELEASE_EVIDENCE_INCOMPLETE"
    assert "release_manifest_not_eligible" in decision.blockers
    assert "synthetic_release_not_completed" in decision.blockers


def test_missing_release_manifest_fails_closed_even_if_runtime_flag_true(tmp_path, monkeypatch):
    config = _released_sk_config()
    monkeypatch.setattr(gate_module, "get_country_config", lambda code: config)
    monkeypatch.setattr(
        gate_module,
        "_release_manifest_path",
        lambda code: tmp_path / "missing-release-manifest.json",
    )

    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("SK")

    decision = exc_info.value.decision
    assert decision.code == "SOURCE_COUNTRY_RELEASE_EVIDENCE_MISSING"
    assert decision.blockers == ("committed_source_country_release_manifest_missing",)


def test_malformed_release_manifest_fails_closed_even_if_runtime_flag_true(tmp_path, monkeypatch):
    config = _released_sk_config()
    monkeypatch.setattr(gate_module, "get_country_config", lambda code: config)
    path = tmp_path / "release.json"
    path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(gate_module, "_release_manifest_path", lambda code: path)

    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("SK")

    decision = exc_info.value.decision
    assert decision.code == "SOURCE_COUNTRY_RELEASE_EVIDENCE_INVALID"
    assert decision.blockers == ("committed_source_country_release_manifest_invalid",)


def test_non_cz_release_requires_second_independent_evidence_gate(monkeypatch):
    config = _released_sk_config()
    monkeypatch.setattr(gate_module, "get_country_config", lambda code: config)
    calls = []

    decision = require_source_country_analysis_release(
        "SK",
        release_evidence_gate=lambda code: calls.append(code),
    )

    assert calls == ["SK"]
    assert decision.allowed is True


def test_cz_remains_released_and_can_delegate_to_existing_pair_gate():
    calls = []

    decision = require_source_country_analysis_release(
        "CZ",
        released_country_gate=lambda code: calls.append(code),
    )

    assert calls == ["CZ"]
    assert decision.allowed is True
    assert decision.code == "SOURCE_COUNTRY_RELEASED"
    assert decision.release_status == "released"
    assert decision.blockers == ()


def test_unknown_source_country_fails_closed():
    with pytest.raises(UnsupportedSourceCountryError):
        require_source_country_analysis_release("XX")


def _write_pattern_release_evidence(tmp_path, *, pattern_scopes=201):
    import json

    evidence = {
        "schema_version": 1,
        "source_country": "SK",
        "status": "human_review_completed_with_pattern_reconciliation",
        "coverage": {
            "expected_scope_count": 225,
            "individually_reviewed_scopes": 24,
            "pattern_reconciled_scopes": pattern_scopes,
            "legal_review_covered_scopes": 225,
            "uncovered_scopes": 0,
        },
        "individual_review": {
            "substantive_machine_discrepancies": 0,
            "exceptions": 0,
        },
        "pattern_reconciliation": {
            "scope_count": pattern_scopes,
            "result": "COVERED_BY_VALIDATED_STANDARD_PATTERN",
            "individual_human_review_claimed": False,
        },
        "production_released_scopes": 0,
    }

    manifest = {
        "schema_version": 2,
        "source_country": "SK",
        "dataset_release": "test-sk-release",
        "expected_scope_count": 225,
        "human_reviewed_scopes": 24,
        "legal_review_covered_scopes": 225,
        "pattern_reconciled_scopes": 201,
        "human_review_evidence": "human_review_coverage.json",
        "cooperating_state_list_ready": True,
        "final_calculation_policy_ready": True,
        "zero_withholding_notification_scope_ready": True,
        "compliance_calendar_adjustment_ready": True,
        "rendered_report_leakage_gate_ready": True,
        "release_eligible": True,
        "release_status": "released",
        "blockers": [],
        "policy": {
            "all_expected_scopes_must_be_human_reviewed": False,
            "all_expected_scopes_must_be_legally_covered": True,
            "pattern_reconciliation_allowed_for_standard_population": True,
        },
    }

    manifest_path = tmp_path / "source_country_release_manifest.json"
    evidence_path = tmp_path / "human_review_coverage.json"

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    evidence_path.write_text(
        json.dumps(evidence),
        encoding="utf-8",
    )

    return manifest_path


def test_pattern_review_coverage_can_satisfy_legal_review_gate(
    tmp_path,
    monkeypatch,
):
    _flip_sk_runtime_flag(monkeypatch)
    manifest_path = _write_pattern_release_evidence(tmp_path)

    monkeypatch.setattr(
        gate_module,
        "_release_manifest_path",
        lambda code: manifest_path,
    )

    decision = require_source_country_analysis_release("SK")

    assert decision.allowed is True
    assert decision.code == "SOURCE_COUNTRY_RELEASED"
    assert decision.blockers == ()


def test_pattern_review_coverage_fails_closed_on_count_mismatch(
    tmp_path,
    monkeypatch,
):
    _flip_sk_runtime_flag(monkeypatch)
    manifest_path = _write_pattern_release_evidence(
        tmp_path,
        pattern_scopes=200,
    )

    monkeypatch.setattr(
        gate_module,
        "_release_manifest_path",
        lambda code: manifest_path,
    )

    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("SK")

    decision = exc_info.value.decision

    assert decision.allowed is False
    assert "legal_review_pattern_count_manifest_mismatch" in decision.blockers
    assert "legal_review_coverage_count_mismatch" in decision.blockers


def test_pattern_review_coverage_fails_closed_without_evidence(
    tmp_path,
    monkeypatch,
):
    import json

    _flip_sk_runtime_flag(monkeypatch)

    manifest = {
        "schema_version": 2,
        "source_country": "SK",
        "dataset_release": "test-sk-release",
        "expected_scope_count": 225,
        "human_reviewed_scopes": 24,
        "legal_review_covered_scopes": 225,
        "pattern_reconciled_scopes": 201,
        "human_review_evidence": "missing.json",
        "cooperating_state_list_ready": True,
        "final_calculation_policy_ready": True,
        "zero_withholding_notification_scope_ready": True,
        "compliance_calendar_adjustment_ready": True,
        "rendered_report_leakage_gate_ready": True,
        "release_eligible": True,
        "release_status": "released",
        "blockers": [],
        "policy": {
            "all_expected_scopes_must_be_human_reviewed": False,
            "all_expected_scopes_must_be_legally_covered": True,
        },
    }

    manifest_path = tmp_path / "source_country_release_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr(
        gate_module,
        "_release_manifest_path",
        lambda code: manifest_path,
    )

    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("SK")

    assert (
        "legal_review_coverage_evidence_missing"
        in exc_info.value.decision.blockers
    )
