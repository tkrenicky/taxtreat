from dataclasses import replace
import json
from pathlib import Path

import pytest

import taxtreat.services.source_country_calculation as calc_module
import taxtreat.services.source_country_release_gate as gate_module
import taxtreat.services.source_country_runtime_metadata as metadata_module
from taxtreat.countries.registry import get_country_config
from taxtreat.services.source_country_calculation import (
    build_source_country_withholding_compliance_schedule,
    build_source_country_withholding_tax_calculation,
)
from taxtreat.services.source_country_release_gate import (
    SourceCountryNotReleasedError,
    require_source_country_analysis_release,
)
from taxtreat.services.source_country_runtime_metadata import (
    source_country_runtime_dataset_version,
)


def _valid_coverage_payload():
    return {
        "source_country": "SK",
        "status": "human_review_completed_with_pattern_reconciliation_and_mli_reconfirmation",
        "coverage": {
            "expected_scope_count": 225,
            "individually_reviewed_scopes": 24,
            "pattern_reconciled_scopes": 201,
            "legal_review_covered_scopes": 225,
            "uncovered_scopes": 0,
        },
        "individual_review": {
            "substantive_machine_discrepancies": 0,
            "exceptions": 0,
        },
        "pattern_reconciliation": {
            "scope_count": 201,
            "result": "COVERED_BY_VALIDATED_STANDARD_PATTERN",
            "individual_human_review_claimed": False,
        },
        "production_released_scopes": 0,
    }


def _valid_manifest():
    return {
        "source_country": "SK",
        "expected_scope_count": 225,
        "human_reviewed_scopes": 24,
        "pattern_reconciled_scopes": 201,
        "legal_review_covered_scopes": 225,
        "human_review_evidence": "coverage.json",
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


def _write_release_pair(tmp_path: Path, manifest=None, coverage=None):
    manifest = _valid_manifest() if manifest is None else manifest
    coverage = _valid_coverage_payload() if coverage is None else coverage
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "coverage.json").write_text(json.dumps(coverage), encoding="utf-8")
    return manifest_path


def test_release_coverage_policy_validation_shortcuts(tmp_path):
    path = tmp_path / "manifest.json"
    base = _valid_manifest()

    invalid = dict(base, policy=None)
    assert gate_module._review_coverage_blockers(invalid, path) == (
        "release_manifest_review_policy_invalid",
    )

    missing = dict(base, policy={
        "all_expected_scopes_must_be_human_reviewed": False,
        "all_expected_scopes_must_be_legally_covered": False,
    })
    assert gate_module._review_coverage_blockers(missing, path) == (
        "release_manifest_legal_review_coverage_policy_missing",
    )

    legacy = dict(base, policy={
        "all_expected_scopes_must_be_human_reviewed": True,
        "all_expected_scopes_must_be_legally_covered": False,
    })
    assert gate_module._review_coverage_blockers(legacy, path) == ()


def test_release_coverage_evidence_missing_and_invalid(tmp_path):
    manifest = _valid_manifest()
    manifest["human_review_evidence"] = ""
    assert gate_module._review_coverage_blockers(manifest, tmp_path / "m.json") == (
        "legal_review_coverage_evidence_missing",
    )

    manifest["human_review_evidence"] = "missing.json"
    assert gate_module._review_coverage_blockers(manifest, tmp_path / "m.json") == (
        "legal_review_coverage_evidence_missing",
    )

    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    manifest["human_review_evidence"] = bad.name
    assert gate_module._review_coverage_blockers(manifest, tmp_path / "m.json") == (
        "legal_review_coverage_evidence_invalid",
    )

    bad.write_text("[]", encoding="utf-8")
    assert gate_module._review_coverage_blockers(manifest, tmp_path / "m.json") == (
        "legal_review_coverage_evidence_invalid",
    )


def test_release_coverage_collects_all_semantic_mismatches(tmp_path):
    manifest = _valid_manifest()
    coverage = _valid_coverage_payload()
    coverage["source_country"] = "CZ"
    coverage["status"] = "incomplete"
    coverage["coverage"] = {
        "expected_scope_count": 224,
        "individually_reviewed_scopes": 23,
        "pattern_reconciled_scopes": 199,
        "legal_review_covered_scopes": 220,
        "uncovered_scopes": 5,
    }
    coverage["pattern_reconciliation"] = {
        "scope_count": 198,
        "result": "INCOMPLETE",
        "individual_human_review_claimed": True,
    }
    coverage["individual_review"] = {
        "substantive_machine_discrepancies": 1,
        "exceptions": 1,
    }
    coverage["production_released_scopes"] = 1
    (tmp_path / "coverage.json").write_text(json.dumps(coverage), encoding="utf-8")

    blockers = set(gate_module._review_coverage_blockers(manifest, tmp_path / "m.json"))
    expected = {
        "legal_review_coverage_source_country_mismatch",
        "legal_review_coverage_status_incomplete",
        "legal_review_coverage_expected_scope_mismatch",
        "legal_review_individual_count_manifest_mismatch",
        "legal_review_pattern_count_manifest_mismatch",
        "legal_review_covered_count_manifest_mismatch",
        "legal_review_coverage_count_mismatch",
        "full_legal_review_coverage_not_completed",
        "legal_review_pattern_scope_count_mismatch",
        "legal_review_pattern_reconciliation_incomplete",
        "legal_review_pattern_false_individual_review_claim",
        "legal_review_substantive_discrepancy_unresolved",
        "legal_review_exception_unresolved",
        "legal_review_evidence_preclaims_production_release",
    }
    assert expected <= blockers


def test_release_coverage_rejects_bad_count_types_and_missing_sections(tmp_path):
    manifest = _valid_manifest()
    coverage = _valid_coverage_payload()
    coverage["coverage"]["expected_scope_count"] = "225"
    (tmp_path / "coverage.json").write_text(json.dumps(coverage), encoding="utf-8")
    assert "legal_review_coverage_counts_invalid" in gate_module._review_coverage_blockers(
        manifest, tmp_path / "m.json"
    )

    coverage = _valid_coverage_payload()
    coverage["coverage"] = None
    (tmp_path / "coverage.json").write_text(json.dumps(coverage), encoding="utf-8")
    assert "legal_review_coverage_evidence_invalid" in gate_module._review_coverage_blockers(
        manifest, tmp_path / "m.json"
    )

    coverage = _valid_coverage_payload()
    coverage.pop("pattern_reconciliation")
    coverage.pop("individual_review")
    (tmp_path / "coverage.json").write_text(json.dumps(coverage), encoding="utf-8")
    blockers = gate_module._review_coverage_blockers(manifest, tmp_path / "m.json")
    assert "legal_review_pattern_reconciliation_missing" in blockers
    assert "legal_review_individual_evidence_missing" in blockers


def test_committed_release_manifest_non_dict_is_invalid(tmp_path, monkeypatch):
    path = tmp_path / "manifest.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(gate_module, "_release_manifest_path", lambda code: path)
    with pytest.raises(SourceCountryNotReleasedError) as exc:
        gate_module._require_committed_release_evidence("SK")
    assert exc.value.decision.code == "SOURCE_COUNTRY_RELEASE_EVIDENCE_INVALID"


def test_committed_release_manifest_collects_gate_failures(tmp_path, monkeypatch):
    manifest = _valid_manifest()
    manifest.update({
        "source_country": "CZ",
        "expected_scope_count": 0,
        "human_reviewed_scopes": 1,
        "cooperating_state_list_ready": False,
        "final_calculation_policy_ready": False,
        "zero_withholding_notification_scope_ready": False,
        "compliance_calendar_adjustment_ready": False,
        "rendered_report_leakage_gate_ready": False,
        "release_eligible": False,
        "release_status": "pre_release",
        "policy": {"all_expected_scopes_must_be_legally_covered": False},
    })
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(gate_module, "_release_manifest_path", lambda code: path)

    with pytest.raises(SourceCountryNotReleasedError) as exc:
        gate_module._require_committed_release_evidence("SK")
    blockers = set(exc.value.decision.blockers)
    assert {
        "release_manifest_source_country_mismatch",
        "release_manifest_expected_scope_count_invalid",
        "full_human_legal_review_not_completed",
        "country_specific_legal_source_gates_not_ready",
        "source_country_final_calculation_policy_not_ready",
        "source_country_zero_withholding_notification_scope_not_ready",
        "source_country_compliance_calendar_adjustment_not_ready",
        "source_country_rendered_report_leakage_gate_not_ready",
        "release_manifest_not_eligible",
        "release_manifest_status_not_released",
    } <= blockers


def test_release_gate_runtime_false_and_unknown_strategy(monkeypatch):
    real = get_country_config("SK")
    monkeypatch.setattr(
        gate_module,
        "get_country_config",
        lambda code: replace(real, runtime_released=False),
    )
    with pytest.raises(SourceCountryNotReleasedError) as exc:
        require_source_country_analysis_release("SK")
    assert exc.value.decision.code == "SOURCE_COUNTRY_NOT_RELEASED"

    monkeypatch.setattr(
        gate_module,
        "get_country_config",
        lambda code: replace(real, release_gate_strategy="unknown"),
    )
    with pytest.raises(ValueError, match="Unsupported release gate strategy"):
        require_source_country_analysis_release("SK")


def test_release_manifest_default_path_for_config_without_override(monkeypatch):
    real = get_country_config("SK")
    monkeypatch.setattr(
        gate_module,
        "get_country_config",
        lambda code: replace(real, release_manifest_path=None),
    )
    assert gate_module._release_manifest_path("SK").as_posix().endswith(
        "data/legal_reviews/sk_outbound/source_country_release_manifest.json"
    )


def test_runtime_metadata_canonical_loader_validation():
    with pytest.raises(ValueError, match="requires the canonical Stage 6 loader"):
        source_country_runtime_dataset_version("CZ")
    with pytest.raises(ValueError, match="has no dataset identifier"):
        source_country_runtime_dataset_version("CZ", cz_release_loader=lambda: {})


def test_runtime_metadata_manifest_fail_closed_paths(tmp_path, monkeypatch):
    real = get_country_config("SK")
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(metadata_module, "_source_release_manifest_path", lambda code: missing)
    with pytest.raises(ValueError, match="No source-country release manifest"):
        source_country_runtime_dataset_version("SK")

    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(metadata_module, "_source_release_manifest_path", lambda code: bad)
    with pytest.raises(ValueError, match="Invalid source-country release manifest"):
        source_country_runtime_dataset_version("SK")

    cases = [
        ({"source_country": "CZ", "release_status": "released", "release_eligible": True, "dataset_release": "x"}, "mismatch"),
        ({"source_country": "SK", "release_status": "pre_release", "release_eligible": True, "dataset_release": "x"}, "not released"),
        ({"source_country": "SK", "release_status": "released", "release_eligible": True}, "no dataset identifier"),
    ]
    for payload, message in cases:
        bad.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            source_country_runtime_dataset_version("SK")

    monkeypatch.setattr(
        metadata_module,
        "get_country_config",
        lambda code: replace(real, runtime_dataset_strategy="unknown"),
    )
    with pytest.raises(ValueError, match="Unsupported runtime dataset strategy"):
        source_country_runtime_dataset_version("SK")


def test_runtime_metadata_default_manifest_path(monkeypatch):
    real = get_country_config("SK")
    monkeypatch.setattr(
        metadata_module,
        "get_country_config",
        lambda code: replace(real, release_manifest_path=None),
    )
    assert metadata_module._source_release_manifest_path("SK").as_posix().endswith(
        "data/legal_reviews/sk_outbound/source_country_release_manifest.json"
    )


def test_calculation_unregistered_source_uses_legacy_wrappers():
    schedule = build_source_country_withholding_compliance_schedule(
        "AT", "2026-01-10", income_type="interest", decision_status="FINAL", rate_percent=10
    )
    assert schedule["schema_version"] == 2

    result = build_source_country_withholding_tax_calculation(
        "AT", {"amount": "1000", "currency": "CZK"}, decision_status="FINAL", rate_percent=10
    )
    assert result["status"] == "CALCULATED"


def test_calculation_unknown_country_strategies_fail(monkeypatch):
    real = get_country_config("SK")
    monkeypatch.setattr(
        calc_module,
        "get_country_config",
        lambda code: replace(real, compliance_strategy="unknown"),
    )
    with pytest.raises(ValueError, match="No compliance schedule strategy"):
        build_source_country_withholding_compliance_schedule(
            "SK", "2026-01-10", income_type="interest", decision_status="FINAL", rate_percent=10
        )

    monkeypatch.setattr(
        calc_module,
        "get_country_config",
        lambda code: replace(real, calculation_strategy="unknown"),
    )
    with pytest.raises(ValueError, match="No tax calculation strategy"):
        build_source_country_withholding_tax_calculation(
            "SK", {"amount": "1000", "currency": "EUR"}, decision_status="FINAL", rate_percent=10
        )


def test_sk_compliance_pending_outside_subject_and_rate_validation():
    pending = build_source_country_withholding_compliance_schedule(
        "SK", "2026-12-10", income_type="dividend", decision_status="REVIEW_REQUIRED", rate_percent=None
    )
    assert pending["status"] == "PENDING_FINAL_TREATMENT"

    outside = build_source_country_withholding_compliance_schedule(
        "SK", "2026-12-10", income_type="dividend", decision_status="FINAL", rate_percent=None,
        tax_treatment="outside_subject_of_tax",
    )
    assert outside["status"] == "NOT_APPLICABLE"
    assert outside["notification_required"] is False

    exempt = build_source_country_withholding_compliance_schedule(
        "SK", "2026-12-10", income_type="dividend", decision_status="FINAL", rate_percent=None,
        tax_treatment="domestic_exemption",
    )
    assert exempt["status"] == "REVIEW_NOTIFICATION_SCOPE"

    with pytest.raises(ValueError, match="decimal number"):
        build_source_country_withholding_compliance_schedule(
            "SK", "2026-12-10", income_type="interest", decision_status="FINAL", rate_percent="bad"
        )
    for rate in (-1, 101):
        with pytest.raises(ValueError, match="between 0 and 100"):
            build_source_country_withholding_compliance_schedule(
                "SK", "2026-12-10", income_type="interest", decision_status="FINAL", rate_percent=rate
            )


def test_sk_calculation_input_and_non_taxing_paths():
    assert build_source_country_withholding_tax_calculation(
        "SK", None, decision_status="FINAL", rate_percent=10
    ) is None

    with pytest.raises(ValueError, match="Transaction amount must be a decimal number"):
        build_source_country_withholding_tax_calculation(
            "SK", {"currency": "EUR"}, decision_status="FINAL", rate_percent=10
        )
    with pytest.raises(ValueError, match="greater than zero"):
        build_source_country_withholding_tax_calculation(
            "SK", {"amount": "0", "currency": "EUR"}, decision_status="FINAL", rate_percent=10
        )

    pending = build_source_country_withholding_tax_calculation(
        "SK", {"amount": "100", "currency": "EUR"}, decision_status="REVIEW_REQUIRED", rate_percent=None
    )
    assert pending["reason"] == "final_rate_unavailable"

    outside = build_source_country_withholding_tax_calculation(
        "SK", {"amount": "100", "currency": "EUR"}, decision_status="FINAL", rate_percent=None,
        tax_treatment="outside_subject_of_tax",
    )
    assert outside["status"] == "NOT_APPLICABLE"

    exempt = build_source_country_withholding_tax_calculation(
        "SK", {"amount": "100", "currency": "EUR"}, decision_status="FINAL", rate_percent=None,
        tax_treatment="domestic_exemption",
    )
    assert exempt["status"] == "CALCULATED"
    assert exempt["rate_percent"] is None
    assert exempt["withholding_tax_eur"] == "0.00"

    with pytest.raises(ValueError, match="Rate must be a decimal number"):
        build_source_country_withholding_tax_calculation(
            "SK", {"amount": "100", "currency": "EUR"}, decision_status="FINAL", rate_percent="bad"
        )
    for rate in (-1, 101):
        with pytest.raises(ValueError, match="between 0 and 100"):
            build_source_country_withholding_tax_calculation(
                "SK", {"amount": "100", "currency": "EUR"}, decision_status="FINAL", rate_percent=rate
            )


def test_sk_fx_fail_closed_validation_paths():
    base = {"amount": "1000", "currency": "USD"}
    no_date = build_source_country_withholding_tax_calculation(
        "SK", base, decision_status="FINAL", rate_percent=10
    )
    assert no_date["reason"] == "sk_withholding_date_required_for_fx"

    wrong_currency = build_source_country_withholding_tax_calculation(
        "SK", {**base, "exchange_rate": {
            "source": "ECB", "currency": "GBP", "foreign_units_per_eur": "1.1", "effective_date": "2026-01-10"
        }}, decision_status="FINAL", rate_percent=10, transaction_date="2026-01-10"
    )
    assert wrong_currency["reason"] == "sk_exchange_rate_currency_mismatch"

    invalid_date = build_source_country_withholding_tax_calculation(
        "SK", {**base, "exchange_rate": {
            "source": "ECB", "currency": "USD", "foreign_units_per_eur": "1.1", "effective_date": "bad"
        }}, decision_status="FINAL", rate_percent=10, transaction_date="2026-01-10"
    )
    assert invalid_date["reason"] == "sk_exchange_rate_effective_date_invalid"

    with pytest.raises(ValueError, match="foreign-units-per-EUR rate must be a decimal number"):
        build_source_country_withholding_tax_calculation(
            "SK", {**base, "exchange_rate": {
                "source": "NBS", "currency": "USD", "foreign_units_per_eur": "bad", "effective_date": "2026-01-10"
            }}, decision_status="FINAL", rate_percent=10, transaction_date="2026-01-10"
        )
    with pytest.raises(ValueError, match="greater than zero"):
        build_source_country_withholding_tax_calculation(
            "SK", {**base, "exchange_rate": {
                "source": "NBS", "currency": "USD", "foreign_units_per_eur": "0", "effective_date": "2026-01-10"
            }}, decision_status="FINAL", rate_percent=10, transaction_date="2026-01-10"
        )


def test_slovak_business_day_crosses_year_boundary():
    assert calc_module._next_sk_business_day(calc_module.date(2027, 1, 1)).isoformat() == "2027-01-04"
