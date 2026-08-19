import taxtreat.services.sk_prerelease_decision as decision_module
from taxtreat.services.sk_prerelease_decision import (
    evaluate_sk_prerelease_candidate,
)


def _manifest(*, fallback=False, mli=True, cooperating_ready=False):
    return {
        "source_country": "SK",
        "policy": {"runtime_release": False},
        "scopes": [{
            "scope_key": ["SK", "AT", "dividend"],
            "source_country": "SK",
            "treaty_machine_evidence_status": (
                "machine_candidate_primary_summary_fallback_not_legal_conclusion"
                if fallback
                else "machine_candidate_not_legal_conclusion"
            ),
            "treaty_semantic_candidate": {
                "rate_candidates": [
                    {"rate_percent": 5.0},
                    {"rate_percent": 15.0},
                ],
                "exclusive_residence_taxation_candidate": False,
                "beneficial_owner_wording_present": True,
                "pe_or_fixed_base_carveout_wording_present": True,
                "holding_period_candidates": [],
                "ownership_linked_rate_candidate_count": 1,
                "evidence_quality": (
                    "official_primary_source_summary_fallback_not_byte_exact"
                    if fallback
                    else "official_primary_source_byte_extracted"
                ),
            },
            "mli_applicable": mli,
            "mli_machine_evidence_status": "completed" if mli else "not_applicable",
            "mli_wht_effective_dates": ["2020-01-01"] if mli else [],
            "cooperating_state_list_ready": cooperating_ready,
        }, {
            "scope_key": ["SK", "AT", "interest"],
            "source_country": "SK",
            "treaty_machine_evidence_status": "machine_candidate_not_legal_conclusion",
            "treaty_semantic_candidate": {
                "rate_candidates": [{"rate_percent": 10.0}],
                "exclusive_residence_taxation_candidate": False,
                "beneficial_owner_wording_present": True,
                "pe_or_fixed_base_carveout_wording_present": True,
                "holding_period_candidates": [],
                "ownership_linked_rate_candidate_count": 0,
                "evidence_quality": "official_primary_source_byte_extracted",
            },
            "mli_applicable": mli,
            "mli_machine_evidence_status": "completed" if mli else "not_applicable",
            "mli_wht_effective_dates": ["2020-01-01"] if mli else [],
            "cooperating_state_list_ready": cooperating_ready,
        }],
    }


def test_dividend_candidate_never_trusts_user_non_cooperating_representation_before_official_list():
    result = evaluate_sk_prerelease_candidate(
        recipient_country="AT",
        income_type="dividend",
        facts={
            "recipient_entity_type": "corporate",
            "distribution_category_is_section_3_1_f": False,
            "distribution_is_tax_deductible_for_payer": False,
            "recipient_is_non_cooperating_state_taxpayer": False,
        },
        manifest=_manifest(cooperating_ready=False),
    )

    assert result.status == "REVIEW_REQUIRED"
    assert result.final_rate_percent is None
    assert result.candidate_domestic_treatment == (
        "section_12_7_c_outside_subject_candidate_pending_cooperating_state_status"
    )
    assert "official_2026_cooperating_state_list_body_not_ingested" in result.blockers
    assert "official_2026_cooperating_state_status_unresolved" in result.blockers
    assert result.runtime_dependency_source_countries == ("SK",)
    assert result.czech_runtime_fallback_used is False
    assert result.runtime_released is False


def test_prerelease_evaluator_never_selects_lowest_treaty_regex_rate():
    result = evaluate_sk_prerelease_candidate(
        recipient_country="AT",
        income_type="dividend",
        facts={
            "recipient_entity_type": "corporate",
            "distribution_category_is_section_3_1_f": True,
            "distribution_is_tax_deductible_for_payer": False,
        },
        manifest=_manifest(),
    )

    assert [
        row["rate_percent"]
        for row in result.treaty_semantic_candidate["rate_candidates"]
    ] == [5.0, 15.0]
    assert result.final_rate_percent is None
    assert result.requires_review is True


def test_taiwan_primary_summary_fallback_adds_explicit_review_blocker():
    result = evaluate_sk_prerelease_candidate(
        recipient_country="AT",
        income_type="dividend",
        facts={
            "recipient_entity_type": "corporate",
            "distribution_category_is_section_3_1_f": False,
            "distribution_is_tax_deductible_for_payer": False,
        },
        manifest=_manifest(fallback=True),
    )

    assert "treaty_primary_summary_fallback_requires_human_review" in result.blockers
    assert result.final_rate_percent is None
    assert result.runtime_released is False


def test_interest_eu_relief_can_be_candidate_but_never_final_before_release():
    facts = {
        "recipient_has_sk_permanent_establishment": False,
        "recipient_sk_pe_registered_under_income_tax_act": False,
        "income_attributable_to_registered_sk_pe": False,
        "recipient_is_legal_person_or_qualifying_pe_of_eu_legal_person": True,
        "recipient_is_eu_taxpayer_or_qualifying_pe": True,
        "recipient_is_beneficial_owner": True,
        "payer_directly_owns_recipient": True,
        "recipient_directly_owns_payer": False,
        "third_eu_legal_person_directly_owns_both": False,
        "direct_capital_percent": 25,
        "holding_period_months": 24,
        "holding_period_will_reach_24_months": True,
    }
    result = evaluate_sk_prerelease_candidate(
        recipient_country="AT",
        income_type="interest",
        facts=facts,
        manifest=_manifest(),
    )

    assert result.candidate_domestic_treatment == "current_exemption_candidate"
    assert result.final_rate_percent is None
    assert result.status == "REVIEW_REQUIRED"
    assert result.runtime_dependency_source_countries == ("SK",)
    assert result.czech_runtime_fallback_used is False


def test_czech_dependency_is_detected_from_actual_domestic_helper_provenance(monkeypatch):
    monkeypatch.setattr(
        decision_module,
        "evaluate_domestic_transaction_candidates",
        lambda income, facts: {
            "source_country": "CZ",
            "registered_pe_exclusion": {
                "applies": False,
                "missing_facts": [],
            },
            "eu_relief": {
                "candidate_treatment": None,
                "missing_facts": [],
            },
        },
    )

    result = evaluate_sk_prerelease_candidate(
        recipient_country="AT",
        income_type="interest",
        facts={},
        manifest=_manifest(),
    )

    assert result.runtime_dependency_source_countries == ("CZ", "SK")
    assert result.czech_runtime_fallback_used is True
    assert "foreign_runtime_dependency_detected" in result.blockers
    assert "czech_runtime_dependency_detected" in result.blockers
    assert result.final_rate_percent is None
    assert result.runtime_released is False


def test_unknown_scope_is_out_of_scope_without_czech_fallback():
    result = evaluate_sk_prerelease_candidate(
        recipient_country="ZZ",
        income_type="dividend",
        manifest=_manifest(),
    )

    assert result.status == "OUT_OF_SCOPE"
    assert result.runtime_dependency_source_countries == ("SK",)
    assert result.czech_runtime_fallback_used is False
    assert result.runtime_released is False
