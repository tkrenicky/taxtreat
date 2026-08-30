from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"

SPECIAL_INTEREST_FACTS = {
    "article_11_public_body_exemption",
    "article_11_3_exemption",
    "article_11_3a_exemption",
    "special_article_11_3_exemption",
    "article_11_3_public_financing_exemption",
    "official_foreign_exchange_reserve_investment",
}

GENERIC_INTEREST_FACTS = {
    "beneficial_owner",
    "recipient_is_treaty_resident",
    "fallback_case",
    "general_article_11_2_rate",
    "source_state_taxation",
    "permanent_establishment_connection",
}


def _facts(rule: dict) -> set[str]:
    return {
        str(c.get("fact") or "")
        for c in rule.get("conditions", [])
        if str(c.get("fact") or "")
    }


def main() -> int:
    failures: list[str] = []

    for path in sorted(RULE_DIR.glob("*.json")):
        package = json.loads(path.read_text(encoding="utf-8"))
        country = package.get("country_pair", {}).get("recipient_country")
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)

        for rule in package.get("rules", []):
            if rule.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            if rule.get("effect") != "rate" or rule.get("income_type") != "interest":
                continue
            groups[(str(rule.get("article") or ""), str(rule.get("legal_layer") or ""))].append(rule)

        for (article, _layer), rules in groups.items():
            general = [
                r for r in rules
                if _facts(r)
                and _facts(r).issubset(GENERIC_INTEREST_FACTS)
                and float(r.get("rate")) > 0
            ]
            if not general:
                continue

            best_general_priority = min(int(r.get("priority", 100)) for r in general)

            for rule in rules:
                facts = _facts(rule)
                if not (facts & SPECIAL_INTEREST_FACTS):
                    continue
                if float(rule.get("rate")) != 0:
                    continue
                if int(rule.get("priority", 100)) >= best_general_priority:
                    failures.append(
                        f"{country} {rule.get('rule_id')} Article {article}: "
                        f"special 0% interest branch priority {rule.get('priority')} "
                        f"does not outrank general positive-rate branch priority "
                        f"{best_general_priority}"
                    )

    if failures:
        raise AssertionError(
            "Special-interest priority failures:\n" + "\n".join(sorted(set(failures)))
        )

    print("Special-interest priority ordering: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
