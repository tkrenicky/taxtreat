from __future__ import annotations

from copy import deepcopy


def _c(fact: str, operator: str, value) -> dict:
    return {
        "fact": fact,
        "fact_source": "transaction",
        "operator": operator,
        "value": value,
    }


def _company_direct(
    ownership: str,
    *,
    non_partnership: bool = False,
    holding_months: int | None = None,
    voting: bool = False,
) -> list[dict]:
    conditions = [_c("recipient_entity_type", "==", "company")]
    if non_partnership:
        conditions.append(_c("recipient_is_partnership", "==", False))
    conditions.append(_c("direct_ownership", "==", True))
    conditions.append(
        _c("voting_ownership" if voting else "ownership_percent", ">=", ownership)
    )
    if holding_months is not None:
        conditions.append(_c("holding_period_months", ">=", holding_months))
    conditions.append(_c("beneficial_owner", "==", "true"))
    return conditions


# Confirmed against the approved treaty source_text embedded in Stage 6.
# Patches are deliberately explicit by rule_id; no heuristic source-text
# rewriting is performed at runtime.
DIVIDEND_CONDITION_PATCHES: dict[str, list[dict]] = {
    "CZ-GB-DIVIDEND-CURRENT-1": [
        _c("recipient_entity_type", "==", "company"),
        _c("voting_ownership", ">=", "25"),
        _c("beneficial_owner", "==", "true"),
    ],
    "CZ-US-DIVIDEND-CURRENT-1": [
        _c("recipient_entity_type", "==", "company"),
        _c("voting_ownership", ">=", "10"),
        _c("beneficial_owner", "==", "true"),
    ],
    "CZ-IE-DIVIDEND-CURRENT-1": _company_direct("25", voting=True),
    "CZ-FR-DIVIDEND-CURRENT-1": _company_direct("25"),
    "CZ-LU-DIVIDEND-CURRENT-1": _company_direct(
        "10", non_partnership=True, holding_months=12
    ),
    "CZ-HU-DIVIDEND-CURRENT-1": _company_direct("25"),
    "CZ-SK-DIVIDEND-CURRENT-1": _company_direct("10", non_partnership=True),
    "CZ-CY-DIVIDEND-CURRENT-1": _company_direct(
        "10", non_partnership=True, holding_months=12
    ),
    "CZ-IS-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-LI-DIVIDEND-CURRENT-1": _company_direct(
        "10", non_partnership=True, holding_months=12
    ),
    "CZ-MD-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-AL-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-LT-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-EG-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-BB-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-LK-DIVIDEND-CURRENT-1": _company_direct("10"),
    "CZ-UA-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-ZA-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-XK-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-MK-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-IL-DIVIDEND-CURRENT-1": _company_direct("15", non_partnership=True),
    "CZ-KG-DIVIDEND-CURRENT-1": _company_direct("15", non_partnership=True),
    "CZ-PK-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-SI-DIVIDEND-CURRENT-1": _company_direct("25"),
    "CZ-GE-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-AD-DIVIDEND-CURRENT-1": _company_direct("10", non_partnership=True),
    "CZ-DK-DIVIDEND-CURRENT-1": _company_direct("10", non_partnership=True),
    "CZ-BD-DIVIDEND-CURRENT-1": [
        _c("recipient_entity_type", "==", "company"),
        _c("direct_ownership", "==", True),
        _c("ownership_percent", ">=", "25"),
        _c("beneficial_owner", "==", "true"),
        _c("continuous_holding_period_days", ">=", 365),
    ],
    "CZ-TN-DIVIDEND-CURRENT-1": [
        _c("recipient_entity_type", "==", "company"),
        _c("ownership_percent", ">=", "25"),
        _c("beneficial_owner", "==", "true"),
    ],
}


def normalize_raw_legal_rule(raw_rule: dict) -> dict:
    """Return one rule with only explicitly verified projection corrections."""

    conditions = DIVIDEND_CONDITION_PATCHES.get(str(raw_rule.get("rule_id")))
    if conditions is None:
        return raw_rule

    normalized = deepcopy(raw_rule)
    normalized["conditions"] = deepcopy(conditions)
    return normalized
