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


DIVIDEND_CONDITION_PATCHES: dict[str, list[dict]] = {
    "CZ-CH-DIVIDEND-SEMANTIC-REMEDIATION-5": [
        _c("recipient_is_treaty_resident", "==", True),
        _c("permanent_establishment_connection", "==", False),
        _c("recipient_entity_type", "==", "company"),
        _c("recipient_is_partnership", "==", False),
        _c("direct_ownership", "==", True),
        _c("ownership_percent", ">=", "25"),
        _c("beneficial_owner", "==", "true"),
    ],
    "CZ-EE-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-LV-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-VE-DIVIDEND-CURRENT-1": _company_direct("15", non_partnership=True),
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
    "CZ-LU-DIVIDEND-CURRENT-1": _company_direct("10", non_partnership=True, holding_months=12),
    "CZ-HU-DIVIDEND-CURRENT-1": _company_direct("25"),
    "CZ-SK-DIVIDEND-CURRENT-1": _company_direct("10", non_partnership=True),
    "CZ-CY-DIVIDEND-CURRENT-1": _company_direct("10", non_partnership=True, holding_months=12),
    "CZ-IS-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-LI-DIVIDEND-CURRENT-1": _company_direct("10", non_partnership=True, holding_months=12),
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
    "CZ-UZ-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-CN-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-ES-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-CO-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
    "CZ-NG-DIVIDEND-CURRENT-1": [
        _c("recipient_entity_type", "==", "company"),
        _c("direct_or_indirect_voting_ownership", ">=", "10"),
        _c("beneficial_owner", "==", "true"),
    ],
}


RULE_FIELD_PATCHES: dict[str, dict] = {
    "CZ-EG-INTEREST-CURRENT-1": {"priority": 671},
    "CZ-AL-INTEREST-CURRENT-2": {"priority": 671},
    "CZ-BR-INTEREST-CURRENT-1": {"priority": 671},
    "CZ-PT-INTEREST-CURRENT-1": {"priority": 671},
    "CZ-KW-DIVIDEND-CURRENT-1": {"priority": 671},
}


DIVIDEND_SOURCE_PATCHES: dict[str, dict] = {
    "CZ-UZ-DIVIDEND-CURRENT-1": {
        "legal_instrument": "protocol",
        "legal_layer": "protocol",
        "effective_from": "2013-01-01",
        "source_id": "CZ-MF-UZ-91E56630154D",
        "source_url": "https://aplikace.mv.gov.cz/sbirka-zakonu/ViewFile.aspx?type=z&id=25317",
        "source_text": (
            "Protocol No. 92/2012 Sb.m.s., Article II amends Article 10(2): "
            "5% for a beneficial-owner company other than a partnership directly "
            "holding at least 25% of the payer's capital."
        ),
        "source_excerpt_hash": "96a4279c10a8e81ad8733dc35a9631339119dfc3250c7b9dc4d3f1f908bd48cf",
        "evidence_source_ids": ["CZ-MF-UZ-91E56630154D"],
        "source_representation": "runtime_protocol_remediation_summary",
    },
    "CZ-UZ-DIVIDEND-CURRENT-2": {
        "legal_instrument": "protocol",
        "legal_layer": "protocol",
        "effective_from": "2013-01-01",
        "source_id": "CZ-MF-UZ-91E56630154D",
        "source_url": "https://aplikace.mv.gov.cz/sbirka-zakonu/ViewFile.aspx?type=z&id=25317",
        "source_text": (
            "Protocol No. 92/2012 Sb.m.s., Article II amends Article 10(2): "
            "10% in all other beneficial-owner dividend cases."
        ),
        "source_excerpt_hash": "82ff2525a18b72616cfd967bb94c2960298dc1dba8683ac798ad83ffb10b4570",
        "evidence_source_ids": ["CZ-MF-UZ-91E56630154D"],
        "source_representation": "runtime_protocol_remediation_summary",
    },
}


def normalize_raw_legal_rule(raw_rule: dict) -> dict:
    """Apply only exact-rule remediations verified by the condition-aware audit."""
    rule_id = str(raw_rule.get("rule_id"))
    conditions = DIVIDEND_CONDITION_PATCHES.get(rule_id)
    source_patch = DIVIDEND_SOURCE_PATCHES.get(rule_id)
    field_patch = RULE_FIELD_PATCHES.get(rule_id)

    narrow_zero_rate_qualification = (
        raw_rule.get("income_type") == "dividend"
        and raw_rule.get("rate") is not None
        and float(raw_rule.get("rate")) == 0.0
        and any(
            condition.get("fact") == "recipient_entity_type"
            and str(condition.get("value") or "")
            not in {"company", "individual", "fund", "other"}
            for condition in raw_rule.get("conditions", [])
        )
    )

    if (
        conditions is None
        and source_patch is None
        and field_patch is None
        and not narrow_zero_rate_qualification
    ):
        return raw_rule
    normalized = deepcopy(raw_rule)
    if conditions is not None:
        normalized["conditions"] = deepcopy(conditions)
    elif narrow_zero_rate_qualification:
        normalized["conditions"] = [
            (
                _c("treaty_specific_recipient_qualification", "==", True)
                if condition.get("fact") == "recipient_entity_type"
                else deepcopy(condition)
            )
            for condition in raw_rule.get("conditions", [])
        ]
    if source_patch is not None:
        normalized.update(deepcopy(source_patch))
    if field_patch is not None:
        normalized.update(deepcopy(field_patch))
    normalized["runtime_remediation_id"] = "condition-aware-audit-2026-08-30"
    return normalized
