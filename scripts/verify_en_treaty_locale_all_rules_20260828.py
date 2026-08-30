from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"

GENERIC_CONDITION_FACTS = {"beneficial_owner", "fallback_case"}
SUMMARY_STATUSES = {"verified_stage6_rule_summary", "machine_translation_from_official_text"}


def _rate_rules(package: dict) -> list[dict]:
    return [
        rule
        for rule in package.get("rules", [])
        if rule.get("legal_layer") in {"treaty", "protocol", "mli"}
        and rule.get("effect") == "rate"
    ]


def _is_condition_sensitive(rule: dict, siblings: list[dict]) -> bool:
    facts = {
        str(condition.get("fact") or "")
        for condition in rule.get("conditions", [])
        if str(condition.get("fact") or "")
    }
    non_generic = facts - GENERIC_CONDITION_FACTS
    rates = {rule_item.get("rate") for rule_item in siblings}
    return bool(non_generic or len(rates) > 1)


def main() -> int:
    failures = []
    checked = 0
    condition_sensitive = 0

    for rule_path in sorted(RULE_DIR.glob("*.json")):
        package = json.loads(rule_path.read_text(encoding="utf-8"))
        country = package.get("country_pair", {}).get("recipient_country")
        if not country:
            continue

        locale_path = LOCALE_DIR / f"{country}.json"
        if not locale_path.is_file():
            failures.append(f"{country}: missing country EN locale registry")
            continue

        locale = json.loads(locale_path.read_text(encoding="utf-8"))
        locale_rules = locale.get("rules", {})
        articles = locale.get("articles", {})

        grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
        rules = _rate_rules(package)
        for rule in rules:
            grouped[(str(rule.get("income_type") or ""), str(rule.get("article") or ""))].append(rule)

        for rule in rules:
            checked += 1
            rid = str(rule.get("rule_id") or "")
            article = str(rule.get("article") or "")
            income_type = str(rule.get("income_type") or "")
            exact = (locale_rules.get(rid) or {}).get("en") or {}
            article_en = (articles.get(article) or {}).get("en") or {}
            selected = exact if exact.get("text") else article_en

            if not selected.get("text"):
                failures.append(
                    f"{country} {rid} Article {article}: no usable EN treaty text/summary"
                )
                continue

            siblings = grouped[(income_type, article)]
            sensitive = _is_condition_sensitive(rule, siblings)
            if sensitive:
                condition_sensitive += 1

            # An article-level official treaty text may safely cover all branches because
            # the actual wording is preserved. A synthetic/translated summary may not:
            # condition-sensitive rules need their own rule-specific entry, otherwise a
            # generic article summary can silently flatten special treaty conditions.
            status = str(selected.get("status") or "")
            using_article_fallback = not bool(exact.get("text"))
            if sensitive and using_article_fallback and status in SUMMARY_STATUSES:
                failures.append(
                    f"{country} {rid} Article {article}: condition-sensitive rule "
                    f"uses article-level {status}; add a rule-specific EN entry preserving "
                    "the rule conditions"
                )

    if failures:
        raise AssertionError(
            "EN treaty locale coverage failures:\n" + "\n".join(failures)
        )
    if checked < 100:
        raise AssertionError(f"Suspiciously low treaty-rule coverage: {checked}")

    print(
        "EN treaty locale rule coverage: PASS "
        f"({checked} treaty rules; {condition_sensitive} condition-sensitive rules)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
