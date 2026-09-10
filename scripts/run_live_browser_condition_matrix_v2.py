from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import date
from typing import Any

from dateutil.relativedelta import relativedelta
from playwright.sync_api import Page

import run_live_browser_condition_matrix as base
from taxtreat.services import intake


COMMON_PRIMARY_BROWSER_FACTS = {
    "beneficial_owner",
    "recipient_is_treaty_resident",
    "permanent_establishment_connection",
}

PRIMARY_BROWSER_FACTS_BY_INCOME = {
    "dividend": {
        "ownership_percent",
        "direct_ownership",
        "holding_period_months",
        "direct_or_indirect_voting_ownership",
        "voting_ownership",
        "voting_power_control",
    },
    "interest": {
        "arm_length_amount",
        "payment_is_arm_length_amount",
    },
    "royalty": {
        "royalty_category",
    },
}

# Some structured treaty rules still use older broad royalty labels. The
# current workspace deliberately asks the user for a more precise canonical
# category. A browser test of a broad branch therefore has to exercise every
# concrete UI category contained in that branch rather than silently selecting
# one arbitrary representative or dropping the branch from browser coverage.
LEGACY_ROYALTY_CATEGORY_EXPANSIONS = {
    "copyright_literary_artistic_scientific_including_films_and_broadcast_media": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
    "patent_trademark_design_model_plan_secret_formula_process_software_equipment_or_knowhow": (
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
}


def normalized(value: Any) -> Any:
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def value_equal(left: Any, right: Any) -> bool:
    left = normalized(left)
    right = normalized(right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) < 1e-9
    return left == right


def browser_scenarios(
    *,
    source_country: str,
    income_type: str,
    shard_index: int,
    shard_count: int,
) -> list[dict[str, Any]]:
    raw = base._original_browser_scenarios(
        source_country=source_country,
        income_type=income_type,
        shard_index=shard_index,
        shard_count=shard_count,
    )
    inv = base.inventory()
    result: list[dict[str, Any]] = []
    income_primary_facts = PRIMARY_BROWSER_FACTS_BY_INCOME.get(income_type, set())

    for scenario in raw:
        item = deepcopy(scenario)
        target_fact = item.get("target_fact")
        target_value = item.get("target_value")
        label = str(item.get("label") or "")
        recipient_country = str(item.get("recipient_country") or "")
        scope_conditions = inv[source_country]["conditions"].get(
            (recipient_country, income_type), set()
        )

        if target_fact:
            guidance = intake.FACT_GUIDANCE.get(str(target_fact), {})
            dynamic_browser_fact = bool(
                guidance
                and guidance.get("client_answerable", True) is not False
                and guidance.get("response_type")
            )
            primary_browser_fact = (
                target_fact in COMMON_PRIMARY_BROWSER_FACTS
                or target_fact in income_primary_facts
            )
            if not primary_browser_fact and not dynamic_browser_fact:
                continue

        if target_fact in {
            "fallback_case",
            "source_state_taxation",
            "general_article_11_2_rate",
            "holding_period_will_reach_months",
        }:
            continue

        if label.endswith(":boundary_or_fail") and target_value == "__taxtreat_other__":
            continue

        if label.endswith(":boundary_or_fail") and target_fact in {
            "holding_period_months",
            "holding_period_years",
            "continuous_holding_period_days",
        }:
            continue

        if label == "related_party" and not any(
            condition[1] == "related_party_status" for condition in scope_conditions
        ):
            continue

        facts = item.get("payload", {}).get("facts", {})
        for key, value in list(facts.items()):
            facts[key] = normalized(value)

        if target_fact == "royalty_is_technical_or_economic_study_or_technical_assistance":
            item["payload"] = deepcopy(item["payload"])
            item["payload"]["facts"]["royalty_category"] = "other"

        if target_fact == "royalty_category":
            expansions = LEGACY_ROYALTY_CATEGORY_EXPANSIONS.get(str(target_value))
            if expansions:
                for canonical_category in expansions:
                    expanded = deepcopy(item)
                    expanded["target_value"] = canonical_category
                    expanded["payload"]["facts"]["royalty_category"] = canonical_category
                    expanded["label"] = f"{label}:ui={canonical_category}"
                    result.append(expanded)
                continue

        result.append(item)

    return result


def bootstrap(page: Page, source_country: str, lang: str) -> None:
    page.goto(
        f"{base.BASE_URL}/ui/{lang}",
        wait_until="domcontentloaded",
        timeout=20_000,
    )
    page.wait_for_function(
        "() => Boolean(window.TaxTreatWorkspaceSourceCountry && window.TaxTreatSourceCountries)"
    )
    page.wait_for_timeout(1000)

    if source_country == "SK":
        page.locator('[data-nav="payers"]:visible').first.click()
        page.wait_for_function(
            "() => Boolean(document.querySelector('[data-view=\"payers\"].active'))"
        )
        page.locator("[data-create-payer]:visible").first.click()
        page.wait_for_function("() => Boolean(document.querySelector('#payer-dialog')?.open)")
        form = page.locator("#payer-dialog #payer-form")
        country = form.locator('[name="payer_country"]')
        country.wait_for(state="visible")
        country.select_option("SK")
        form.locator('[name="payer_id"]').wait_for(state="visible")
        form.locator('[name="payer_id"]').fill("12345679")
        form.locator('[name="payer_name"]').fill("Matrix SK s.r.o.")
        form.locator('[name="payer_vat_id"]').fill("SK2020000000")
        form.locator("[data-save-payer]").click()
        page.wait_for_function("() => !document.querySelector('#payer-dialog')?.open")
        page.wait_for_function("() => document.body.dataset.sourceCountry === 'SK'")

    page.wait_for_function(
        """(expected) => document.querySelectorAll(
            '#new-recipient-form [name="recipient_country"] option'
        ).length === expected""",
        arg=base.source_partner_count(source_country),
    )
    base.check(
        page.evaluate("document.body.dataset.sourceCountry") == source_country,
        f"source-country bootstrap mismatch: {source_country}",
    )
    base.check(
        page.evaluate("document.documentElement.lang") == lang,
        f"language bootstrap mismatch: {lang}",
    )


def set_recipient_country(page: Page, recipient_country: str) -> None:
    page.locator('[data-nav="recipients"]:visible').first.click()
    page.locator('[data-view="recipients"] [data-open-recipient]').click()
    page.locator('[data-view="recipient-detail"] [data-edit-recipient]:visible').click()
    page.wait_for_function("() => Boolean(document.querySelector('#recipient-dialog')?.open)")
    dialog = page.locator("#recipient-dialog #recipient-edit-form")
    dialog.locator('[name="recipient_country"]').select_option(recipient_country)
    dialog.locator('[name="beneficial_owner"]').select_option("")
    dialog.locator('[name="treaty_resident"]').select_option("")
    dialog.locator('[name="pe_connection"]').select_option("")
    dialog.locator('button[type="submit"]').click()
    page.wait_for_function("() => !document.querySelector('#recipient-dialog')?.open")


def start_flow(page: Page) -> None:
    # A completed calculation mutates substantial DOM state. Reload before
    # every scenario so the matrix verifies persistence plus a clean browser
    # lifecycle, rather than accidentally reusing hidden step/result nodes.
    page.reload(wait_until="domcontentloaded", timeout=20_000)
    page.wait_for_function(
        "() => Boolean(window.TaxTreatWorkspaceSourceCountry && window.TaxTreatSourceCountries)"
    )
    page.wait_for_function("() => Boolean(document.body.dataset.sourceCountry)")
    page.wait_for_function(
        "() => Boolean(document.querySelector('[data-nav=\"dashboard\"]'))"
    )

    dashboard = page.locator('[data-nav="dashboard"]:visible')
    base.check(dashboard.count() > 0, "no visible dashboard navigation control")
    dashboard.first.click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('[data-view=dashboard].active'))"
    )
    start = page.locator("[data-start-flow]:visible")
    base.check(start.count() > 0, "no visible New calculation control")
    start.first.click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"1\"].active'))"
    )
    page.locator('[data-next-step="2"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"2\"].active'))"
    )
    page.locator('[data-next-step="3"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"3\"].active'))"
    )


def set_radio(form, name: str, value: bool) -> None:
    radio = form.locator(
        f'[name="{name}"][value="{str(bool(normalized(value))).lower()}"]'
    )
    label = radio.locator("xpath=ancestor::label[1]")
    base.check(label.count() == 1, f"missing visible label for {name}")
    label.click()
    base.check(radio.is_checked(), f"radio {name} did not become checked")


def fill_primary_controls(page: Page, scenario: dict[str, Any]) -> None:
    base._original_fill_primary_controls(page, scenario)
    target_fact = scenario.get("target_fact")
    target_value = normalized(scenario.get("target_value"))

    if target_fact == "voting_power_control":
        control = page.locator('#workspace-payment [name="voting_ownership_percent"]')
        if control.count() and control.is_visible():
            control.fill(str(target_value))

    # Treaty datasets contain both historical names for the same arm's-length
    # payment fact. The workspace exposes one primary select and serializes it
    # as facts.arm_length_amount, so drive that real control for either alias.
    if target_fact == "payment_is_arm_length_amount":
        control = page.locator('#workspace-payment [name="arm_length_amount"]')
        base.check(
            control.count() == 1 and control.is_visible(),
            "missing arm_length_amount primary control for payment alias",
        )
        control.select_option("true" if bool(target_value) else "false")


def acquisition_date_for_months(payload: dict[str, Any], months: Any) -> str:
    transaction_date = date.fromisoformat(str(payload["transaction_date"]))
    numeric_months = float(months)
    rounded = int(round(numeric_months))
    base.check(
        abs(numeric_months - rounded) < 1e-9,
        f"browser date input cannot represent fractional complete months: {months!r}",
    )
    return (transaction_date - relativedelta(months=rounded)).isoformat()


def desired_for_path(payload: dict[str, Any], path: str) -> tuple[bool, Any]:
    if (
        path == "derived.acquisition_date"
        and "holding_period_months" in payload.get("facts", {})
    ):
        return True, acquisition_date_for_months(
            payload,
            payload["facts"]["holding_period_months"],
        )
    return base._original_desired_for_path(payload, path)


def assert_target_reached(
    scenario: dict[str, Any],
    submitted: dict[str, Any],
) -> None:
    target_fact = scenario["target_fact"]
    facts = submitted.get("facts") or {}

    if target_fact == "payment_is_arm_length_amount":
        base.check(
            "arm_length_amount" in facts,
            f"unreachable UI fact payment_is_arm_length_amount for {scenario['label']}",
        )
        base.check(
            value_equal(facts["arm_length_amount"], scenario["target_value"]),
            (
                f"UI fact mismatch payment_is_arm_length_amount for {scenario['label']}: "
                f"expected={scenario['target_value']!r} "
                f"actual_arm_length_amount={facts['arm_length_amount']!r}"
            ),
        )
        return

    if target_fact == "holding_period_months":
        if "holding_period_months" in facts:
            base.check(
                value_equal(facts["holding_period_months"], scenario["target_value"]),
                (
                    f"UI fact mismatch holding_period_months for {scenario['label']}: "
                    f"expected={scenario['target_value']!r} "
                    f"actual={facts['holding_period_months']!r}"
                ),
            )
            return

        derived = submitted.get("derived") or {}
        expected_date = acquisition_date_for_months(
            scenario["payload"], scenario["target_value"]
        )
        base.check(
            "acquisition_date" in derived,
            f"unreachable UI fact holding_period_months for {scenario['label']}",
        )
        base.check(
            derived["acquisition_date"] == expected_date,
            (
                f"UI derived acquisition date mismatch for {scenario['label']}: "
                f"expected={expected_date!r} actual={derived['acquisition_date']!r}"
            ),
        )
        return

    base._original_assert_target_reached(scenario, submitted)


def finish_dynamic_questions(page: Page, payload: dict[str, Any]) -> None:
    for _ in range(30):
        if page.locator('.flow-step[data-step="4"].active').count():
            return
        if page.locator("#workspace-error").is_visible():
            raise AssertionError(
                "workspace error: " + page.locator("#workspace-error").inner_text().strip()
            )

        questions = page.locator("#workspace-questions [data-input-path]")
        count = questions.count()
        if count == 0:
            page.wait_for_timeout(20)
            continue

        restart = False
        for index in range(count):
            if page.locator('.flow-step[data-step="4"].active').count():
                return
            question = questions.nth(index)
            try:
                base.fill_question(question, payload)
            except Exception:
                if page.locator('.flow-step[data-step="4"].active').count():
                    return
                if question.count() == 0:
                    restart = True
                    break
                raise

        if restart:
            page.wait_for_timeout(10)
            continue

        state = page.evaluate(
            """() => {
                if (document.querySelector('.flow-step[data-step="4"].active')) return 'result';
                const button = document.querySelector('#workspace-submit');
                if (button && !button.disabled &&
                    (button.offsetWidth || button.offsetHeight || button.getClientRects().length)) {
                    return 'submit';
                }
                return 'wait';
            }"""
        )
        if state == "result":
            return
        if state != "submit":
            page.wait_for_timeout(15)
            continue

        try:
            page.locator("#workspace-submit").click(timeout=1000)
        except Exception:
            if page.locator('.flow-step[data-step="4"].active').count():
                return
            page.wait_for_timeout(10)
            continue
        page.wait_for_timeout(30)

    raise AssertionError("dynamic questions did not resolve")


def install() -> None:
    base._original_browser_scenarios = base.browser_scenarios
    base._original_fill_primary_controls = base.fill_primary_controls
    base._original_desired_for_path = base.desired_for_path
    base._original_assert_target_reached = base.assert_target_reached
    base.value_equal = value_equal
    base.browser_scenarios = browser_scenarios
    base.bootstrap = bootstrap
    base.set_recipient_country = set_recipient_country
    base.start_flow = start_flow
    base.set_radio = set_radio
    base.fill_primary_controls = fill_primary_controls
    base.desired_for_path = desired_for_path
    base.assert_target_reached = assert_target_reached
    base.finish_dynamic_questions = finish_dynamic_questions


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
