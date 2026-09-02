from __future__ import annotations

from typing import Any


AT_BMF_SOURCE_RELIEF_URL = (
    "https://www.bmf.gv.at/themen/steuern/internationales-steuerrecht/"
    "rueckerstattung/Entlastung-von-%C3%B6sterreichischen-Abzugsteuern-an-der-Quelle.html"
)
AT_BMF_REFUND_URL = (
    "https://www.bmf.gv.at/themen/steuern/internationales-steuerrecht/"
    "rueckerstattung/rueckerstattung-oesterreichischer-abzugsteuer.html"
)
AT_BMF_FORMS_URL = (
    "https://service.bmf.gv.at/service/anwend/formulare/show_mast.asp?"
    "Styp=KAT&Typ=SM&s=Doppelbesteuerungsabkommen"
)
AT_SECTION_102_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=102"
)


def _missing(facts: dict[str, Any], names: tuple[str, ...]) -> list[str]:
    return sorted(name for name in names if name not in facts or facts[name] is None)


def evaluate_treaty_source_relief_procedure_candidate(facts: dict[str, Any]) -> dict[str, Any]:
    """Evaluate procedural readiness for Austrian DTT relief at source.

    This does not determine substantive treaty entitlement.  It only decides
    whether an already confirmed treaty entitlement can be implemented at the
    payment date under the Austrian DBA-Entlastungsverordnung framework.
    """
    required = (
        "recipient_is_legal_entity",
        "recipient_has_austrian_residence_or_seat",
        "annual_austrian_source_income_eur",
        "payer_chooses_dba_relief_at_source",
        "dba_relief_at_source_restricted_for_case",
        "additional_treaty_documents_available",
    )
    missing = _missing(facts, required)
    if missing:
        return {
            "status": "candidate_not_released",
            "relief_at_source_available_candidate": None,
            "documentation_route_candidate": None,
            "missing_facts": missing,
            "review_required": True,
            "official_source_urls": [AT_BMF_SOURCE_RELIEF_URL, AT_BMF_FORMS_URL],
            "production_release_allowed": False,
        }

    if facts["recipient_is_legal_entity"] is not True:
        form = "ZS-QU1"
    else:
        form = "ZS-QU2"

    simplified = (
        facts["recipient_has_austrian_residence_or_seat"] is False
        and float(facts["annual_austrian_source_income_eur"]) <= 10000
    )
    documentation_required = [
        f"{form}_completed_and_signed",
        "additional_treaty_documents_available",
    ]
    if not simplified:
        documentation_required.append("foreign_tax_authority_residence_certificate_available")

    doc_missing = _missing(facts, tuple(documentation_required))
    blockers: list[str] = []
    if facts["payer_chooses_dba_relief_at_source"] is not True:
        blockers.append("payer_did_not_choose_optional_dba_relief_at_source")
    if facts["dba_relief_at_source_restricted_for_case"] is True:
        blockers.append("dba_entlastungsverordnung_source_relief_restricted_for_case")
    if facts["additional_treaty_documents_available"] is not True:
        blockers.append("additional_treaty_documentation_missing")
    for name in doc_missing:
        if name != "additional_treaty_documents_available":
            blockers.append(name + "_missing")

    available = not blockers
    return {
        "status": "candidate_not_released",
        "relief_at_source_available_candidate": available,
        "documentation_route_candidate": "simplified_written_declaration" if simplified else form,
        "simplified_documentation_candidate": simplified,
        "residence_certificate_required_candidate": not simplified,
        "required_documentation": documentation_required,
        "missing_facts": [],
        "legal_blockers": sorted(set(blockers)),
        "review_required": bool(blockers),
        "substantive_treaty_entitlement_determined_here": False,
        "official_source_urls": [AT_BMF_SOURCE_RELIEF_URL, AT_BMF_FORMS_URL],
        "production_release_allowed": False,
    }


def evaluate_refund_procedure_candidate(facts: dict[str, Any]) -> dict[str, Any]:
    """Model the current § 240a BAO / BMF refund filing procedure."""
    required = (
        "withholding_year_ended",
        "electronic_refund_prenotification_submitted",
        "prenotification_printed_and_signed",
        "foreign_residence_confirmation_obtained",
        "postal_submission_to_finanzamt_fuer_grossbetriebe_ready",
        "years_since_end_of_withholding_year",
    )
    missing = _missing(facts, required)
    if missing:
        return {
            "status": "candidate_not_released",
            "refund_filing_ready_candidate": False,
            "missing_facts": missing,
            "review_required": True,
            "production_release_allowed": False,
            "official_source_url": AT_BMF_REFUND_URL,
        }

    blockers: list[str] = []
    if facts["withholding_year_ended"] is not True:
        blockers.append("refund_prenotification_not_permitted_before_end_of_withholding_year")
    if facts["electronic_refund_prenotification_submitted"] is not True:
        blockers.append("electronic_prenotification_missing")
    if facts["prenotification_printed_and_signed"] is not True:
        blockers.append("printed_signed_prenotification_missing")
    if facts["foreign_residence_confirmation_obtained"] is not True:
        blockers.append("foreign_residence_confirmation_missing")
    if facts["postal_submission_to_finanzamt_fuer_grossbetriebe_ready"] is not True:
        blockers.append("postal_submission_to_finanzamt_fuer_grossbetriebe_not_ready")
    if float(facts["years_since_end_of_withholding_year"]) > 5:
        blockers.append("candidate_five_year_refund_period_exceeded")

    return {
        "status": "candidate_not_released",
        "refund_filing_ready_candidate": not blockers,
        "competent_authority_candidate": "Finanzamt für Großbetriebe",
        "electronic_prenotification_required": True,
        "prenotification_only_after_end_of_withholding_year": True,
        "printed_signed_submission_required": True,
        "foreign_residence_confirmation_required": True,
        "postal_submission_required": True,
        "candidate_refund_period_years": 5,
        "missing_facts": [],
        "legal_blockers": blockers,
        "review_required": bool(blockers),
        "official_source_url": AT_BMF_REFUND_URL,
        "production_release_allowed": False,
    }


def evaluate_royalty_pe_assessment_candidate(facts: dict[str, Any]) -> dict[str, Any]:
    """Separate payment-date withholding from final-tax/assessment character.

    Royalty income attributable to an Austrian business/PE can enter Austrian
    assessment, where withholding is creditable.  That is not the same as a
    payment-date exemption and therefore must not synthesize a 0% WHT result.
    """
    missing = _missing(
        facts,
        (
            "recipient_has_austrian_business_or_pe",
            "royalty_attributable_to_austrian_business_or_pe",
        ),
    )
    if missing:
        return {
            "status": "candidate_not_released",
            "assessment_character_candidate": None,
            "missing_facts": missing,
            "review_required": True,
            "production_release_allowed": False,
            "official_source_url": AT_SECTION_102_URL,
        }

    attributable = (
        facts["recipient_has_austrian_business_or_pe"] is True
        and facts["royalty_attributable_to_austrian_business_or_pe"] is True
    )
    return {
        "status": "candidate_not_released",
        "assessment_character_candidate": (
            "withholding_creditable_in_austrian_assessment" if attributable
            else "withholding_potentially_final_subject_to_other_relief"
        ),
        "payment_date_wht_exemption_created_by_pe_attribution": False,
        "withholding_creditable_candidate": attributable,
        "expenses_considered_in_assessment_candidate": attributable,
        "missing_facts": [],
        "review_required": False,
        "official_source_url": AT_SECTION_102_URL,
        "production_release_allowed": False,
    }
