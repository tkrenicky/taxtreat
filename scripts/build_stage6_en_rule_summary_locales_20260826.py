from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PARTNERS = ROOT / "data" / "cz_treaty_partners.json"
RULES_DIR = ROOT / "data" / "legal_rules_stage6"
LOCALES_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"
REPORT = ROOT / "reports" / "treaty_en_rule_summary_coverage_20260826.json"

FACT_LABELS = {
    "beneficial_owner": "the recipient is the beneficial owner",
    "ownership_percent": "direct ownership percentage",
    "direct_or_indirect_voting_ownership": "direct or indirect voting ownership percentage",
    "direct_ownership": "the ownership is direct",
    "holding_period_months": "holding period in complete months",
    "recipient_is_treaty_resident": "the recipient is a treaty resident",
    "permanent_establishment_connection": "the income is connected with a permanent establishment",
    "recipient_entity_type": "recipient entity type",
    "royalty_category": "royalty category",
    "lender_type": "lender type",
    "interest_category": "interest category",
}


def _fmt_value(value: Any) -> str:
    text = str(value)
    if text.lower() == "true":
        return "yes"
    if text.lower() == "false":
        return "no"
    return text


def _condition_text(condition: dict[str, Any]) -> str:
    fact = str(condition.get("fact") or "fact")
    label = FACT_LABELS.get(fact, fact.replace("_", " "))
    operator = str(condition.get("operator") or "")
    value = _fmt_value(condition.get("value"))
    operator_words = {
        "==": "is",
        "!=": "is not",
        ">=": "is at least",
        "<=": "is at most",
        ">": "is more than",
        "<": "is less than",
        "in": "is one of",
        "not_in": "is not one of",
    }
    return f"{label} {operator_words.get(operator, operator)} {value}".strip()


def _effect_text(rule: dict[str, Any]) -> str:
    effect = str(rule.get("effect") or "").lower()
    rate = rule.get("rate")
    treatment = str(rule.get("tax_treatment") or "").lower()
    if rate is not None:
        try:
            rate_text = f"{float(rate):g}%"
        except (TypeError, ValueError):
            rate_text = f"{rate}%"
        if effect == "rate" or not effect:
            return f"a maximum Czech source-state withholding rate of {rate_text}"
        return f"the recorded treaty effect '{effect}' with a rate of {rate_text}"
    if treatment == "exclusive_foreign_taxation" or effect in {"exclusive_foreign_taxation", "exemption"}:
        return "no Czech source-state withholding tax under the represented treaty rule"
    if treatment:
        return f"the treaty treatment '{treatment.replace('_', ' ')}'"
    if effect:
        return f"the recorded treaty effect '{effect.replace('_', ' ')}'"
    return "the verified treaty treatment represented in the approved Stage 6 rule"


def _rule_summary(rule: dict[str, Any]) -> str:
    article = str(rule.get("article") or "")
    income = str(rule.get("income_type") or "income").capitalize()
    conditions = [
        _condition_text(condition)
        for condition in (rule.get("conditions") or [])
        if isinstance(condition, dict)
    ]
    condition_sentence = (
        " Conditions represented in the approved rule: " + "; ".join(conditions) + "."
        if conditions
        else ""
    )
    paragraph = rule.get("paragraph")
    paragraph_text = f", paragraph {paragraph}" if paragraph not in (None, "") else ""
    return (
        f"Article {article}{paragraph_text} — {income}. "
        f"TaxTreat's production-approved Stage 6 structured rule records {_effect_text(rule)}."
        f"{condition_sentence} "
        "This is an English rule summary derived mechanically from verified structured legal data; "
        "it is not presented as the authentic treaty wording. The cited official source and the "
        "production-approved structured rule control."
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_locale(path: Path, country: str) -> dict[str, Any]:
    if path.is_file():
        payload = _load_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"Locale must be an object: {path}")
        payload.setdefault("schema_version", 1)
        payload.setdefault("source_country", "CZ")
        payload.setdefault("recipient_country", country)
        payload.setdefault("articles", {})
        payload.setdefault("rules", {})
        return payload
    return {
        "schema_version": 1,
        "source_country": "CZ",
        "recipient_country": country,
        "articles": {},
        "rules": {},
    }


def _has_en_for_rule(locale: dict[str, Any], rule: dict[str, Any]) -> bool:
    rule_id = str(rule.get("rule_id") or "")
    rules = locale.get("rules") or {}
    entry = rules.get(rule_id) if isinstance(rules, dict) else None
    if isinstance(entry, dict) and isinstance(entry.get("en"), dict) and entry["en"].get("text"):
        return True
    article = str(rule.get("article") or "")
    articles = locale.get("articles") or {}
    article_entry = articles.get(article) if isinstance(articles, dict) else None
    return bool(
        isinstance(article_entry, dict)
        and isinstance(article_entry.get("en"), dict)
        and article_entry["en"].get("text")
    )


def main() -> int:
    partners = _load_json(PARTNERS)
    if not isinstance(partners, list):
        raise ValueError("CZ treaty partner registry must be a list")

    LOCALES_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    country_results: list[dict[str, Any]] = []
    changed_files = 0
    generated_rules = 0

    for partner in partners:
        country = str(partner["iso2"]).upper()
        rule_path = RULES_DIR / f"{country.lower()}.json"
        if not rule_path.is_file():
            country_results.append({"country": country, "status": "MISSING_STAGE6_RULE_FILE"})
            continue

        rules_payload = _load_json(rule_path)
        rules = [
            rule
            for rule in (rules_payload.get("rules") or [])
            if isinstance(rule, dict)
            and str(rule.get("legal_layer") or "") == "treaty"
            and str(rule.get("verification_status") or "") == "verified"
            and str(rule.get("article") or "") in {"10", "11", "12"}
        ]
        locale_path = LOCALES_DIR / f"{country}.json"
        locale = _load_locale(locale_path, country)
        before = json.dumps(locale, sort_keys=True, ensure_ascii=False)
        locale_rules = locale.setdefault("rules", {})

        for rule in rules:
            if _has_en_for_rule(locale, rule):
                continue
            rule_id = str(rule.get("rule_id") or "")
            if not rule_id:
                continue
            locale_rules[rule_id] = {
                "article": str(rule.get("article") or ""),
                "en": {
                    "language": "en",
                    "status": "verified_stage6_rule_summary",
                    "authority": "TaxTreat Stage 6 production-approved structured rule derived from official treaty source",
                    "source_url": str(rule.get("source_url") or ""),
                    "source_id": str(rule.get("source_id") or ""),
                    "rule_id": rule_id,
                    "text": _rule_summary(rule),
                },
            }
            generated_rules += 1

        after = json.dumps(locale, sort_keys=True, ensure_ascii=False)
        if after != before:
            locale_path.write_text(
                json.dumps(locale, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            changed_files += 1

        uncovered = [str(rule.get("rule_id") or "") for rule in rules if not _has_en_for_rule(locale, rule)]
        country_results.append({
            "country": country,
            "status": "PASS" if rules and not uncovered else "FAIL",
            "verified_treaty_rules": len(rules),
            "uncovered_rule_ids": uncovered,
            "locale_file": str(locale_path.relative_to(ROOT)),
        })

    passed = [row for row in country_results if row.get("status") == "PASS"]
    failed = [row for row in country_results if row.get("status") != "PASS"]
    report = {
        "schema_version": 1,
        "coverage_basis": "all CZ treaty partners in data/cz_treaty_partners.json",
        "partner_count": len(partners),
        "pass_count": len(passed),
        "coverage_percent": round((len(passed) / len(partners) * 100.0), 2) if partners else 0.0,
        "changed_locale_files": changed_files,
        "generated_rule_summaries": generated_rules,
        "results": country_results,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("partner_count", "pass_count", "coverage_percent", "changed_locale_files", "generated_rule_summaries")}, indent=2))

    if failed:
        print("Coverage failures:", ", ".join(str(row.get("country")) for row in failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
