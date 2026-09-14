from taxtreat.countries.at_procedure_candidate import (
    evaluate_refund_procedure_candidate,
    evaluate_royalty_pe_assessment_candidate,
    evaluate_treaty_source_relief_procedure_candidate,
)


def _source_relief(**updates):
    facts = {
        "recipient_is_legal_entity": True,
        "recipient_has_austrian_residence_or_seat": False,
        "annual_austrian_source_income_eur": 25000,
        "payer_chooses_dba_relief_at_source": True,
        "dba_relief_at_source_restricted_for_case": False,
        "additional_treaty_documents_available": True,
        "ZS-QU2_completed_and_signed": True,
        "foreign_tax_authority_residence_certificate_available": True,
    }
    facts.update(updates)
    return facts


def _refund(**updates):
    facts = {
        "withholding_year_ended": True,
        "electronic_refund_prenotification_submitted": True,
        "prenotification_printed_and_signed": True,
        "foreign_residence_confirmation_obtained": True,
        "postal_submission_to_finanzamt_fuer_grossbetriebe_ready": True,
        "years_since_end_of_withholding_year": 2,
    }
    facts.update(updates)
    return facts


def test_dba_source_relief_for_legal_entity_requires_zs_qu2_and_residence_certificate_above_simplified_threshold():
    result = evaluate_treaty_source_relief_procedure_candidate(_source_relief())
    assert result["relief_at_source_available_candidate"] is True
    assert result["documentation_route_candidate"] == "ZS-QU2"
    assert result["residence_certificate_required_candidate"] is True
    assert result["substantive_treaty_entitlement_determined_here"] is False


def test_low_value_dba_source_relief_can_use_simplified_documentation_candidate():
    facts = _source_relief(annual_austrian_source_income_eur=9000)
    facts.pop("foreign_tax_authority_residence_certificate_available")
    result = evaluate_treaty_source_relief_procedure_candidate(facts)
    assert result["simplified_documentation_candidate"] is True
    assert result["residence_certificate_required_candidate"] is False
    assert result["documentation_route_candidate"] == "simplified_written_declaration"
    assert result["relief_at_source_available_candidate"] is True


def test_individual_dba_source_relief_uses_zs_qu1():
    facts = _source_relief(recipient_is_legal_entity=False)
    facts.pop("ZS-QU2_completed_and_signed")
    facts["ZS-QU1_completed_and_signed"] = True
    result = evaluate_treaty_source_relief_procedure_candidate(facts)
    assert result["documentation_route_candidate"] == "ZS-QU1"
    assert result["relief_at_source_available_candidate"] is True


def test_source_relief_missing_core_or_documentary_facts_fails_closed():
    core = _source_relief()
    core.pop("annual_austrian_source_income_eur")
    result = evaluate_treaty_source_relief_procedure_candidate(core)
    assert result["relief_at_source_available_candidate"] is None
    assert "annual_austrian_source_income_eur" in result["missing_facts"]

    docs = _source_relief()
    docs.pop("ZS-QU2_completed_and_signed")
    blocked = evaluate_treaty_source_relief_procedure_candidate(docs)
    assert blocked["relief_at_source_available_candidate"] is False
    assert "ZS-QU2_completed_and_signed_missing" in blocked["legal_blockers"]

    residence = _source_relief()
    residence.pop("foreign_tax_authority_residence_certificate_available")
    blocked = evaluate_treaty_source_relief_procedure_candidate(residence)
    assert "foreign_tax_authority_residence_certificate_available_missing" in blocked["legal_blockers"]


def test_payer_may_choose_refund_route_even_if_treaty_entitlement_exists():
    result = evaluate_treaty_source_relief_procedure_candidate(
        _source_relief(payer_chooses_dba_relief_at_source=False)
    )
    assert result["relief_at_source_available_candidate"] is False
    assert "payer_did_not_choose_optional_dba_relief_at_source" in result["legal_blockers"]


def test_dba_source_relief_restriction_and_missing_additional_documents_are_explicit_blockers():
    restricted = evaluate_treaty_source_relief_procedure_candidate(
        _source_relief(dba_relief_at_source_restricted_for_case=True)
    )
    assert "dba_entlastungsverordnung_source_relief_restricted_for_case" in restricted["legal_blockers"]

    missing_docs = evaluate_treaty_source_relief_procedure_candidate(
        _source_relief(additional_treaty_documents_available=False)
    )
    assert "additional_treaty_documentation_missing" in missing_docs["legal_blockers"]


def test_current_refund_procedure_requires_electronic_prenotification_then_signed_postal_filing():
    result = evaluate_refund_procedure_candidate(_refund())
    assert result["refund_filing_ready_candidate"] is True
    assert result["competent_authority_candidate"] == "Finanzamt für Großbetriebe"
    assert result["electronic_prenotification_required"] is True
    assert result["prenotification_only_after_end_of_withholding_year"] is True
    assert result["printed_signed_submission_required"] is True
    assert result["postal_submission_required"] is True


def test_refund_missing_core_facts_fails_closed_before_procedure_conclusion():
    facts = _refund()
    facts.pop("years_since_end_of_withholding_year")
    result = evaluate_refund_procedure_candidate(facts)
    assert result["refund_filing_ready_candidate"] is False
    assert "years_since_end_of_withholding_year" in result["missing_facts"]


def test_each_current_refund_filing_step_is_independently_required():
    cases = (
        ("electronic_refund_prenotification_submitted", "electronic_prenotification_missing"),
        ("prenotification_printed_and_signed", "printed_signed_prenotification_missing"),
        ("foreign_residence_confirmation_obtained", "foreign_residence_confirmation_missing"),
        (
            "postal_submission_to_finanzamt_fuer_grossbetriebe_ready",
            "postal_submission_to_finanzamt_fuer_grossbetriebe_not_ready",
        ),
    )
    for fact, blocker in cases:
        result = evaluate_refund_procedure_candidate(_refund(**{fact: False}))
        assert result["refund_filing_ready_candidate"] is False
        assert blocker in result["legal_blockers"]


def test_refund_before_end_of_year_or_after_candidate_five_year_period_fails_closed():
    early = evaluate_refund_procedure_candidate(_refund(withholding_year_ended=False))
    assert early["refund_filing_ready_candidate"] is False
    assert "refund_prenotification_not_permitted_before_end_of_withholding_year" in early["legal_blockers"]

    late = evaluate_refund_procedure_candidate(_refund(years_since_end_of_withholding_year=6))
    assert late["refund_filing_ready_candidate"] is False
    assert "candidate_five_year_refund_period_exceeded" in late["legal_blockers"]


def test_royalty_pe_attribution_changes_final_tax_character_not_payment_date_wht_to_zero():
    result = evaluate_royalty_pe_assessment_candidate({
        "recipient_has_austrian_business_or_pe": True,
        "royalty_attributable_to_austrian_business_or_pe": True,
    })
    assert result["assessment_character_candidate"] == "withholding_creditable_in_austrian_assessment"
    assert result["payment_date_wht_exemption_created_by_pe_attribution"] is False
    assert result["withholding_creditable_candidate"] is True
    assert result["expenses_considered_in_assessment_candidate"] is True


def test_royalty_without_pe_attribution_does_not_create_assessment_credit_candidate():
    result = evaluate_royalty_pe_assessment_candidate({
        "recipient_has_austrian_business_or_pe": False,
        "royalty_attributable_to_austrian_business_or_pe": False,
    })
    assert result["withholding_creditable_candidate"] is False
    assert result["payment_date_wht_exemption_created_by_pe_attribution"] is False


def test_royalty_pe_assessment_missing_facts_fail_closed():
    result = evaluate_royalty_pe_assessment_candidate({
        "recipient_has_austrian_business_or_pe": True,
    })
    assert result["assessment_character_candidate"] is None
    assert "royalty_attributable_to_austrian_business_or_pe" in result["missing_facts"]
    assert result["review_required"] is True
