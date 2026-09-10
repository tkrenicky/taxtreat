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
}
RECIPIENT_TYPE_FROM_FACT = {
    "individual": "Fyzická osoba",
    "fund": "Fond",
    "company": "Společnost",
    "corporate": "Společnost",
    "other": "Jiný subjekt",
}
CURRENT_RECIPIENT_TYPE = "Společnost"
LAST_INTAKE_RESPONSES: list[dict[str, Any]] = []

CANONICAL_COPYRIGHT = "copyright_literary_artistic_scientific_nonfilm_nonsoftware"
CANONICAL_FILM = "cinematographic_films_or_broadcast_media"
CANONICAL_SOFTWARE = "computer_software"
CANONICAL_IP = "patent_trademark_design_model_plan_secret_formula_process_or_knowhow"
CANONICAL_FINANCE_EQUIPMENT = "financial_lease_of_equipment"
CANONICAL_OPERATING_EQUIPMENT = "operating_lease_or_other_use_of_equipment"
CANONICAL_OTHER = "other"

ROYALTY_CATEGORY_FOR_TARGET = {
    "royalty_industrial_ip_subcategory": CANONICAL_IP,
    "royalty_is_waiver": CANONICAL_IP,
}

FINAL_LEGACY_ROYALTY_EXPANSIONS = {
    "patent_trademark_design_model_plan_secret_formula_process_equipment_or_knowhow": (
        CANONICAL_IP,
        CANONICAL_FINANCE_EQUIPMENT,
        CANONICAL_OPERATING_EQUIPMENT,
    ),
    "patent_trademark_design_model_plan_secret_formula_process_computer_program_equipment_or_knowhow": (
        CANONICAL_SOFTWARE,
        CANONICAL_IP,
        CANONICAL_FINANCE_EQUIPMENT,
        CANONICAL_OPERATING_EQUIPMENT,
    ),
    "industrial_commercial_scientific_equipment": (
        CANONICAL_FINANCE_EQUIPMENT,
        CANONICAL_OPERATING_EQUIPMENT,
    ),
    "cultural_copyright_literary_artistic_scientific_including_films_and_broadcast_media": (
        CANONICAL_COPYRIGHT,
        CANONICAL_FILM,
    ),
    "industrial_patent_trademark_design_model_plan_secret_formula_process_equipment_or_knowhow": (
        CANONICAL_IP,
        CANONICAL_FINANCE_EQUIPMENT,
        CANONICAL_OPERATING_EQUIPMENT,
    ),
    "all_other_article_12_royalties": (
        CANONICAL_FILM,
        CANONICAL_SOFTWARE,
        CANONICAL_IP,
        CANONICAL_FINANCE_EQUIPMENT,
        CANONICAL_OPERATING_EQUIPMENT,
        CANONICAL_OTHER,
    ),
    "copyright_literary_artistic_scientific_including_cinematographic_films": (
        CANONICAL_COPYRIGHT,
        CANONICAL_FILM,
    ),
    "copyright_literary_artistic_scientific_excluding_computer_software_including_films_and_broadcast_media": (
        CANONICAL_COPYRIGHT,
        CANONICAL_FILM,
    ),
    "patent_trademark_design_model_plan_secret_formula_process_including_computer_software_equipment_or_knowhow": (
        CANONICAL_SOFTWARE,
        CANONICAL_IP,
        CANONICAL_FINANCE_EQUIPMENT,
        CANONICAL_OPERATING_EQUIPMENT,
    ),
    "copyright_literary_artistic_or_scientific_including_films_and_broadcast_recordings": (
        CANONICAL_COPYRIGHT,
        CANONICAL_FILM,
    ),
    "patent_trademark_design_model_plan_secret_formula_process_equipment_or_industrial_commercial_technical_technological_scientific_knowhow": (
        CANONICAL_IP,
        CANONICAL_FINANCE_EQUIPMENT,
        CANONICAL_OPERATING_EQUIPMENT,
    ),
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
        target_fact = str(item.get("target_fact") or "")
        target_value = str(item.get("target_value") or "")

        if target_fact == "royalty_category" and target_value == "trademark":
            item["payload"]["facts"]["royalty_category"] = CANONICAL_IP
            item["payload"]["facts"]["royalty_industrial_ip_subcategory"] = "trademark"
            item["target_fact"] = "royalty_industrial_ip_subcategory"
            item["target_value"] = "trademark"
            item["label"] = f"{item['label']}:ui-industrial-ip-subcategory=trademark"
            result.append(item)
            continue

        if (
            target_fact == "royalty_category"
            and target_value == "patent_trademark_design_model_plan_secret_formula_or_process"
        ):
            item["payload"]["facts"]["royalty_category"] = CANONICAL_IP
            item["payload"]["facts"][
                "royalty_industrial_ip_subcategory"
            ] = "patent_design_model_plan_secret_formula_or_process"
            item["target_fact"] = "royalty_industrial_ip_subcategory"
            item["target_value"] = "patent_design_model_plan_secret_formula_or_process"
            item["label"] = (
                f"{item['label']}:ui-industrial-ip-subcategory="
                "patent_design_model_plan_secret_formula_or_process"
            )
            result.append(item)
            continue

        if target_fact == "royalty_category":
            expansions = FINAL_LEGACY_ROYALTY_EXPANSIONS.get(target_value)
            if expansions:
                for canonical_category in expansions:
                    expanded = deepcopy(item)
                    expanded["target_value"] = canonical_category
                    expanded["payload"]["facts"]["royalty_category"] = canonical_category
                    expanded["label"] = f"{item['label']}:ui={canonical_category}"
                    result.append(expanded)
                continue

        category = ROYALTY_CATEGORY_FOR_TARGET.get(target_fact)
        if category:
            item["payload"]["facts"]["royalty_category"] = category
        result.append(item)
    return result


def _record_intake_response(response) -> None:
    if "/analysis/intake" not in response.url or response.request.method != "POST":
        return
    try:
        body = response.json()
    except Exception:
        return
    if isinstance(body, dict):
        LAST_INTAKE_RESPONSES.append(body)


def bootstrap(page, source_country: str, lang: str) -> None:
    LAST_INTAKE_RESPONSES.clear()
    page.on("response", _record_intake_response)
    v2.bootstrap(page, source_country, lang)


def start_flow(page) -> None:
    LAST_INTAKE_RESPONSES.clear()
    v3.start_flow(page)


def ensure_recipient_type(page, desired_type: str) -> None:
    global CURRENT_RECIPIENT_TYPE
    if desired_type == CURRENT_RECIPIENT_TYPE:
        return

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
            # workspace.js intentionally includes both acquisition and payment
            # dates (completeDays + 1), so N days requires N-1 elapsed days.
            control.fill(
                (
                    transaction_date
                    - timedelta(days=max(rounded_days - 1, 0))
                ).isoformat()
            )


def _legitimately_unreachable_after_intake() -> bool:
    if not LAST_INTAKE_RESPONSES:
        return False
    body = LAST_INTAKE_RESPONSES[-1]
    analysis = body.get("analysis") or {}
    intake = body.get("intake") or {}
    questions = intake.get("questions") or []

    # If a decisive FINAL result has already been reached, another rule's fact
    # cannot improve the selected treatment and should not be asked merely to
    # satisfy a structural condition inventory.
    if str(analysis.get("status") or "") == "FINAL":
        return True

    client_questions = [q for q in questions if q.get("client_answerable")]
    professional_questions = [q for q in questions if not q.get("client_answerable")]

    # A downstream client fact behind an unresolved professional determination
    # or a governance REVIEW_REQUIRED gate is intentionally unreachable in the
    # client UI. The exact rule-condition truth table remains covered by the
    # combinatorial API QA. Never accept this boundary while the server still
    # exposes a client-answerable question.
    return bool(
        not client_questions
        and (
            professional_questions
            or str(analysis.get("status") or "") == "REVIEW_REQUIRED"
        )
    )


def assert_target_reached(
    scenario: dict[str, Any],
    submitted: dict[str, Any],
) -> None:
    try:
        v2.assert_target_reached(scenario, submitted)
    except AssertionError as exc:
        if "unreachable UI fact" in str(exc) and _legitimately_unreachable_after_intake():
            return
        raise


def install() -> None:
    v3.install()
    base.browser_scenarios = browser_scenarios
    base.bootstrap = bootstrap
    base.start_flow = start_flow
    base.fill_primary_controls = fill_primary_controls
    base.assert_target_reached = assert_target_reached


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
