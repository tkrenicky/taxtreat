from __future__ import annotations

from pathlib import Path

from taxtreat.engine.legal_rule_loader import load_legal_rules

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"

EXPECTED_FACTS = {
    "CZ-GB-DIVIDEND-CURRENT-1": {
        "recipient_entity_type",
        "voting_ownership",
        "beneficial_owner",
    },
    "CZ-US-DIVIDEND-CURRENT-1": {
        "recipient_entity_type",
        "voting_ownership",
        "beneficial_owner",
    },
    "CZ-IE-DIVIDEND-CURRENT-1": {
        "recipient_entity_type",
        "direct_ownership",
        "voting_ownership",
        "beneficial_owner",
    },
    "CZ-FR-DIVIDEND-CURRENT-1": {
        "recipient_entity_type",
        "direct_ownership",
        "ownership_percent",
        "beneficial_owner",
    },
    "CZ-LU-DIVIDEND-CURRENT-1": {
        "recipient_entity_type",
        "recipient_is_partnership",
        "direct_ownership",
        "ownership_percent",
        "holding_period_months",
        "beneficial_owner",
    },
}

COUNTRY_BY_RULE = {
    rule_id: rule_id.split("-")[1].lower()
    for rule_id in EXPECTED_FACTS
}


def main() -> int:
    failures: list[str] = []

    for rule_id, expected in EXPECTED_FACTS.items():
        country = COUNTRY_BY_RULE[rule_id]
        rules = load_legal_rules(RULE_DIR / f"{country}.json")
        rule = next(item for item in rules if item.rule_id == rule_id)
        actual = {condition.fact for condition in rule.conditions}

        if actual != expected:
            failures.append(
                f"{rule_id}: expected facts {sorted(expected)}, got {sorted(actual)}"
            )

        if "voting_ownership" in expected and "ownership_percent" in actual:
            failures.append(
                f"{rule_id}: voting-rights treaty branch still depends on capital ownership_percent"
            )

    workspace = (ROOT / "app" / "web" / "workspace.js").read_text(encoding="utf-8")
    required_web_fragments = (
        "facts.voting_ownership =",
        "facts.voting_power_control =",
        "facts.direct_or_indirect_voting_ownership =",
    )
    for fragment in required_web_fragments:
        if fragment not in workspace:
            failures.append(f"workspace does not emit required voting fact: {fragment}")

    if failures:
        raise AssertionError(
            "Dividend normalization regression failures:\n" + "\n".join(failures)
        )

    print("Dividend rule normalization regressions: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
