from __future__ import annotations

from typing import Any, Mapping


FACT_GUIDANCE: dict[str, dict[str, Any]] = {
    "beneficial_owner": {
        "prompt": "Is the recipient the beneficial owner of the income?",
        "why": "Treaty relief commonly depends on beneficial-owner status.",
        "documents": [
            "Beneficial-owner declaration",
            "Relevant agreements and payment-flow evidence",
        ],
    },
    "recipient_is_treaty_resident": {
        "prompt": "Is the recipient resident for treaty purposes?",
        "why": "Treaty access requires qualifying residence.",
        "documents": ["Current tax-residence certificate"],
    },
    "permanent_establishment_connection": {
        "prompt": (
            "Is the right or asset connected with a permanent establishment "
            "in the Czech Republic?"
        ),
        "why": "A permanent-establishment connection can change the tax path.",
        "documents": [
            "Organizational structure",
            "Permanent-establishment analysis",
        ],
    },
    "arm_length_amount": {
        "prompt": "Is the full payment amount arm's length?",
        "why": "Treaty limits may apply only to an arm's-length amount.",
        "documents": [
            "Intercompany agreement",
            "Transfer-pricing support",
        ],
    },
    "payment_is_arm_length_amount": {
        "prompt": "Is the payment limited to an arm's-length amount?",
        "why": "Related-party excess may follow a different tax treatment.",
        "documents": [
            "Intercompany agreement",
            "Transfer-pricing support",
        ],
    },
    "ownership_percent": {
        "prompt": "What ownership percentage does the recipient hold?",
        "why": "Ownership thresholds can select a reduced dividend rate.",
        "response_type": "decimal_percent",
        "documents": [
            "Share register",
            "Ownership chart",
        ],
    },
    "direct_ownership": {
        "prompt": "Is the qualifying ownership held directly?",
        "why": "Some relief paths require direct ownership.",
        "documents": ["Share register", "Ownership chart"],
    },
    "direct_or_indirect_voting_ownership": {
        "prompt": "What direct or indirect voting ownership is held?",
        "why": "Treaty rate thresholds may use voting ownership.",
        "response_type": "decimal_percent",
        "documents": ["Share register", "Ownership chart"],
    },
    "holding_period_months": {
        "prompt": "For how many completed months has the interest been held?",
        "why": "A minimum holding period may be required.",
        "response_type": "integer",
        "documents": [
            "Acquisition documents",
            "Dated share-register extract",
        ],
    },
    "holding_period_will_reach_months": {
        "prompt": "Will the required holding period be completed?",
        "why": "Some relief can depend on subsequent completion.",
        "documents": ["Acquisition date and expected holding evidence"],
    },
    "recipient_entity_type": {
        "prompt": "What is the legal form and tax classification of the recipient?",
        "why": "Entity type can determine eligibility for a relief path.",
        "response_type": "text",
        "documents": [
            "Commercial-register extract",
            "Constitutional documents",
        ],
    },
    "recipient_is_qualifying_company_form": {
        "prompt": "Does the recipient have a qualifying company form?",
        "why": "EU relief requires an eligible legal form.",
        "documents": [
            "Commercial-register extract",
            "Constitutional documents",
        ],
    },
    "recipient_subject_to_qualifying_corporate_tax": {
        "prompt": (
            "Is the recipient subject to qualifying corporate tax without "
            "an elective exemption?"
        ),
        "why": "EU relief requires qualifying tax-subject status.",
        "documents": [
            "Tax-status confirmation",
            "Residence certificate",
        ],
    },
    "royalty_category": {
        "prompt": "What legal category best describes the royalty payment?",
        "why": "Different royalty categories may follow different provisions.",
        "response_type": "text",
        "documents": ["Licence agreement", "Description of licensed rights"],
    },
    "special_article_11_3_exemption": {
        "prompt": "Does a specific Article 11(3) interest exemption apply?",
        "why": "A special treaty exemption may override the general rate.",
        "documents": ["Loan agreement", "Evidence for the claimed exemption"],
    },
}

DETERMINATION_GUIDANCE = {
    "treaty_ppt_passed": {
        "prompt": "Has the treaty principal-purpose test been reviewed and passed?",
        "why": "PPT is a legal determination and is not inferred from client facts.",
        "documents": [
            "Transaction purpose memorandum",
            "Substance and commercial-rationale evidence",
        ],
    },
}


def _humanize(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def _question_for_missing_fact(missing: str) -> dict[str, Any]:
    prefix = None
    name = missing
    if ":" in missing:
        prefix, name = missing.split(":", 1)

    if prefix == "legal_fact":
        return {
            "question_id": missing,
            "input_path": None,
            "category": "legal_evidence",
            "client_answerable": False,
            "response_type": "professional_review",
            "prompt": f"Resolve the legal fact: {_humanize(name)}.",
            "why": (
                "This item must come from released legal evidence or "
                "professional review, not a client assertion."
            ),
            "required_documents": [],
        }

    if prefix == "determination":
        guidance = DETERMINATION_GUIDANCE.get(name, {})
        return {
            "question_id": missing,
            "input_path": f"determinations.{name}",
            "category": "legal_determination",
            "client_answerable": False,
            "response_type": "reviewed_boolean",
            "prompt": guidance.get(
                "prompt",
                f"Has {_humanize(name).lower()} been professionally determined?",
            ),
            "why": guidance.get(
                "why",
                "This is an explicit legal determination, not an inferred fact.",
            ),
            "required_documents": guidance.get("documents", []),
        }

    guidance = FACT_GUIDANCE.get(name, {})
    return {
        "question_id": missing,
        "input_path": f"facts.{name}",
        "category": "transaction_fact",
        "client_answerable": True,
        "response_type": guidance.get("response_type", "boolean"),
        "prompt": guidance.get(
            "prompt",
            f"Please confirm: {_humanize(name)}.",
        ),
        "why": guidance.get(
            "why",
            "The released rule path requires this transaction fact.",
        ),
        "required_documents": guidance.get("documents", []),
    }


def build_intake_plan(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> dict[str, Any]:
    questions = [
        _question_for_missing_fact(missing)
        for missing in analysis.get("missing_facts", [])
    ]

    calculation = analysis.get("withholding_tax_calculation")
    if (
        isinstance(calculation, Mapping)
        and calculation.get("status") == "NOT_CALCULATED"
        and calculation.get("reason")
        not in {None, "final_rate_unavailable"}
    ):
        questions.append(
            {
                "question_id": "transaction_amount.exchange_rate_evidence",
                "input_path": "transaction_amount",
                "category": "exchange_rate_evidence",
                "client_answerable": True,
                "response_type": "structured_cnb_rate",
                "prompt": (
                    "Provide payment date, accounting date and CNB rate "
                    "evidence for the earlier date."
                ),
                "why": (
                    "Foreign-currency withholding tax must be converted to CZK "
                    "using the applicable evidenced rate."
                ),
                "required_documents": [
                    "CNB rate source URL",
                    "Payment or accounting record",
                ],
            }
        )

    supplied_amount = request.get("transaction_amount")
    optional_inputs = []
    if supplied_amount is None:
        optional_inputs.append(
            {
                "input_path": "transaction_amount",
                "prompt": (
                    "Add the gross amount and currency to calculate CZK tax "
                    "after a final rate is available."
                ),
            }
        )

    status = str(analysis.get("status"))
    if status == "OUT_OF_SCOPE":
        intake_status = "OUT_OF_SCOPE"
    elif questions:
        intake_status = "ACTION_REQUIRED"
    elif status == "FINAL":
        intake_status = "COMPLETE"
    else:
        intake_status = "PROFESSIONAL_REVIEW_REQUIRED"

    documents = sorted(
        {
            document
            for question in questions
            for document in question["required_documents"]
        }
    )
    return {
        "schema_version": 1,
        "status": intake_status,
        "analysis_status": status,
        "questions": questions,
        "required_documents": documents,
        "optional_inputs": optional_inputs,
        "semantics": {
            "client_facts_are_not_legal_approval": True,
            "unanswered_items_remain_unresolved": True,
            "legal_determinations_require_review": True,
        },
    }
