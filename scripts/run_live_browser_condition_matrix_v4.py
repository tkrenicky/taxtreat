from __future__ import annotations

import sys
from copy import deepcopy
from datetime import date, timedelta
from typing import Any

import run_live_browser_condition_matrix as base
import run_live_browser_condition_matrix_v2 as v2
import run_live_browser_condition_matrix_v3 as v3


RECIPIENT_TYPE_FOR_TARGET = {
    "recipient_is_qualifying_pension_fund": "Fond",
    "recipient_is_partnership": "Jiný subjekt",
    "recipient_is_central_bank": "Jiný subjekt",
    "article_10_public_body_exemption": "Jiný subjekt",
    "article_11_public_body_exemption": "Jiný subjekt",
    "article_11_3_public_financing_exemption": "Jiný subjekt",
}
RECIPIENT_TYPE_FROM_FACT = {
    "individual": "Fyzická osoba",
    "fund": "Fond",
    "company": "Společnost",
    "corporate": "Společnost",
    "other": "Jiný subjekt",
}
CURRENT_RECIPIENT_TYPE = "Společnost"


# These treaty-specific questions sit below a canonical royalty-family choice.
# The browser must enter that family through the real payment select before the
# dynamic question can legitimately appear.
ROYALTY_CATEGORY_FOR_TARGET = {
    "royalty_industrial_ip_subcategory": "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    "royalty_is_waiver": "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
}


def browser_scenarios(
    *,
    source_country: str,
    income_type: str,
    shard_index: int,
    shard_count: int,
) -> list[dict[str, Any]]:
    scenarios = v3.browser_scenarios(
        source_country=source_country,
        income_type=income_type,
        shard_index=shard_index,
        shard_count=shard_count,
    )
    result: list[dict[str, Any]] = []
    for scenario in scenarios:
        item = deepcopy(scenario)
        category = ROYALTY_CATEGORY_FOR_TARGET.get(str(item.get("target_fact") or ""))
        if category:
            item["payload"]["facts"]["royalty_category"] = category
        result.append(item)
    return result


def ensure_recipient_type(page, desired_type: str) -> None:
    global CURRENT_RECIPIENT_TYPE
    if desired_type == CURRENT_RECIPIENT_TYPE:
        return

    # We are already in payment step 3. Move back through the real flow UI,
    # edit the persisted recipient profile, then return to payment. This avoids
    # injecting browser state and verifies the same controls a user would use.
    page.locator('[data-flow-step="2"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"2\"].active'))"
    )
    page.locator('.flow-step[data-step="2"] [data-edit-recipient]:visible').click()
    page.wait_for_function("() => Boolean(document.querySelector('#recipient-dialog')?.open)")
    dialog = page.locator("#recipient-dialog #recipient-edit-form")
    type_control = dialog.locator('[name="recipient_type"]')
    base.check(type_control.count() == 1, "recipient type control missing")
    type_control.select_option(label=desired_type)
    dialog.locator('button[type="submit"]').click()
    page.wait_for_function("() => !document.querySelector('#recipient-dialog')?.open")
    page.locator('[data-next-step="3"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"3\"].active'))"
    )
    CURRENT_RECIPIENT_TYPE = desired_type


def desired_recipient_type(scenario: dict[str, Any]) -> str:
    target_fact = str(scenario.get("target_fact") or "")
    specialized = RECIPIENT_TYPE_FOR_TARGET.get(target_fact)
    if specialized:
        return specialized

    entity_type = str(
        (scenario.get("payload", {}).get("facts", {}) or {}).get(
            "recipient_entity_type", "company"
        )
    )
    return RECIPIENT_TYPE_FROM_FACT.get(entity_type, "Společnost")


def fill_primary_controls(page, scenario: dict[str, Any]) -> None:
    target_fact = scenario.get("target_fact")
    target_value = scenario.get("target_value")

    ensure_recipient_type(page, desired_recipient_type(scenario))

    # Run the current real-UI driver first, then correct the few target facts
    # whose historical scenario payload also contains a conflicting baseline
    # alias or whose threshold cannot be represented by v1's fixed date map.
    v2.fill_primary_controls(page, scenario)
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
    base.browser_scenarios = browser_scenarios
    base.fill_primary_controls = fill_primary_controls


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
