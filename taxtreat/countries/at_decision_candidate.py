from __future__ import annotations

from typing import Any

from taxtreat.countries.at_candidate import (
    evaluate_candidate_domestic_precedence,
    evaluate_treaty_collection_mechanism,
)


AT_EU_SWISS_AGREEMENT_URL = (
    "https://eur-lex.europa.eu/legal-content/EN/TXT/?"
    "uri=CELEX:02004A1229(01)-20260101"
)
AT_SECTION_99_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=99"
)
AT_SECTION_100_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=100"
)


def _missing(facts: dict[str, Any], names: tuple[str, ...]) -> list[str]:
    return sorted(name for name in names if name not in facts or facts[name] is None)


def evaluate_royalty_collection_basis_candidate(facts: dict[str, Any]) -> dict[str, Any]:
    """Model the Austrian § 99/§ 100 gross-vs-net withholding routes.

    Rates on a gross basis and on a net-after-expenses basis are deliberately
    represented as different collection candidates.  They must never be
    compared as rates on the same tax base.
    """
    required = (
        "recipient_is_corporation",
        "expense_deduction_option_elected",
    )
    missing = _missing(facts, required)
    gross = {
        "route": "section_99_gross_basis",
        "withholding_base": "gross_revenue",
        "rate_percent_candidate": 20.0,
        "legal_basis": ["§ 99 Abs. 2 Z 1 EStG 1988", "§ 100 Abs. 1 EStG 1988"],
        "official_source_urls": [AT_SECTION_99_URL, AT_SECTION_100_URL],
        "status": "candidate_not_released",
    }
    if missing:
        return {
            "status": "candidate_not_released",
            "selected_route_candidate": None,
            "collection_candidates": [gross],
            "missing_facts": missing,
            "review_required": True,
            "production_release_allowed": False,
        }

    if facts["expense_deduction_option_elected"] is not True:
        return {
            "status": "candidate_not_released",
            "selected_route_candidate": "section_99_gross_basis",
            "collection_candidates": [gross],
            "missing_facts": [],
            "review_required": False,
            "production_release_allowed": False,
        }

    net_required = (
        "recipient_is_eu_or_eea_resident",
        "directly_related_expenses_disclosed_in_writing_before_payment",
        "deducted_expense_payee_is_limited_taxpayer",
        "deducted_expenses_to_limited_taxpayer_eur",
        "domestic_taxation_of_expense_payee_sufficiently_secured",
    )
    net_missing = _missing(facts, net_required)
    if net_missing:
        return {
            "status": "candidate_not_released",
            "selected_route_candidate": None,
            "collection_candidates": [gross],
            "missing_facts": net_missing,
            "review_required": True,
            "production_release_allowed": False,
        }

    blockers: list[str] = []
    if facts["recipient_is_eu_or_eea_resident"] is not True:
        blockers.append("net_expense_route_requires_eu_or_eea_residence")
    if facts["directly_related_expenses_disclosed_in_writing_before_payment"] is not True:
        blockers.append("direct_expenses_not_disclosed_in_writing_before_payment")

    expense_payee_limited = facts["deducted_expense_payee_is_limited_taxpayer"] is True
    deducted_amount = float(facts["deducted_expenses_to_limited_taxpayer_eur"])
    secured = facts["domestic_taxation_of_expense_payee_sufficiently_secured"] is True
    if expense_payee_limited and deducted_amount > 2463 and not secured:
        blockers.append("section_99_2_2_expense_payee_domestic_taxation_not_secured")

    if blockers:
        return {
            "status": "candidate_not_released",
            "selected_route_candidate": "section_99_gross_basis",
            "collection_candidates": [gross],
            "missing_facts": [],
            "legal_blockers": blockers,
            "review_required": True,
            "production_release_allowed": False,
        }

    is_corporation = facts["recipient_is_corporation"] is True
    if is_corporation:
        net = {
            "route": "section_99_net_expense_basis_corporate",
            "withholding_base": "net_revenue_after_admissible_direct_expenses",
            "rate_percent_candidate": 23.0,
            "calendar_year_threshold_eur": None,
            "legal_basis": ["§ 99 Abs. 2 Z 2 EStG 1988", "§ 100 Abs. 1a Z 1 EStG 1988"],
            "official_source_urls": [AT_SECTION_99_URL, AT_SECTION_100_URL],
            "status": "candidate_not_released",
        }
    else:
        net = {
            "route": "section_99_net_expense_basis_noncorporate",
            "withholding_base": "net_revenue_after_admissible_direct_expenses",
            "rate_percent_candidate": None,
            "rate_schedule_candidate": [
                {"up_to_calendar_year_income_eur": 20000.0, "rate_percent": 20.0},
                {"above_calendar_year_income_eur": 20000.0, "rate_percent": 25.0},
            ],
            "legal_basis": ["§ 99 Abs. 2 Z 2 EStG 1988", "§ 100 Abs. 1 EStG 1988"],
            "official_source_urls": [AT_SECTION_99_URL, AT_SECTION_100_URL],
            "status": "candidate_not_released",
        }

    return {
        "status": "candidate_not_released",
        "selected_route_candidate": net["route"],
        "collection_candidates": [gross, net],
        "missing_facts": [],
        "legal_blockers": [],
        "review_required": False,
        "policy": {
            "gross_and_net_rates_have_different_tax_bases": True,
            "twenty_three_percent_corporate_net_rate_applies_from_2024": True,
            "section_99_expense_security_threshold_eur": 2463.0,
        },
        "production_release_allowed": False,
    }


def evaluate_eu_swiss_article9_candidate(
    *,
    recipient_country: str,
    income_type: str,
    facts: dict[str, Any],
) -> dict[str, Any] | None:
    """Evaluate the current EU-Switzerland Article 9 company-payment relief.

    Existing DTT provisions that are more favourable remain unaffected, so
    this function returns a parallel international-relief candidate rather
    than overriding the treaty route.
    """
    if str(recipient_country).upper() != "CH":
        return None
    if income_type not in {"dividend", "interest", "royalty"}:
        return None

    common = (
        "eu_swiss_company_residence_pair_satisfied",
        "neither_company_third_state_resident_under_dtt",
        "companies_subject_to_corporation_tax_without_exemption",
        "companies_are_qualifying_limited_company_forms",
        "eu_swiss_anti_abuse_clear",
    )
    if income_type == "dividend":
        required = common + (
            "direct_ownership_percent",
            "holding_period_months_completed",
        )
    else:
        required = common + (
            "eu_swiss_association_25_percent_test_satisfied",
            "holding_period_months_completed",
        )
    missing = _missing(facts, required)
    if missing:
        return {
            "status": "candidate_not_released",
            "legal_instrument": "EU-Switzerland Agreement Article 9",
            "candidate_treatment": None,
            "source_tax_rate_percent_candidate": None,
            "missing_facts": missing,
            "review_required": True,
            "official_source_url": AT_EU_SWISS_AGREEMENT_URL,
            "production_release_allowed": False,
        }

    common_ok = all(
        facts[name] is True
        for name in common
    )
    holding_ok = float(facts["holding_period_months_completed"]) >= 24
    if income_type == "dividend":
        relation_ok = float(facts["direct_ownership_percent"]) >= 25
    else:
        relation_ok = facts["eu_swiss_association_25_percent_test_satisfied"] is True

    eligible = common_ok and holding_ok and relation_ok
    blockers: list[str] = []
    if not holding_ok:
        blockers.append("eu_swiss_article9_two_year_holding_not_satisfied")
    if not relation_ok:
        blockers.append("eu_swiss_article9_25_percent_relationship_not_satisfied")
    if not common_ok:
        blockers.append("eu_swiss_article9_common_company_conditions_not_satisfied")

    return {
        "status": "candidate_not_released",
        "legal_instrument": "EU-Switzerland Agreement Article 9",
        "candidate_treatment": "source_state_exemption" if eligible else None,
        "source_tax_rate_percent_candidate": 0.0 if eligible else None,
        "eligible_candidate": eligible,
        "missing_facts": [],
        "legal_blockers": blockers,
        "review_required": bool(blockers),
        "official_source_url": AT_EU_SWISS_AGREEMENT_URL,
        "existing_more_favourable_dtt_unaffected": True,
        "must_be_compared_with_dtt": True,
        "production_release_allowed": False,
    }


def evaluate_at_wht_candidate(
    *,
    recipient_country: str,
    income_type: str,
    facts: dict[str, Any],
    treaty_rate_percent: float | None = None,
    treaty_substantive_entitlement_confirmed: bool = False,
    treaty_relief_at_source_documentation_ready: bool = False,
    treaty_relief_at_source_restricted_for_case: bool = False,
) -> dict[str, Any]:
    """Orchestrate Austrian pre-release WHT decision layers deterministically."""
    domestic = evaluate_candidate_domestic_precedence(
        income_type=income_type,
        facts=facts,
    )
    swiss = evaluate_eu_swiss_article9_candidate(
        recipient_country=recipient_country,
        income_type=income_type,
        facts=facts,
    )

    result: dict[str, Any] = {
        "source_country": "AT",
        "recipient_country": str(recipient_country).upper(),
        "income_type": income_type,
        "status": "candidate_not_released",
        "domestic_precedence": domestic,
        "eu_swiss_article9_candidate": swiss,
        "treaty_collection": None,
        "royalty_domestic_collection_basis": None,
        "final_payment_date_withholding_rate_percent": None,
        "selected_legal_route": None,
        "review_required": True,
        "production_release_allowed": False,
        "policy": {
            "domestic_precedence_before_treaty": True,
            "substantive_entitlement_separate_from_collection": True,
            "refund_separate_from_relief_at_source": True,
            "international_special_agreement_does_not_silently_override_more_favourable_dtt": True,
            "fail_closed": True,
        },
    }

    if (
        domestic.get("continue_to_treaty_for_current_withholding") is False
        and domestic.get("withholding_rate_now_candidate") is not None
        and domestic.get("review_required") is False
    ):
        result["final_payment_date_withholding_rate_percent"] = domestic["withholding_rate_now_candidate"]
        result["selected_legal_route"] = "domestic"
        result["review_required"] = False
        return result

    if swiss and swiss.get("eligible_candidate") is True:
        result["final_payment_date_withholding_rate_percent"] = 0.0
        result["selected_legal_route"] = "eu_swiss_article9_candidate"
        result["review_required"] = True
        # Human review still compares this route with the treaty and confirms
        # controlling facts; no production conclusion is released.

    if treaty_substantive_entitlement_confirmed or treaty_rate_percent is not None:
        treaty = evaluate_treaty_collection_mechanism(
            treaty_rate_percent=treaty_rate_percent,
            treaty_substantive_entitlement_confirmed=treaty_substantive_entitlement_confirmed,
            relief_at_source_documentation_ready=treaty_relief_at_source_documentation_ready,
            relief_at_source_restricted_for_case=treaty_relief_at_source_restricted_for_case,
        )
        result["treaty_collection"] = treaty
        if treaty.get("withholding_rate_now_candidate") is not None:
            rate = float(treaty["withholding_rate_now_candidate"])
            current = result["final_payment_date_withholding_rate_percent"]
            if current is None or rate < current:
                result["final_payment_date_withholding_rate_percent"] = rate
                result["selected_legal_route"] = "treaty_relief_at_source_candidate"

    if income_type == "royalty" and domestic.get("withholding_rate_now_candidate") is None:
        result["royalty_domestic_collection_basis"] = evaluate_royalty_collection_basis_candidate(facts)

    return result
