from __future__ import annotations

import sys
from datetime import date, timedelta
from typing import Any

import run_live_browser_condition_matrix as base
import run_live_browser_condition_matrix_v2 as v2
import run_live_browser_condition_matrix_v3 as v3


def fill_primary_controls(page, scenario: dict[str, Any]) -> None:
    # Run the current real-UI driver first, then correct the few target facts
    # whose historical scenario payload also contains a conflicting baseline
    # alias or whose threshold cannot be represented by v1's fixed date map.
    v2.fill_primary_controls(page, scenario)

    target_fact = scenario.get("target_fact")
    target_value = scenario.get("target_value")
    form = page.locator("#workspace-payment")

    if target_fact in {
        "direct_or_indirect_voting_ownership",
        "voting_ownership",
        "voting_power_control",
    }:
        control = form.locator('[name="voting_ownership_percent"]')
        if control.count() and control.is_visible():
            control.fill(str(target_value))

    if target_fact == "holding_period_months":
        control = form.locator('[name="acquisition_date"]')
        if control.count() and control.is_visible():
            control.fill(v2.acquisition_date_for_months(scenario["payload"], target_value))

    if target_fact == "continuous_holding_period_days":
        numeric_days = float(target_value)
        rounded_days = int(round(numeric_days))
        base.check(
            abs(numeric_days - rounded_days) < 1e-9,
            f"browser date input cannot represent fractional complete days: {target_value!r}",
        )
        transaction_date = date.fromisoformat(str(scenario["payload"]["transaction_date"]))
        control = form.locator('[name="acquisition_date"]')
        if control.count() and control.is_visible():
            control.fill((transaction_date - timedelta(days=rounded_days)).isoformat())


def install() -> None:
    v3.install()
    base.fill_primary_controls = fill_primary_controls


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
