from __future__ import annotations

import json
from pathlib import Path

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

    bd = json.loads(
        (ROOT / "data" / "legal_rules_stage6" / "bd.json").read_text(encoding="utf-8")
    )
    rule = next(r for r in bd["rules"] if r["rule_id"] == "CZ-BD-DIVIDEND-CURRENT-1")
    facts = {c["fact"] for c in rule.get("conditions", [])}
    forbidden = {
        "holding_period_includes_payment_date",
        "holding_period_reorganisation_continuity",
    }
    leaked = facts & forbidden
    if leaked:
        failures.append(
            "BD dividend rule contains holding-period counting pseudo-facts: "
            + ", ".join(sorted(leaked))
        )

    if failures:
        raise AssertionError(
            "Holding-period regression failures:\n" + "\n".join(failures)
        )

    print("Holding-period regressions: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
