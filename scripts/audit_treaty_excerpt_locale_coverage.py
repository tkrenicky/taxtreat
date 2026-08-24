from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
LOCALE_REGISTRY = ROOT / "app" / "web" / "treaty-excerpt-locales-20260824.json"


def _load_rules() -> list[dict]:
    rules: list[dict] = []
    for path in sorted(RULE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rules.extend(payload.get("rules", []))
    return rules


def main() -> int:
    rules = _load_rules()
    locale_registry = json.loads(LOCALE_REGISTRY.read_text(encoding="utf-8"))
    locale_entries = locale_registry.get("entries", {})

    required: set[tuple[str, str]] = set()
    income_types: dict[tuple[str, str], set[str]] = defaultdict(set)

    for rule in rules:
        if rule.get("verification_status") != "verified":
            continue
        if rule.get("effect") != "rate":
            continue
        if rule.get("legal_layer") not in {"treaty", "protocol", "mli"}:
            continue
        country = str(rule.get("recipient_country") or "").upper()
        article = str(rule.get("article") or "").strip()
        if not country or not article:
            continue
        key = (country, article)
        required.add(key)
        income_types[key].add(str(rule.get("income_type") or ""))

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

    missing = sorted(required - covered)
    extra = sorted(covered - required)
    packages = sorted({country for country, _ in required})
    covered_packages = sorted({country for country, _ in covered if (country, _) in required})

    print("TaxTreat treaty excerpt EN locale coverage")
    print(f"Verified treaty packages: {len(packages)}")
    print(f"Required country/article pairs: {len(required)}")
    print(f"Covered country/article pairs: {len(required & covered)}")
    print(f"Missing country/article pairs: {len(missing)}")
    print(f"Packages with at least one EN excerpt: {len(covered_packages)}")

    if missing:
        print("\nMissing EN treaty excerpt variants:")
        for country, article in missing:
            incomes = ",".join(sorted(value for value in income_types[(country, article)] if value))
            print(f"  {country} Article {article}: {incomes or '-'}")

    if extra:
        print("\nRegistry entries not referenced by verified treaty rules:")
        for country, article in extra:
            print(f"  {country} Article {article}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
