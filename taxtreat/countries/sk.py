from __future__ import annotations

from datetime import date
from typing import Any

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalDecisionResult,
    TaxTreatment,
)


DIVIDEND_DOMESTIC_REQUIRED_FACTS = (
    "recipient_entity_type",
    "distribution_is_tax_deductible_for_payer",
    "recipient_is_non_cooperating_state_taxpayer",
    "distribution_category_is_section_3_1_f",
)


def evaluate_domestic_precedence(
    *,
    recipient_country: str,
    income_type: str,
    transaction_date: date,
    facts: dict[str, Any],
) -> LegalDecisionResult | None:
    """Evaluate Slovak source-country domestic precedence.

    Returning None means that no terminal domestic result has been reached
    and canonical treaty/MLI evaluation may continue.
    """

    del recipient_country
    del transaction_date

    if income_type != "dividend":
        return None

    missing = [
        name
        for name in DIVIDEND_DOMESTIC_REQUIRED_FACTS
        if name not in facts or facts[name] is None
    ]

    if missing:
        return LegalDecisionResult(
            status=DecisionStatus.REVIEW_REQUIRED,
            requires_review=True,
            rate=None,
            candidate_rate=None,
            eligible=False,
            missing_facts=sorted(missing),
            explanation=[
                "Slovak domestic dividend treatment under § 12 ods. 7 "
                "písm. c) cannot be resolved until all required domestic "
                "transaction facts are known."
            ],
        )

    outside_subject = (
        facts["recipient_entity_type"] == "corporate"
        and facts["distribution_is_tax_deductible_for_payer"] is False
        and facts["recipient_is_non_cooperating_state_taxpayer"] is False
        and facts["distribution_category_is_section_3_1_f"] is False
    )

    if not outside_subject:
        return None

    rule_id = "SK-DIV-DOMESTIC-SECTION-12-7-C"

    return LegalDecisionResult(
        status=DecisionStatus.FINAL,
        rate=None,
        candidate_rate=None,
        selected_rule_id=rule_id,
        candidate_rule_id=rule_id,
        tax_treatment=TaxTreatment.OUTSIDE_SUBJECT_OF_TAX,
        candidate_tax_treatment=TaxTreatment.OUTSIDE_SUBJECT_OF_TAX,
        applied_rule_ids=[rule_id],
        eligible=True,
        requires_review=False,
        explanation=[
            "The dividend is outside the subject of Slovak corporate "
            "income tax under § 12 ods. 7 písm. c). Treaty and MLI "
            "rate analysis is therefore not applied."
        ],
        citations=[
            {
                "rule_id": rule_id,
                "legal_instrument": "zákon č. 595/2003 Z. z.",
                "legal_layer": "domestic",
                "rate": None,
                "tax_treatment": (
                    TaxTreatment.OUTSIDE_SUBJECT_OF_TAX.value
                ),
                "source_id": "SK-ITA-595-2003-SECTION-12-7-C",
                "source_url": (
                    "https://static.slov-lex.sk/static/SK/ZZ/2003/595/"
                    "20260101.print.html"
                ),
                "article": "§ 12",
                "paragraph": "ods. 7 písm. c)",
                "excerpt": None,
                "excerpt_sha256": None,
                "conditions": [
                    {
                        "fact": "recipient_entity_type",
                        "operator": "==",
                        "value": "corporate",
                        "fact_source": "transaction",
                    },
                    {
                        "fact": (
                            "distribution_is_tax_deductible_for_payer"
                        ),
                        "operator": "==",
                        "value": False,
                        "fact_source": "transaction",
                    },
                    {
                        "fact": (
                            "recipient_is_non_cooperating_state_taxpayer"
                        ),
                        "operator": "==",
                        "value": False,
                        "fact_source": "transaction",
                    },
                    {
                        "fact": (
                            "distribution_category_is_section_3_1_f"
                        ),
                        "operator": "==",
                        "value": False,
                        "fact_source": "transaction",
                    },
                ],
            }
        ],
        layer_results=[
            {
                "layer": "domestic",
                "rule_id": rule_id,
                "effect": "rate",
                "rate": None,
                "tax_treatment": (
                    TaxTreatment.OUTSIDE_SUBJECT_OF_TAX.value
                ),
                "outcome": "applicable",
                "verification_status": "verified",
                "missing_facts": [],
                "failed_conditions": [],
            }
        ],
        dataset_release="sk-source-country-release-2026-08-21.2",
    )
