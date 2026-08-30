from __future__ import annotations

from pathlib import Path

from taxtreat.engine.dividend_rule_normalization import DIVIDEND_CONDITION_PATCHES
from taxtreat.engine.legal_rule_loader import load_legal_rules

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"


def main() -> int:
    failures: list[str] = []

    for rule_id, expected_conditions in sorted(DIVIDEND_CONDITION_PATCHES.items()):
        country = rule_id.split("-")[1].lower()
        rules = load_legal_rules(RULE_DIR / f"{country}.json")
        rule = next(item for item in rules if item.rule_id == rule_id)

        expected_facts = {str(condition["fact"]) for condition in expected_conditions}
        actual_facts = {condition.fact for condition in rule.conditions}
        if actual_facts != expected_facts:
            failures.append(
                f"{rule_id}: expected facts {sorted(expected_facts)}, "
                f"got {sorted(actual_facts)}"
            )

        if "voting_ownership" in expected_facts and "ownership_percent" in actual_facts:
            failures.append(
                f"{rule_id}: voting-rights branch still depends on capital ownership_percent"
            )

    workspace = (ROOT / "app" / "web" / "workspace.js").read_text(encoding="utf-8")
    required_web_fragments = (
        "facts.voting_ownership =",
        "facts.voting_power_control =",
        "facts.direct_or_indirect_voting_ownership =",
        "facts.direct_ownership =",
    )
    for fragment in required_web_fragments:
        if fragment not in workspace:
            failures.append(f"workspace does not emit required dividend fact: {fragment}")

    if failures:
        raise AssertionError(
            "Dividend normalization regression failures:\n" + "\n".join(failures)
        )

    print(
        "Dividend rule normalization regressions: PASS "
        f"({len(DIVIDEND_CONDITION_PATCHES)} explicit treaty branches)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
