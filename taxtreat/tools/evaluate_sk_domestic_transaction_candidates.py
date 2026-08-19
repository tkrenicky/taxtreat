from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "sk_outbound"
    / "domestic_transaction_condition_model.json"
)

RELATIONSHIP_FACTS = {
    "payer_directly_owns_recipient": "payer_directly_owns_recipient",
    "recipient_directly_owns_payer": "recipient_directly_owns_payer",
    "third_eu_legal_person_directly_owns_both": "third_eu_legal_person_directly_owns_both",
}


def _load_model() -> dict[str, Any]:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def evaluate_registered_pe_exclusion(facts: dict[str, Any]) -> dict[str, Any]:
    names = (
        "recipient_has_sk_permanent_establishment",
        "recipient_sk_pe_registered_under_income_tax_act",
        "income_attributable_to_registered_sk_pe",
    )
    missing = [name for name in names if facts.get(name) is None]
    if missing:
        return {
            "status": "blocked_missing_transaction_facts",
            "applies": None,
            "missing_facts": missing,
        }

    applies = all(facts[name] is True for name in names)
    return {
        "status": "machine_candidate_not_legal_conclusion",
        "applies": applies,
        "missing_facts": [],
    }


def evaluate_eu_relief_candidate(
    income_type: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    if income_type not in {"interest", "royalty"}:
        return {
            "status": "not_applicable_income_type",
            "candidate_treatment": None,
            "missing_facts": [],
        }

    model = _load_model()
    key = "eu_interest_relief" if income_type == "interest" else "eu_royalty_relief"
    relief = model[key]

    required_boolean_facts = (
        "recipient_is_legal_person_or_qualifying_pe_of_eu_legal_person",
        "recipient_is_eu_taxpayer_or_qualifying_pe",
        "recipient_is_beneficial_owner",
    )
    missing = [name for name in required_boolean_facts if facts.get(name) is None]

    relationship_values = [
        facts.get(name)
        for name in RELATIONSHIP_FACTS
    ]
    if all(value is None for value in relationship_values):
        missing.append("ownership_relationship")

    ownership_percent = facts.get("direct_capital_percent")
    if ownership_percent is None:
        missing.append("direct_capital_percent")

    holding_months = facts.get("holding_period_months")
    will_reach_24 = facts.get("holding_period_will_reach_24_months")
    if holding_months is None:
        missing.append("holding_period_months")

    if missing:
        return {
            "status": "blocked_missing_transaction_facts",
            "candidate_treatment": None,
            "missing_facts": sorted(set(missing)),
        }

    base_conditions = all(
        facts[name] is True for name in required_boolean_facts
    )
    relationship_ok = any(value is True for value in relationship_values)
    ownership_ok = float(ownership_percent) >= relief[
        "required_conditions"
    ]["direct_capital_percent_min"]
    current_holding_ok = float(holding_months) >= relief[
        "required_conditions"
    ]["holding_period_months_min"]

    if base_conditions and relationship_ok and ownership_ok and current_holding_ok:
        return {
            "status": "machine_candidate_not_legal_conclusion",
            "candidate_treatment": "current_exemption_candidate",
            "rate_candidate_percent": 0,
            "refund_route_candidate": False,
            "missing_facts": [],
        }

    if (
        base_conditions
        and relationship_ok
        and ownership_ok
        and not current_holding_ok
        and will_reach_24 is True
    ):
        return {
            "status": "machine_candidate_not_legal_conclusion",
            "candidate_treatment": "future_holding_period_refund_candidate",
            "rate_candidate_percent": None,
            "refund_route_candidate": True,
            "refund_locator": relief["post_payment_refund_locator"],
            "missing_facts": [],
        }

    return {
        "status": "machine_candidate_not_legal_conclusion",
        "candidate_treatment": "exemption_conditions_not_met",
        "rate_candidate_percent": None,
        "refund_route_candidate": False,
        "missing_facts": [],
    }


def evaluate_domestic_transaction_candidates(
    income_type: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    pe = evaluate_registered_pe_exclusion(facts)
    relief = evaluate_eu_relief_candidate(income_type, facts)
    return {
        "source_country": "SK",
        "income_type": income_type,
        "registered_pe_exclusion": pe,
        "eu_relief": relief,
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }
