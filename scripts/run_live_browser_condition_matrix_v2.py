from __future__ import annotations

import json
import sys
from copy import deepcopy
from typing import Any

from playwright.sync_api import Page

import run_live_browser_condition_matrix as base
from taxtreat.services import intake


PRIMARY_BROWSER_FACTS = {
    "beneficial_owner",
    "recipient_is_treaty_resident",
    "permanent_establishment_connection",
    "ownership_percent",
    "direct_ownership",
    "holding_period_months",
    "direct_or_indirect_voting_ownership",
    "voting_ownership",
    "arm_length_amount",
    "payment_is_arm_length_amount",
    "royalty_category",
}


def install_runtime_guidance() -> None:
    intake.FACT_GUIDANCE.update(
        {
            "article_11_special_exemption": {
                "prompt": (
                    "Spadá příjemce úroku do zvláštní veřejné nebo "
                    "institucionální kategorie, kterou příslušná smlouva "
                    "výslovně osvobozuje?"
                ),
                "why": (
                    "Některé smlouvy osvobozují úrok pouze při přesně "
                    "vymezeném postavení příjemce."
                ),
                "response_type": "boolean",
                "documents": [
                    "Doklady k právnímu postavení příjemce",
                    "Úvěrová nebo zápůjční smlouva",
                ],
            },
            "related_party_status": {
                "prompt": "Jde o platbu mezi spojenými osobami?",
                "why": (
                    "U některých smluv mohou zvláštní vztahy mezi plátcem "
                    "a příjemcem ovlivnit použitelný režim."
                ),
                "response_type": "choice",
                "options": [["unrelated", "Ne"], ["related", "Ano"]],
                "documents": [
                    "Vlastnická struktura",
                    "Úvěrová nebo zápůjční smlouva",
                ],
            },
        }
    )


def value_equal(left: Any, right: Any) -> bool:
    def normalized(value: Any) -> Any:
        if isinstance(value, str) and value.lower() in {"true", "false"}:
            return value.lower() == "true"
        return value

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
            if (
                target_fact not in PRIMARY_BROWSER_FACTS
                and not dynamic_browser_fact
            ):
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
            condition[1] == "related_party_status"
            for condition in scope_conditions
        ):
            continue

        # Tunisia Article 12 only asks the technical/economic study or
        # technical-assistance question inside the treaty branch whose royalty
        # category is "other". Make that prerequisite explicit while keeping
        # the boolean as the fact under test.
        if (
            target_fact
            == "royalty_is_technical_or_economic_study_or_technical_assistance"
        ):
            item["payload"] = deepcopy(item["payload"])
            item["payload"]["facts"]["royalty_category"] = "other"

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
        page.wait_for_function(
            "() => Boolean(document.querySelector('#payer-dialog')?.open)"
        )
        form = page.locator("#payer-dialog #payer-form")
        country = form.locator('[name="payer_country"]')
        country.wait_for(state="visible")
        country.select_option("SK")
        form.locator('[name="payer_id"]').wait_for(state="visible")
        form.locator('[name="payer_id"]').fill("12345679")
        form.locator('[name="payer_name"]').fill("Matrix SK s.r.o.")
        form.locator('[name="payer_vat_id"]').fill("SK2020000000")
        form.locator("[data-save-payer]").click()
        page.wait_for_function(
            "() => !document.querySelector('#payer-dialog')?.open"
        )
        page.wait_for_function(
            "() => document.body.dataset.sourceCountry === 'SK'"
        )

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
    page.locator(
        '[data-view="recipient-detail"] [data-edit-recipient]:visible'
    ).click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('#recipient-dialog')?.open)"
    )
    dialog = page.locator("#recipient-dialog #recipient-edit-form")
    dialog.locator('[name="recipient_country"]').select_option(
        recipient_country
    )
    dialog.locator('[name="beneficial_owner"]').select_option("")
    dialog.locator('[name="treaty_resident"]').select_option("")
    dialog.locator('[name="pe_connection"]').select_option("")
    dialog.locator('button[type="submit"]').click()
    page.wait_for_function(
        "() => !document.querySelector('#recipient-dialog')?.open"
    )


def set_radio(form, name: str, value: bool) -> None:
    radio = form.locator(
        f'[name="{name}"][value="{str(bool(value)).lower()}"]'
    )
    label = radio.locator("xpath=ancestor::label[1]")
    base.check(label.count() == 1, f"missing visible label for {name}")
    label.click()
    base.check(radio.is_checked(), f"radio {name} did not become checked")


def finish_dynamic_questions(page: Page, payload: dict[str, Any]) -> None:
    for _ in range(30):
        if page.locator('.flow-step[data-step="4"].active').count():
            return
        if page.locator("#workspace-error").is_visible():
            raise AssertionError(
                "workspace error: "
                + page.locator("#workspace-error").inner_text().strip()
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
                if (document.querySelector('.flow-step[data-step="4"].active')) {
                    return 'result';
                }
                const button = document.querySelector('#workspace-submit');
                if (
                    button && !button.disabled &&
                    (button.offsetWidth || button.offsetHeight || button.getClientRects().length)
                ) {
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
    install_runtime_guidance()
    base._original_browser_scenarios = base.browser_scenarios
    base.value_equal = value_equal
    base.browser_scenarios = browser_scenarios
    base.bootstrap = bootstrap
    base.set_recipient_country = set_recipient_country
    base.set_radio = set_radio
    base.finish_dynamic_questions = finish_dynamic_questions


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
