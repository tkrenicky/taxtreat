from __future__ import annotations

from copy import deepcopy


# Confirmed against the approved treaty source_text embedded in Stage 6.
# These patches are deliberately explicit by rule_id: no heuristic source-text
# rewriting is allowed at runtime.
DIVIDEND_CONDITION_PATCHES: dict[str, list[dict]] = {
    "CZ-GB-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "voting_ownership", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-US-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "voting_ownership", "fact_source": "transaction", "operator": ">=", "value": "10"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-IE-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "voting_ownership", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-FR-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-LU-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "10"},
        {"fact": "holding_period_months", "fact_source": "transaction", "operator": ">=", "value": 12},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-HU-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-SK-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "10"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-CY-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "10"},
        {"fact": "holding_period_months", "fact_source": "transaction", "operator": ">=", "value": 12},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-IS-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-LI-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "10"},
        {"fact": "holding_period_months", "fact_source": "transaction", "operator": ">=", "value": 12},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-MD-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-AL-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-LT-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
    "CZ-EG-DIVIDEND-CURRENT-1": [
        {"fact": "recipient_entity_type", "fact_source": "transaction", "operator": "==", "value": "company"},
        {"fact": "recipient_is_partnership", "fact_source": "transaction", "operator": "==", "value": False},
        {"fact": "direct_ownership", "fact_source": "transaction", "operator": "==", "value": True},
        {"fact": "ownership_percent", "fact_source": "transaction", "operator": ">=", "value": "25"},
        {"fact": "beneficial_owner", "fact_source": "transaction", "operator": "==", "value": "true"},
    ],
}


def normalize_raw_legal_rule(raw_rule: dict) -> dict:
    """Return one rule with only explicitly verified projection corrections.

    The source package is not mutated. The rule id remains unchanged so report
    citations/provenance continue to point to the approved source record.
    """

    conditions = DIVIDEND_CONDITION_PATCHES.get(str(raw_rule.get("rule_id")))
    if conditions is None:
        return raw_rule

    normalized = deepcopy(raw_rule)
    normalized["conditions"] = deepcopy(conditions)
    return normalized
