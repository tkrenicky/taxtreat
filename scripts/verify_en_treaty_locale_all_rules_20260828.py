from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"


def main() -> int:
    failures = []
    checked = 0
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
        rules = locale.get("rules", {})
        articles = locale.get("articles", {})
        for rule in package.get("rules", []):
            if rule.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            if rule.get("effect") != "rate":
                continue
            checked += 1
            rid = str(rule.get("rule_id") or "")
            article = str(rule.get("article") or "")
            exact = (rules.get(rid) or {}).get("en") or {}
            article_en = (articles.get(article) or {}).get("en") or {}
            if not (exact.get("text") or article_en.get("text")):
                failures.append(f"{country} {rid} Article {article}: no usable EN treaty text/summary")

    if failures:
        raise AssertionError("EN treaty locale coverage failures:\n" + "\n".join(failures))
    if checked < 100:
        raise AssertionError(f"Suspiciously low treaty-rule coverage: {checked}")
    print(f"EN treaty locale rule coverage: PASS ({checked} treaty rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
