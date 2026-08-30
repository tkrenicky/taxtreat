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
    # Protocol No. 92/2012 Sb.m.s., Article II replaced Article 10(2).
    "CZ-UZ-DIVIDEND-CURRENT-1": _company_direct("25", non_partnership=True),
}


# Stage 6 correctly projected the UZ protocol rates/conditions but attached the
# base-treaty Article 10 excerpt and base-treaty source. Keep the approved raw
# package immutable and repair the runtime citation explicitly. The protocol
# source id and official URL already exist in legal_evidence_sources.json.
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
    """Return one rule with only explicitly verified projection corrections.

    The Stage 6 file itself remains the approved immutable snapshot. Runtime
    remediation is keyed only by exact rule_id and preserves the original
    review-package hash as the link back to that snapshot.
    """

    rule_id = str(raw_rule.get("rule_id"))
    conditions = DIVIDEND_CONDITION_PATCHES.get(rule_id)
    source_patch = DIVIDEND_SOURCE_PATCHES.get(rule_id)

    if conditions is None and source_patch is None:
        return raw_rule

    normalized = deepcopy(raw_rule)
    if conditions is not None:
        normalized["conditions"] = deepcopy(conditions)
    if source_patch is not None:
        normalized.update(deepcopy(source_patch))

    normalized["runtime_remediation_id"] = "condition-aware-audit-2026-08-30"
    return normalized
