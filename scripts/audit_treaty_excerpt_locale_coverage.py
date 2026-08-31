from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
LOCALE_REGISTRY = ROOT / "app" / "web" / "treaty-excerpt-locales-20260824.json"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"


def _load_rules() -> list[dict]:
    rules: list[dict] = []
    for path in sorted(RULE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rules.extend(payload.get("rules", []))
    return rules


def _load_locale_entries() -> tuple[dict[str, dict], dict[str, tuple[str, dict]]]:
    payload = json.loads(LOCALE_REGISTRY.read_text(encoding="utf-8"))
    entries = dict(payload.get("entries", {}))
    rule_entries: dict[str, tuple[str, dict]] = {}

    if LOCALE_DIR.is_dir():
        for path in sorted(LOCALE_DIR.glob("*.json")):
            country_payload = json.loads(path.read_text(encoding="utf-8"))
            country = str(country_payload.get("recipient_country") or path.stem).upper()
            articles = country_payload.get("articles", {})
            if isinstance(articles, dict):
                target = entries.setdefault(country, {})
                for article, locale_payload in articles.items():
                    # The per-country locale files are the current canonical
                    # store. The legacy aggregate registry is retained only as
                    # a compatibility fallback and may contain older text for
                    # the same article (AT is the known migration case).
                    target[str(article)] = locale_payload

            rules = country_payload.get("rules", {})
            if isinstance(rules, dict):
                for rule_id, rule_payload in rules.items():
                    if rule_id in rule_entries and rule_entries[rule_id] != (country, rule_payload):
                        raise RuntimeError(f"Conflicting rule-specific treaty locale entry for {rule_id}")
                    rule_entries[str(rule_id)] = (country, rule_payload)

    return entries, rule_entries


def _is_verified_treaty_rate_rule(rule: dict) -> bool:
    return (
        rule.get("verification_status") == "verified"
        and rule.get("effect") == "rate"
        and rule.get("legal_layer") in {"treaty", "protocol", "mli"}
    )


def _outcome_signature(rule: dict) -> tuple:
    return (
        rule.get("rate"),
        rule.get("tax_treatment"),
        rule.get("resolve_tax_treatment"),
    )


def _condition_signature(rule: dict) -> str:
    return json.dumps(rule.get("conditions") or [], sort_keys=True, separators=(",", ":"))


def _article_locale_text(locale_entries: dict[str, dict], country: str, article: str) -> str:
    locale = locale_entries.get(country, {}).get(str(article), {}).get("en")
    if not isinstance(locale, dict):
        return ""
    return str(locale.get("text") or "").strip()


def _article_supports_outcome(text: str, rule: dict) -> bool:
    if not text:
        return False
    rate = rule.get("rate")
    try:
        numeric_rate = float(rate)
    except (TypeError, ValueError):
        numeric_rate = None

    if numeric_rate is not None and numeric_rate > 0:
        canonical = str(int(numeric_rate)) if numeric_rate.is_integer() else str(numeric_rate)
        escaped = re.escape(canonical).replace(r"\.", r"[.,]")
        return bool(re.search(rf"(?:^|[^0-9]){escaped}(?:[.,]0+)?\s*(?:%|percent|per cent)", text, re.I))

    treatment = str(rule.get("tax_treatment") or rule.get("resolve_tax_treatment") or "")
    if numeric_rate == 0 or treatment == "exclusive_foreign_taxation":
        return bool(re.search(
            r"\b(taxable only|shall be taxable only|exempt from tax|shall be exempt|only in (?:that|the) other (?:Contracting )?State)\b",
            text,
            re.I,
        ))

    return False


def main() -> int:
    all_rules = _load_rules()
    rules = [rule for rule in all_rules if _is_verified_treaty_rate_rule(rule)]
    locale_entries, rule_locale_entries = _load_locale_entries()

    required: set[tuple[str, str]] = set()
    income_types: dict[tuple[str, str], set[str]] = defaultdict(set)
    rules_by_article: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for rule in rules:
        country = str(rule.get("recipient_country") or "").upper()
        article = str(rule.get("article") or "").strip()
        if not country or not article:
            continue
        key = (country, article)
        required.add(key)
        income_types[key].add(str(rule.get("income_type") or ""))
        rules_by_article[key].append(rule)

    covered: set[tuple[str, str]] = set()
    for country, country_entries in locale_entries.items():
        if not isinstance(country_entries, dict):
            continue
        for article, article_entries in country_entries.items():
            if not isinstance(article_entries, dict):
                continue
            locale = article_entries.get("en")
            if isinstance(locale, dict) and str(locale.get("text") or "").strip():
                covered.add((str(country).upper(), str(article)))

    rules_by_id = {str(rule.get("rule_id")): rule for rule in rules if rule.get("rule_id")}
    rule_specific_covered: set[str] = set()
    invalid_rule_locale_entries: list[str] = []
    for rule_id, (country, payload) in rule_locale_entries.items():
        locale = payload.get("en") if isinstance(payload, dict) else None
        if not isinstance(locale, dict) or not str(locale.get("text") or "").strip():
            continue
        rule = rules_by_id.get(rule_id)
        if not rule:
            invalid_rule_locale_entries.append(rule_id)
            continue
        expected_country = str(rule.get("recipient_country") or "").upper()
        expected_article = str(rule.get("article") or "")
        declared_article = str(payload.get("article") or expected_article)
        if country != expected_country or declared_article != expected_article:
            invalid_rule_locale_entries.append(rule_id)
            continue
        rule_specific_covered.add(rule_id)

    covered_article_rule_ids: set[str] = set()
    decisive_outcome_covered: set[str] = set()
    decisive_outcome_missing: set[str] = set()
    rule_specific_required: set[str] = set()

    for key, article_rules in rules_by_article.items():
        country, article = key
        if key not in covered:
            continue
        text = _article_locale_text(locale_entries, country, article)
        outcome_groups: dict[tuple, list[dict]] = defaultdict(list)
        for rule in article_rules:
            outcome_groups[_outcome_signature(rule)].append(rule)
            rule_id = str(rule.get("rule_id") or "")
            if not rule_id:
                continue
            covered_article_rule_ids.add(rule_id)
            if rule_id in rule_specific_covered or _article_supports_outcome(text, rule):
                decisive_outcome_covered.add(rule_id)
            else:
                decisive_outcome_missing.add(rule_id)
                rule_specific_required.add(rule_id)

        for group in outcome_groups.values():
            condition_signatures = {_condition_signature(rule) for rule in group}
            if len(group) > 1 and len(condition_signatures) > 1:
                rule_specific_required.update(
                    str(rule.get("rule_id"))
                    for rule in group
                    if rule.get("rule_id")
                )

    missing = sorted(required - covered)
    extra = sorted(covered - required)
    packages = sorted({country for country, _ in required})
    covered_packages = sorted({country for country, article in covered if (country, article) in required})
    rule_specific_missing = sorted(rule_specific_required - rule_specific_covered)

    print("TaxTreat treaty excerpt EN locale coverage")
    print(f"Verified treaty packages: {len(packages)}")
    print(f"Required country/article pairs: {len(required)}")
    print(f"Covered country/article pairs: {len(required & covered)}")
    print(f"Missing country/article pairs: {len(missing)}")
    print(f"Packages with at least one EN excerpt: {len(covered_packages)}")
    print(f"Verified treaty rules inside covered EN articles: {len(covered_article_rule_ids)}")
    print(f"Rules with decisive EN outcome evidence: {len(decisive_outcome_covered)}")
    print(f"Rules without decisive EN outcome evidence: {len(decisive_outcome_missing)}")
    print(f"Rules requiring explicit rule-specific EN disambiguation: {len(rule_specific_required)}")
    print(f"Required rule-specific EN excerpts covered: {len(rule_specific_required & rule_specific_covered)}")
    print(f"Required rule-specific EN excerpts missing: {len(rule_specific_missing)}")

    if missing:
        print("\nMissing EN treaty excerpt variants:")
        for country, article in missing:
            incomes = ",".join(sorted(value for value in income_types[(country, article)] if value))
            print(f"  {country} Article {article}: {incomes or '-'}")

    if decisive_outcome_missing:
        print("\nCovered articles whose selected outcome is not yet decisively evidenced in EN:")
        for rule_id in sorted(decisive_outcome_missing):
            rule = rules_by_id[rule_id]
            print(
                f"  {rule_id}: {rule.get('recipient_country')} Article {rule.get('article')} "
                f"{rule.get('income_type')} rate={rule.get('rate')}"
            )

    if rule_specific_missing:
        print("\nRules requiring rule-specific EN disambiguation and still missing it:")
        for rule_id in rule_specific_missing:
            rule = rules_by_id[rule_id]
            print(
                f"  {rule_id}: {rule.get('recipient_country')} Article {rule.get('article')} "
                f"{rule.get('income_type')} rate={rule.get('rate')}"
            )

    if extra:
        print("\nRegistry entries not referenced by verified treaty rules:")
        for country, article in extra:
            print(f"  {country} Article {article}")

    if invalid_rule_locale_entries:
        print("\nInvalid rule-specific locale entries:")
        for rule_id in sorted(invalid_rule_locale_entries):
            print(f"  {rule_id}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
