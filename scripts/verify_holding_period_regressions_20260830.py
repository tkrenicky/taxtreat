from __future__ import annotations

import json
from pathlib import Path

from taxtreat.engine.dividend_rule_normalization import normalize_raw_legal_rule


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    failures: list[str] = []

    workspace = (ROOT / "app" / "web" / "workspace.js").read_text(encoding="utf-8")
    expected = (
        "facts.continuous_holding_period_days =\n"
        "      completeDays(acquisitionDate, transactionDate) + 1;"
    )
    if expected not in workspace:
        failures.append(
            "workspace.js must calculate continuous_holding_period_days inclusively"
        )

    payload = json.loads(
        (ROOT / "data" / "legal_rules_stage6" / "bd.json").read_text(
            encoding="utf-8"
        )
    )
    raw_rule = next(
        row
        for row in payload["rules"]
        if row["rule_id"] == "CZ-BD-DIVIDEND-CURRENT-1"
    )
    rule = normalize_raw_legal_rule(raw_rule)
    facts = {str(row.get("fact")) for row in rule.get("conditions", [])}
    expected_facts = {
        "recipient_entity_type",
        "direct_ownership",
        "ownership_percent",
        "beneficial_owner",
        "continuous_holding_period_days",
    }
    if facts != expected_facts:
        failures.append(
            "BD effective runtime holding-period facts differ from the "
            "condition-aware normalization contract"
        )

    if failures:
        raise AssertionError(
            "Holding-period regression failures:\n" + "\n".join(failures)
        )

    print("Holding-period regressions: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
