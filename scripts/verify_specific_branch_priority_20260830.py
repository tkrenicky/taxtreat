from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from taxtreat.engine.dividend_rule_normalization import normalize_raw_legal_rule

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"

RULE_CONTROL_FACTS = {
    "fallback_case",
    "source_state_taxation",
    "general_article_11_2_rate",
}


def _condition_key(condition: dict) -> tuple[str, str, str, str]:
    return (
        str(condition.get("fact_source") or "transaction"),
        str(condition.get("fact") or ""),
        str(condition.get("operator") or ""),
        json.dumps(condition.get("value"), sort_keys=True),
    )


def _material_conditions(rule: dict) -> set[tuple[str, str, str, str]]:
    return {
        _condition_key(condition)
        for condition in rule.get("conditions", [])
        if str(condition.get("fact") or "") not in RULE_CONTROL_FACTS
    }


def _outcome(rule: dict) -> tuple:
    return (rule.get("effect"), rule.get("rate"), rule.get("tax_treatment"))


def main() -> int:
    failures: list[str] = []

    for path in sorted(RULE_DIR.glob("*.json")):
        package = json.loads(path.read_text(encoding="utf-8"))
        country = package.get("country_pair", {}).get("recipient_country")
        groups: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)

        for raw_rule in package.get("rules", []):
            rule = normalize_raw_legal_rule(raw_rule)
            if rule.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            if rule.get("effect") != "rate":
                continue
            key = (
                str(rule.get("income_type") or ""),
                str(rule.get("legal_layer") or ""),
                str(rule.get("article") or ""),
                str(rule.get("effective_from") or ""),
                str(rule.get("effective_to") or ""),
            )
            groups[key].append(rule)

        for key, rules in groups.items():
            for special in rules:
                special_conditions = _material_conditions(special)
                if not special_conditions:
                    continue
                for broader in rules:
                    if special is broader or _outcome(special) == _outcome(broader):
                        continue
                    broader_conditions = _material_conditions(broader)
                    if not broader_conditions < special_conditions:
                        continue
                    if int(special.get("priority", 100)) >= int(broader.get("priority", 100)):
                        failures.append(
                            f"{country} {key[0]} Article {key[2]}: "
                            f"specific branch {special.get('rule_id')} "
                            f"(priority {special.get('priority')}, outcome {_outcome(special)}) "
                            f"does not outrank broader branch {broader.get('rule_id')} "
                            f"(priority {broader.get('priority')}, outcome {_outcome(broader)})"
                        )

    if failures:
        raise AssertionError(
            "Specific-branch priority failures:\n" + "\n".join(sorted(set(failures)))
        )

    print("Specific-branch priority ordering after runtime remediation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
