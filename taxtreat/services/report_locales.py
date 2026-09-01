from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


_ROOT = Path(__file__).resolve().parents[2]
_LOCALE_ROOT = _ROOT / "app" / "web" / "treaty-excerpt-locales"
_SK_RULE_ROOT = _ROOT / "data" / "legal_rules_sk"

_STATUS_LABELS = {
    "official_treaty_text": "Official English treaty text",
    "official_synthesised_text": "Official synthesised English text",
    "official_protocol_text": "Official English protocol text",
    "official_translation_non_authentic": "Official English translation — non-authentic",
    "machine_translation_from_official_text": "Machine translation from official text",
    "verified_stage6_rule_summary": "Verified English rule summary — not treaty wording",
    "verified_structured_rule_summary": "Verified English structured rule summary — not treaty wording",
    "review_required_structured_rule_summary": "Review-required English structured rule summary — not treaty wording",
    "current_application_suspended": "Current application suspended",
}

_FACT_LABELS = {
    "beneficial_owner": "the recipient is the beneficial owner",
    "recipient_is_treaty_resident": "the recipient is a treaty resident",
    "permanent_establishment_connection": "the income is connected with a permanent establishment",
    "ownership_percent": "ownership percentage",
    "voting_ownership_percent": "voting ownership percentage",
    "direct_or_indirect_voting_ownership": "direct or indirect voting ownership percentage",
    "direct_ownership": "the ownership is direct",
    "holding_period_months": "holding period in complete months",
    "royalty_category": "royalty category",
    "interest_category": "interest category",
    "lender_type": "lender type",
    "treaty_ppt_passed": "the MLI principal purpose test is passed",
    "mli_article_10_third_jurisdiction_pe_test_passed": "the MLI Article 10 third-jurisdiction PE test is passed",
    "mli_article_13_specific_activity_pe_status_resolved": "the MLI Article 13 specific-activity PE status is resolved",
}


def _read_locale(recipient_country: str) -> Mapping[str, Any] | None:
    code = str(recipient_country or "").strip().upper()
    if not code or not code.isalnum():
        return None
    path = _LOCALE_ROOT / f"{code}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _read_sk_rule(recipient_country: str, rule_id: str) -> Mapping[str, Any] | None:
    code = str(recipient_country or "").strip().upper()
    wanted = str(rule_id or "").strip()
    if not code or not code.isalnum() or not wanted:
        return None
    path = _SK_RULE_ROOT / f"{code.lower()}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    pair = payload.get("country_pair") or {}
    if (
        not isinstance(pair, dict)
        or str(pair.get("source_country") or "").upper() != "SK"
        or str(pair.get("recipient_country") or "").upper() != code
    ):
        return None
    for rule in payload.get("rules") or []:
        if isinstance(rule, dict) and str(rule.get("rule_id") or "") == wanted:
            return rule
    return None


def _fmt_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return ", ".join(_fmt_value(item) for item in value)
    return str(value)


def _condition_summary(condition: Mapping[str, Any]) -> str:
    fact = str(condition.get("fact") or "fact")
    label = _FACT_LABELS.get(fact, fact.replace("_", " "))
    operator = str(condition.get("operator") or "")
    value = _fmt_value(condition.get("value"))
    words = {
        "==": "is",
        "!=": "is not",
        ">=": "is at least",
        "<=": "is at most",
        ">": "is more than",
        "<": "is less than",
        "in": "is one of",
        "not_in": "is not one of",
    }
    return f"{label} {words.get(operator, operator)} {value}".strip()


def _sk_effect_summary(rule: Mapping[str, Any], review_required: bool) -> str:
    effect = str(rule.get("effect") or "").lower()
    rate = rule.get("rate")
    treatment = str(rule.get("tax_treatment") or "").lower()

    if effect == "review_gate":
        return (
            "The structured rule is a fail-closed review gate; no final treaty "
            "rate or treatment is released."
        )
    if effect == "eligibility_gate":
        layers = ", ".join(str(item) for item in (rule.get("applies_to_layers") or []))
        detail = f" for {layers}" if layers else ""
        return f"The structured rule records an eligibility gate{detail}."
    if rate is not None:
        try:
            rate_text = f"{float(rate):g}%"
        except (TypeError, ValueError):
            rate_text = f"{rate}%"
        if review_required:
            return (
                f"The fail-closed structured rule records a candidate Slovak "
                f"source-state withholding rate of {rate_text}; no final rate is released."
            )
        return (
            f"The verified structured rule records a Slovak source-state "
            f"withholding rate of {rate_text}."
        )
    if treatment == "exclusive_foreign_taxation":
        prefix = "candidate " if review_required else ""
        return (
            f"The structured rule records {prefix}exclusive taxation in the "
            "recipient state of residence."
        )
    if treatment:
        prefix = "candidate " if review_required else ""
        return f"The structured rule records the {prefix}treatment '{treatment.replace('_', ' ')}'."
    return f"The structured rule records the treaty effect '{effect.replace('_', ' ') or 'unspecified'}'."


def _sk_rule_summary(rule: Mapping[str, Any]) -> dict[str, Any] | None:
    rule_id = str(rule.get("rule_id") or "")
    article = str(rule.get("article") or "")
    source_url = str(rule.get("source_url") or "").strip()
    status = str(rule.get("verification_status") or "").strip()
    if not rule_id or not article or status not in {"verified", "needs_review"}:
        return None

    review_required = (
        status != "verified"
        or rule.get("final_rate_allowed") is False
        or str(rule.get("decision_status") or "") == "REVIEW_REQUIRED"
        or rule.get("automatic_production_approval_forbidden") is True
    )
    excerpt_status = (
        "review_required_structured_rule_summary"
        if review_required
        else "verified_structured_rule_summary"
    )
    income = str(rule.get("income_type") or "income").capitalize()
    paragraph = rule.get("paragraph")
    paragraph_copy = f", paragraph {paragraph}" if paragraph not in (None, "") else ""
    conditions = [
        _condition_summary(condition)
        for condition in (rule.get("conditions") or [])
        if isinstance(condition, dict)
    ]
    condition_copy = (
        " Structured conditions: " + "; ".join(conditions) + "."
        if conditions
        else ""
    )
    review_copy = (
        " This rule remains review-required and must not be presented as a final legal conclusion."
        if review_required
        else ""
    )
    text = (
        f"Article {article}{paragraph_copy} — {income}. "
        f"{_sk_effect_summary(rule, review_required)}"
        f"{condition_copy}{review_copy} "
        "This is an English structured rule summary derived mechanically from "
        "TaxTreat's Slovak source-country legal data; it is not treaty wording. "
        "The cited official source and the structured Slovak rule control."
    )
    return {
        "excerpt": text,
        "excerpt_language": "en",
        "excerpt_status": excerpt_status,
        "excerpt_status_label": _STATUS_LABELS[excerpt_status],
        "excerpt_authority": (
            "TaxTreat Slovak structured rule derived from the cited official legal source"
        ),
        "excerpt_source_url": source_url or None,
    }


def english_excerpt_for_citation(
    citation: Mapping[str, Any],
    recipient_country: str,
    source_country: str = "CZ",
) -> dict[str, Any] | None:
    """Return source-country-specific English locale metadata.

    CZ uses the checked-in treaty locale corpus. SK uses mechanical English
    structured-rule summaries derived from the matching Slovak rule and never
    reuses a same-recipient Czech treaty excerpt. Missing or malformed data
    fails closed by returning None.
    """
    source = str(source_country or "").strip().upper()
    if source == "SK":
        rule = _read_sk_rule(recipient_country, str(citation.get("rule_id") or ""))
        return _sk_rule_summary(rule) if rule else None
    if source != "CZ":
        return None

    locale = _read_locale(recipient_country)
    if not locale:
        return None

    rule_id = str(citation.get("rule_id") or "")
    article = str(citation.get("article") or "")
    entry: Mapping[str, Any] | None = None

    rules = locale.get("rules")
    if rule_id and isinstance(rules, dict):
        candidate = rules.get(rule_id)
        if isinstance(candidate, dict):
            entry = candidate

    if entry is None and article:
        articles = locale.get("articles")
        if isinstance(articles, dict):
            candidate = articles.get(article)
            if isinstance(candidate, dict):
                entry = candidate

    if not entry:
        return None
    en = entry.get("en")
    if not isinstance(en, dict):
        return None
    text = str(en.get("text") or "").strip()
    status = str(en.get("status") or "").strip()
    if not text or not status:
        return None

    return {
        "excerpt": text,
        "excerpt_language": "en",
        "excerpt_status": status,
        "excerpt_status_label": _STATUS_LABELS.get(
            status, status.replace("_", " ").title()
        ),
        "excerpt_authority": str(en.get("authority") or "").strip() or None,
        "excerpt_source_url": str(en.get("source_url") or "").strip() or None,
    }
