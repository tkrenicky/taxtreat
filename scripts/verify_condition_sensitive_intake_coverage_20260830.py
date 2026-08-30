from __future__ import annotations

import json
from pathlib import Path

from taxtreat.engine.dividend_rule_normalization import normalize_raw_legal_rule
from taxtreat.services.intake import (
    DERIVED_TRANSACTION_FACTS,
    DETERMINATION_GUIDANCE,
    FACT_GUIDANCE,
    PROFESSIONAL_FACT_GROUPS,
    RULE_CONTROL_FACTS,
    RULE_VALUE_BOOLEAN_GUIDANCE,
)

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"

BASE_RECIPIENT_ENTITY_TYPES = {"company", "individual", "fund", "other"}

# These aliases intentionally remain fail-closed professional-review facts.
# Listing them here makes that treatment explicit instead of silently accepting
# arbitrary unknown facts.
EXPLICIT_PROFESSIONAL_ONLY_FACTS = {
    "detailed_eligibility_review_required",
    "distributed_vs_undistributed_corporate_tax_rate_difference",
}


def main() -> int:
    failures: list[str] = []
    explicit: set[str] = set()
    seen: set[str] = set()

    for path in sorted(RULE_DIR.glob("*.json")):
        package = json.loads(path.read_text(encoding="utf-8"))
        country = package.get("country_pair", {}).get("recipient_country")
        for raw_rule in package.get("rules", []):
            rule = normalize_raw_legal_rule(raw_rule)
            if rule.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            if rule.get("effect") != "rate":
                continue

            for condition in rule.get("conditions", []):
                fact = str(condition.get("fact") or "").strip()
                source = str(condition.get("fact_source") or "transaction").strip()
                if not fact:
                    continue

                if fact == "beneficial_owner":
                    value = condition.get("value")
                    if value not in {True, False, "true", "false"}:
                        failures.append(
                            f"{country} {rule.get('rule_id')}: beneficial_owner={value!r} "
                            "overloads the UBO fact with a treaty-specific category; split it "
                            "into a dedicated condition fact"
                        )
                    continue

                if fact == "fallback_case":
                    continue

                seen.add(fact)

                if fact == "recipient_entity_type":
                    value = condition.get("value")
                    if value not in BASE_RECIPIENT_ENTITY_TYPES:
                        failures.append(
                            f"{country} {rule.get('rule_id')}: recipient_entity_type={value!r} "
                            "is not representable by the base UI entity-type field; split the "
                            "special treaty qualification into its own fact"
                        )
                        continue

                if source == "determination":
                    if fact in DETERMINATION_GUIDANCE:
                        explicit.add(fact)
                    else:
                        failures.append(
                            f"{country} {rule.get('rule_id')}: determination {fact} "
                            "has no explicit DETERMINATION_GUIDANCE classification"
                        )
                    continue

                if (
                    fact in FACT_GUIDANCE
                    or fact in RULE_VALUE_BOOLEAN_GUIDANCE
                    or fact in DERIVED_TRANSACTION_FACTS
                    or fact in RULE_CONTROL_FACTS
                    or fact in PROFESSIONAL_FACT_GROUPS
                    or fact in EXPLICIT_PROFESSIONAL_ONLY_FACTS
                ):
                    explicit.add(fact)
                    continue

                failures.append(
                    f"{country} {rule.get('rule_id')}: transaction fact {fact} "
                    "would fall through to generic professional review"
                )

    if failures:
        raise AssertionError(
            "Condition-sensitive intake coverage failures:\n" + "\n".join(sorted(set(failures)))
        )

    print(
        "Condition-sensitive intake coverage after runtime remediation: PASS "
        f"({len(seen)} special treaty facts; {len(explicit)} explicitly classified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
