from __future__ import annotations

from pathlib import Path

from taxtreat.engine.dividend_rule_normalization import (
    DIVIDEND_CONDITION_PATCHES,
    DIVIDEND_SOURCE_PATCHES,
)
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

    for rule_id, expected in sorted(DIVIDEND_SOURCE_PATCHES.items()):
        country = rule_id.split("-")[1].lower()
        rules = load_legal_rules(RULE_DIR / f"{country}.json")
        rule = next(item for item in rules if item.rule_id == rule_id)

        checks = {
            "legal_instrument": rule.legal_instrument,
            "legal_layer": rule.legal_layer,
            "source_id": rule.source_id,
            "source_url": rule.source_url,
            "source_text": rule.source_text,
            "source_excerpt_hash": rule.source_excerpt_hash,
        }
        for field, actual in checks.items():
            if actual != expected[field]:
                failures.append(
                    f"{rule_id}: {field} expected {expected[field]!r}, got {actual!r}"
                )

        if rule.effective_from is None or rule.effective_from.isoformat() != expected["effective_from"]:
            failures.append(
                f"{rule_id}: effective_from must be {expected['effective_from']}"
            )
        if rule.evidence_source_ids != expected["evidence_source_ids"]:
            failures.append(
                f"{rule_id}: protocol evidence_source_ids mismatch"
            )

    uz_rules = load_legal_rules(RULE_DIR / "uz.json")
    uz_5 = next(rule for rule in uz_rules if rule.rule_id == "CZ-UZ-DIVIDEND-CURRENT-1")
    uz_10 = next(rule for rule in uz_rules if rule.rule_id == "CZ-UZ-DIVIDEND-CURRENT-2")
    if uz_5.rate != 5 or uz_10.rate != 10:
        failures.append("UZ protocol dividend branches must remain 5% / 10%")
    if uz_5.source_id == "SRC-93B80AB9D2395397" or uz_10.source_id == "SRC-93B80AB9D2395397":
        failures.append("UZ protocol branches must not cite the superseded base-treaty source")

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
        f"({len(DIVIDEND_CONDITION_PATCHES)} condition patches, "
        f"{len(DIVIDEND_SOURCE_PATCHES)} provenance patches)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
