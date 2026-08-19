from __future__ import annotations

from taxtreat.tools.build_sk_pre_review_readiness import build_readiness


def test_pre_review_dashboard_preserves_full_scope_and_human_review_policy():
    payload = build_readiness()

    assert payload["source_country"] == "SK"
    assert payload["target"]["country_relationships"] == 75
    assert payload["target"]["treaty_scopes"] == 225
    assert payload["target"]["mli_relationships"] == 46
    assert payload["machine_preparation"]["scopes"] == 225

    assert payload["human_review"]["started"] is True
    assert payload["human_review"]["reviewed_scopes"] == 24
    assert payload["human_review"]["pattern_reconciled_scopes"] == 201
    assert payload["human_review"]["legal_review_covered_scopes"] == 225
    assert payload["human_review"]["completed"] is True
    assert payload["runtime"]["released"] is False
    assert payload["runtime"]["production_released_scopes"] == 0
    assert payload["fail_closed"] is True


def test_pre_review_dashboard_allows_human_review_after_2026_list_ingestion():
    payload = build_readiness()

    assert payload["domestic"]["cooperating_state_list_ingestion_complete"] is True
    assert "official_2026_cooperating_state_list_body_not_ingested" not in payload["blockers"]
    assert payload["all_machine_evidence_ready"] is True
    assert payload["human_review"]["may_start"] is True


def test_mli_instrument_chain_has_no_unexplained_silent_notice_replacement():
    payload = build_readiness()
    chain = payload["mli_instrument_chain"]

    assert chain["relationships"] == 46
    assert chain["resolved_relationships"] + chain["unresolved_notice_mismatches"] == 46


def test_sk_compliance_is_country_specific_and_does_not_reuse_czech_rules():
    payload = build_readiness()
    compliance = payload["compliance"]

    assert compliance["present"] is True
    assert compliance["country_specific"] is True
    assert compliance["monthly_section_43_11_modelled"] is True
    assert compliance["czech_reuse_prohibited"] is True
    assert compliance["form_code"] == "OZN4311v26"
    assert compliance["ordinary_annual_wht_return_configured"] is False
    assert compliance["runtime_release"] is False
    assert "sk_2026_compliance_profile_missing" not in payload["blockers"]
    assert "sk_2026_compliance_profile_incomplete" not in payload["blockers"]


def test_sk_dividend_domestic_model_is_slovak_specific_and_time_correct():
    payload = build_readiness()
    dividend = payload["domestic"]["dividend_model"]

    assert dividend["present"] is True
    assert dividend["slovak_specific"] is True
    assert dividend["outside_subject_rule_modelled"] is True
    assert dividend["2026_source_version"] is True
    assert dividend["non_cooperating_state_gate_preserved"] is True
    assert dividend["distribution_deductibility_required"] is True
    assert dividend["runtime_release"] is False
    assert "sk_dividend_domestic_model_missing" not in payload["blockers"]
    assert "sk_dividend_domestic_model_incomplete" not in payload["blockers"]


def test_sk_prerelease_runtime_manifest_is_fail_closed_when_not_generated():
    payload = build_readiness()
    manifest = payload["prerelease_runtime_manifest"]

    # Clean clones intentionally do not contain machine-generated extraction artifacts.
    # The dedicated runtime-manifest tests validate the complete 225-scope contract
    # with synthetic fixtures. Readiness must therefore either expose a complete
    # generated manifest or fail closed without crashing.
    if manifest is None:
        assert "sk_prerelease_runtime_manifest_not_ready" in payload["blockers"]
        assert payload["human_review"]["may_start"] is False
        assert payload["runtime"]["released"] is False
        return

    assert manifest["scope_count"] == 225
    assert manifest["mli_scopes"] == 138
    assert manifest["non_mli_scopes"] == 87
    assert manifest["primary_summary_fallback_scopes"] == 0
    assert manifest["human_reviewed_scopes"] == 24
    assert manifest["pattern_reconciled_scopes"] == 201
    assert manifest["legal_review_covered_scopes"] == 225
    assert manifest["production_released_scopes"] == 0
    assert manifest["fail_closed"] is True
    assert "sk_prerelease_runtime_manifest_not_ready" not in payload["blockers"]
    assert "sk_prerelease_runtime_manifest_incomplete" not in payload["blockers"]
