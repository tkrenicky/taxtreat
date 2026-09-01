import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "legal_reviews" / "sk_outbound" / "runtime_integration_profile.json"


def _load():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def test_sk_runtime_contract_is_country_specific_and_fail_closed():
    payload = _load()

    assert payload["source_country"] == "SK"
    assert payload["runtime_release"] is True
    assert payload["production_released_scopes"] == 0
    assert payload["status"] == "source_country_released_rule_level_fail_closed"
    assert payload["currency"] == "EUR"
    assert payload["fx"]["provider"] is None
    assert payload["fx"]["cnb_must_not_be_used"] is True
    assert payload["legal_sources"]["domestic_law"]["label"] == "zákon č. 595/2003 Z. z."
    assert "/2003/595/20260101.print.html" in payload["legal_sources"]["domestic_law"]["url"]
    assert payload["legal_sources"]["czech_zdp_must_not_be_used"] is True
    assert payload["release_gates"]["czech_runtime_fallback_prohibited"] is True


def test_sk_runtime_contract_preserves_slovak_domestic_precedence():
    payload = _load()
    domestic = payload["domestic_precedence"]

    assert domestic["dividend"][0] == "section_12_7_c_outside_subject_test"
    assert "non_cooperating_state_exception" in domestic["dividend"]
    assert "section_13_eu_interest_relief" in domestic["interest"]
    assert "section_13_eu_royalty_relief" in domestic["royalty"]
    assert payload["mli"]["pair_specific_matching_required"] is True
    assert payload["mli"]["ppt_only_assumption_prohibited"] is True


def test_sk_runtime_contract_uses_slovak_compliance_and_rule_level_fail_closed_release():
    payload = _load()
    compliance = payload["compliance"]
    gates = payload["release_gates"]

    assert compliance["ordinary_form_code"] == "OZN4311v26"
    assert compliance["legal_reference"] == "§ 43 ods. 11"
    assert compliance["periodicity"] == "monthly"
    assert compliance["deadline_rule"] == "15th_day_of_following_month"
    assert compliance["ordinary_annual_wht_return_configured"] is False
    assert gates["all_225_scopes_machine_evidence_required"] is True
    assert gates["official_2026_cooperating_state_list_required"] is True
    assert gates["full_human_legal_review_required"] is False
    assert gates["full_legal_review_coverage_required"] is True
    assert gates["rule_level_hash_or_review_gate_required"] is True
    assert gates["report_and_web_parity_tests_required"] is True
    assert payload["human_review_status"] == "completed_with_pattern_reconciliation_and_mli_reconfirmation"
    assert payload["approval_eligible"] is True
    assert payload["approval_scope"] == "source_country_gate_only"
    assert payload["treaty_rule_release"]["final_rate_allowed_scopes"] == 0
    assert payload["treaty_rule_release"]["fail_closed_scopes"] == 225
    assert payload["treaty_rule_release"]["automatic_production_approval_forbidden"] is True
