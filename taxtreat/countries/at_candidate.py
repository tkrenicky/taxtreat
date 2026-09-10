from __future__ import annotations

from typing import Any


AT_SECTION_94_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=94"
)
AT_SECTION_98_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=98"
)
AT_SECTION_99A_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=99a"
)
AT_SECTION_99_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=99"
)
AT_SECTION_100_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004570&Paragraf=100"
)
AT_KSTG_21_URL = (
    "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&"
    "Gesetzesnummer=10004569&Paragraf=21"
)


def _missing(facts: dict[str, Any], names: tuple[str, ...]) -> list[str]:
    return sorted(name for name in names if name not in facts or facts[name] is None)


def _result(
    *,
    substantive_treatment: str | None,
    domestic_rate_percent: float | None,
    withholding_rate_now: float | None,
    relief_mechanism: str,
    refund_candidate: bool,
    continue_to_treaty: bool,
    legal_basis: list[str],
    official_source_urls: list[str],
    missing_facts: list[str] | None = None,
    blockers: list[str] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    missing_facts = sorted(set(missing_facts or []))
    blockers = sorted(set(blockers or []))
    return {
        "status": "candidate_not_released",
        "substantive_treatment_candidate": substantive_treatment,
        "domestic_rate_percent_candidate": domestic_rate_percent,
        "withholding_rate_now_candidate": withholding_rate_now,
        "relief_mechanism_candidate": relief_mechanism,
        "refund_candidate": refund_candidate,
        "continue_to_treaty_for_current_withholding": continue_to_treaty,
        "missing_facts": missing_facts,
        "legal_blockers": blockers,
        "review_required": bool(missing_facts or blockers),
        "legal_basis": legal_basis,
        "official_source_urls": official_source_urls,
        "notes": list(notes or []),
        "production_release_allowed": False,
    }


def evaluate_dividend_candidate(facts: dict[str, Any]) -> dict[str, Any]:
    required = (
        "recipient_is_corporation",
        "recipient_is_qualifying_eu_parent",
        "ownership_percent",
        "holding_period_months_completed",
        "anti_abuse_or_hidden_distribution_trigger",
    )
    missing = _missing(facts, required)
    if missing:
        return _result(
            substantive_treatment=None,
            domestic_rate_percent=23.0 if facts.get("recipient_is_corporation") is True else None,
            withholding_rate_now=None,
            relief_mechanism="unresolved",
            refund_candidate=False,
            continue_to_treaty=False,
            legal_basis=["§ 93 Abs. 1a EStG 1988", "§ 94 Z 2 EStG 1988"],
            official_source_urls=[AT_SECTION_94_URL],
            missing_facts=missing,
            notes=["Domestic dividend relief must be resolved before treaty relief."],
        )

    is_corporation = facts["recipient_is_corporation"] is True
    qualifying_parent = facts["recipient_is_qualifying_eu_parent"] is True
    ownership = float(facts["ownership_percent"])
    holding = float(facts["holding_period_months_completed"])
    anti_abuse = facts["anti_abuse_or_hidden_distribution_trigger"] is True

    if qualifying_parent and ownership >= 10:
        if holding >= 12 and not anti_abuse:
            return _result(
                substantive_treatment="domestic_exemption",
                domestic_rate_percent=0.0,
                withholding_rate_now=0.0,
                relief_mechanism="relief_at_source",
                refund_candidate=False,
                continue_to_treaty=False,
                legal_basis=["§ 94 Z 2 EStG 1988"],
                official_source_urls=[AT_SECTION_94_URL],
                notes=[
                    "The qualifying EU parent exemption precedes treaty-rate analysis.",
                    "The one-year holding period must already be satisfied for immediate source relief.",
                ],
            )

        if holding < 12:
            return _result(
                substantive_treatment="directive_relief_candidate_after_holding_period",
                domestic_rate_percent=23.0 if is_corporation else None,
                withholding_rate_now=None,
                relief_mechanism="provisional_withholding_then_refund",
                refund_candidate=True,
                continue_to_treaty=True,
                legal_basis=["§ 94 Z 2 EStG 1988"],
                official_source_urls=[AT_SECTION_94_URL],
                notes=[
                    "Immediate § 94 Z 2 source relief is unavailable before completion of the one-year holding period.",
                    "Treaty entitlement must still be checked because it may reduce the amount withheld before a later directive refund.",
                ],
            )

        return _result(
            substantive_treatment="directive_refund_candidate",
            domestic_rate_percent=23.0 if is_corporation else None,
            withholding_rate_now=None,
            relief_mechanism="withholding_then_refund_review",
            refund_candidate=True,
            continue_to_treaty=True,
            legal_basis=["§ 94 Z 2 EStG 1988"],
            official_source_urls=[AT_SECTION_94_URL],
            blockers=["anti_abuse_or_hidden_distribution_source_relief_block"],
            notes=[
                "A source-relief block does not itself establish final loss of directive relief; refund eligibility requires factual review.",
            ],
        )

    portfolio_required = (
        "recipient_is_eu_or_eea_resident",
        "recipient_state_has_comprehensive_administrative_assistance",
        "wht_creditable_in_residence_state",
    )
    portfolio_missing = _missing(facts, portfolio_required) if is_corporation else []
    refund_candidate = False
    notes = ["No immediate § 94 Z 2 EU-parent exemption was established; treaty analysis continues."]
    if is_corporation and not portfolio_missing:
        residence_ok = (
            facts["recipient_is_eu_or_eea_resident"] is True
            or (
                facts["recipient_state_has_comprehensive_administrative_assistance"] is True
                and ownership < 10
            )
        )
        refund_candidate = residence_ok and facts["wht_creditable_in_residence_state"] is False
        if refund_candidate:
            notes.append(
                "§ 21 Abs. 1 Z 1a KStG is a post-withholding refund remedy and must not be represented as relief at source."
            )

    return _result(
        substantive_treatment="taxable_subject_to_treaty",
        domestic_rate_percent=23.0 if is_corporation else None,
        withholding_rate_now=None,
        relief_mechanism="treaty_relief_at_source_or_refund_to_be_determined",
        refund_candidate=refund_candidate,
        continue_to_treaty=True,
        legal_basis=["§ 93 Abs. 1a EStG 1988", "§ 21 Abs. 1 Z 1a KStG 1988"],
        official_source_urls=[AT_SECTION_94_URL, AT_KSTG_21_URL],
        missing_facts=portfolio_missing,
        notes=notes,
    )


def evaluate_interest_candidate(facts: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(facts, ("recipient_is_natural_person", "interest_is_special_section_99_category"))
    if missing:
        return _result(
            substantive_treatment=None,
            domestic_rate_percent=None,
            withholding_rate_now=None,
            relief_mechanism="unresolved",
            refund_candidate=False,
            continue_to_treaty=False,
            legal_basis=["§ 98 Abs. 1 EStG 1988"],
            official_source_urls=[AT_SECTION_98_URL],
            missing_facts=missing,
        )

    if facts["recipient_is_natural_person"] is False and facts["interest_is_special_section_99_category"] is False:
        return _result(
            substantive_treatment="outside_limited_tax_liability",
            domestic_rate_percent=0.0,
            withholding_rate_now=0.0,
            relief_mechanism="no_domestic_withholding",
            refund_candidate=False,
            continue_to_treaty=False,
            legal_basis=["§ 98 Abs. 1 Z 5 EStG 1988"],
            official_source_urls=[AT_SECTION_98_URL],
            notes=[
                "Current § 98 excludes interest not received by natural persons from Austrian limited tax liability.",
                "Older documentation/declaration descriptions must not be treated as current corporate-interest eligibility conditions without a separate legal basis.",
            ],
        )

    return evaluate_section_99a_candidate("interest", facts)


def evaluate_section_99a_candidate(income_type: str, facts: dict[str, Any]) -> dict[str, Any]:
    if income_type not in {"interest", "royalty"}:
        raise ValueError("§ 99a applies only to interest or royalty candidates")

    required = (
        "payer_and_recipient_section_99a_entity_conditions_satisfied",
        "beneficial_owner",
        "section_99a_association_test_satisfied",
        "holding_period_months_completed",
        "section_99a_confirmations_available_at_payment",
        "tax_avoidance_abuse_trigger",
        "profit_participating_claim",
        "amount_exceeds_arm_length",
    )
    missing = _missing(facts, required)
    baseline = 20.0 if income_type == "royalty" else None
    if missing:
        return _result(
            substantive_treatment=None,
            domestic_rate_percent=baseline,
            withholding_rate_now=None,
            relief_mechanism="unresolved",
            refund_candidate=False,
            continue_to_treaty=False,
            legal_basis=["§ 99a EStG 1988"],
            official_source_urls=[AT_SECTION_99A_URL],
            missing_facts=missing,
        )

    substantive = (
        facts["payer_and_recipient_section_99a_entity_conditions_satisfied"] is True
        and facts["beneficial_owner"] is True
        and facts["section_99a_association_test_satisfied"] is True
        and facts["profit_participating_claim"] is False
        and facts["tax_avoidance_abuse_trigger"] is False
    )
    holding_complete = float(facts["holding_period_months_completed"]) >= 12
    confirmations_ready = facts["section_99a_confirmations_available_at_payment"] is True
    arm_length_ok = facts["amount_exceeds_arm_length"] is False

    if substantive and holding_complete and confirmations_ready and arm_length_ok:
        return _result(
            substantive_treatment="domestic_exemption",
            domestic_rate_percent=0.0,
            withholding_rate_now=0.0,
            relief_mechanism="relief_at_source",
            refund_candidate=False,
            continue_to_treaty=False,
            legal_basis=["§ 98 Abs. 2 EStG 1988", "§ 99a EStG 1988"],
            official_source_urls=[AT_SECTION_98_URL, AT_SECTION_99A_URL],
        )

    if substantive and arm_length_ok and (not holding_complete or not confirmations_ready):
        return _result(
            substantive_treatment="section_99a_refund_candidate",
            domestic_rate_percent=baseline,
            withholding_rate_now=None,
            relief_mechanism="withholding_then_section_99a_refund",
            refund_candidate=True,
            continue_to_treaty=True,
            legal_basis=["§ 99a Abs. 8 EStG 1988"],
            official_source_urls=[AT_SECTION_99A_URL],
            notes=[
                "§ 99a source relief is unavailable when the one-year holding period or required confirmations are missing at payment time.",
                "The statutory refund route is separate from treaty relief that may affect the amount initially withheld.",
            ],
        )

    blockers: list[str] = []
    if facts["profit_participating_claim"] is True:
        blockers.append("profit_participating_claim_excluded_from_section_99a")
    if facts["tax_avoidance_abuse_trigger"] is True:
        blockers.append("section_99a_anti_abuse_exclusion")
    if facts["amount_exceeds_arm_length"] is True:
        blockers.append("section_99a_only_arm_length_amount_can_be_exempt")
    if facts["beneficial_owner"] is False:
        blockers.append("beneficial_owner_not_satisfied")
    if facts["section_99a_association_test_satisfied"] is False:
        blockers.append("section_99a_association_test_not_satisfied")
    if facts["payer_and_recipient_section_99a_entity_conditions_satisfied"] is False:
        blockers.append("section_99a_entity_or_tax_conditions_not_satisfied")

    return _result(
        substantive_treatment="taxable_subject_to_treaty",
        domestic_rate_percent=baseline,
        withholding_rate_now=None,
        relief_mechanism="treaty_relief_at_source_or_refund_to_be_determined",
        refund_candidate=False,
        continue_to_treaty=True,
        legal_basis=["§ 99a EStG 1988"],
        official_source_urls=[AT_SECTION_99A_URL],
        blockers=blockers,
    )


def evaluate_royalty_candidate(facts: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(facts, ("royalty_within_section_99_1_3",))
    if missing:
        return _result(
            substantive_treatment=None,
            domestic_rate_percent=None,
            withholding_rate_now=None,
            relief_mechanism="unresolved",
            refund_candidate=False,
            continue_to_treaty=False,
            legal_basis=["§ 99 Abs. 1 Z 3 EStG 1988", "§ 100 EStG 1988"],
            official_source_urls=[AT_SECTION_99_URL, AT_SECTION_100_URL],
            missing_facts=missing,
        )
    if facts["royalty_within_section_99_1_3"] is False:
        return _result(
            substantive_treatment=None,
            domestic_rate_percent=None,
            withholding_rate_now=None,
            relief_mechanism="outside_generic_royalty_route",
            refund_candidate=False,
            continue_to_treaty=False,
            legal_basis=["§ 99 Abs. 1 Z 3 EStG 1988"],
            official_source_urls=[AT_SECTION_99_URL],
            blockers=["payment_not_classified_within_section_99_1_3_royalty_route"],
        )
    return evaluate_section_99a_candidate("royalty", facts)


def evaluate_treaty_collection_mechanism(
    *,
    treaty_rate_percent: float | None,
    treaty_substantive_entitlement_confirmed: bool,
    relief_at_source_documentation_ready: bool,
    relief_at_source_restricted_for_case: bool,
) -> dict[str, Any]:
    """Keep treaty entitlement separate from the Austrian collection mechanism."""
    if not treaty_substantive_entitlement_confirmed or treaty_rate_percent is None:
        return {
            "status": "unresolved",
            "withholding_rate_now_candidate": None,
            "relief_mechanism_candidate": "unresolved",
            "refund_candidate": False,
            "production_release_allowed": False,
        }
    if relief_at_source_documentation_ready and not relief_at_source_restricted_for_case:
        return {
            "status": "candidate_not_released",
            "withholding_rate_now_candidate": float(treaty_rate_percent),
            "relief_mechanism_candidate": "treaty_relief_at_source",
            "refund_candidate": False,
            "production_release_allowed": False,
        }
    return {
        "status": "candidate_not_released",
        "withholding_rate_now_candidate": None,
        "relief_mechanism_candidate": "domestic_withholding_then_treaty_refund",
        "refund_candidate": True,
        "production_release_allowed": False,
    }


def evaluate_candidate_domestic_precedence(
    *,
    income_type: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    """Pre-release Austrian domestic/procedural decision layer.

    This function is deliberately not registered in the runtime country registry.
    It is a deterministic candidate implementation for legal review and tests.
    """
    if income_type == "dividend":
        return evaluate_dividend_candidate(facts)
    if income_type == "interest":
        return evaluate_interest_candidate(facts)
    if income_type == "royalty":
        return evaluate_royalty_candidate(facts)
    raise ValueError(f"Unsupported AT income type: {income_type}")
