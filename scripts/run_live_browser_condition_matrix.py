from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from run_cz_sk_combinatorial_web_qa import (
    EXPECTED,
    INCOME_TYPES,
    base_payload,
    inventory,
    scenario_payloads,
)


BASE_URL = os.environ.get("TAXTREAT_LIVE_BASE_URL", "https://taxtreat.vercel.app").rstrip("/")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "live_browser_condition_matrix.json"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def value_equal(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) < 1e-9
    return left == right


def scenario_target(
    source_country: str,
    recipient_country: str,
    income_type: str,
    label: str,
    payload: dict[str, Any],
) -> tuple[str | None, Any]:
    if label == "baseline":
        return None, None

    if label.startswith("determination:"):
        return "__determination__", None

    baseline = base_payload(source_country, recipient_country, income_type)
    changed = [
        key
        for key, value in payload.get("facts", {}).items()
        if key not in baseline.get("facts", {})
        or not value_equal(value, baseline["facts"].get(key))
    ]

    # The explicit PE web-visible variant changes one public input, while the
    # browser intentionally derives the complementary PE facts itself.
    if label == "pe_connection_true":
        return "permanent_establishment_connection", True

    if len(changed) == 1:
        key = changed[0]
        return key, payload["facts"][key]

    common_targets = {
        "treaty_resident_false": "recipient_is_treaty_resident",
        "beneficial_owner_false": "beneficial_owner",
        "ownership_zero": "ownership_percent",
        "ownership_10": "ownership_percent",
        "ownership_25": "ownership_percent",
        "ownership_50": "ownership_percent",
        "direct_ownership_false": "direct_ownership",
        "holding_0m": "holding_period_months",
        "holding_12m": "holding_period_months",
        "holding_24m": "holding_period_months",
        "arm_length_false": "arm_length_amount",
        "related_party": "related_party_status",
    }
    if label in common_targets:
        key = common_targets[label]
        return key, payload["facts"].get(key)

    if label.startswith("royalty_category_"):
        return "royalty_category", payload["facts"].get("royalty_category")

    # Multiple changed factual values can be a deliberate derived bundle.
    # Such a scenario is still browser-exercised but not used as a single-fact
    # reachability assertion.
    return None, None


def browser_scenarios(
    *,
    source_country: str,
    income_type: str,
    shard_index: int,
    shard_count: int,
) -> list[dict[str, Any]]:
    inv = inventory()
    countries = [
        country
        for country in inv[source_country]["countries"]
        if hash(country) % shard_count == shard_index
    ]
    # Python hash randomization makes hash() unsuitable across workers.
    countries = [
        country
        for position, country in enumerate(inv[source_country]["countries"])
        if position % shard_count == shard_index
    ]

    result: list[dict[str, Any]] = []
    for recipient_country in countries:
        scope_conditions = inv[source_country]["conditions"].get(
            (recipient_country, income_type),
            set(),
        )
        scenarios, unsupported = scenario_payloads(
            source_country,
            recipient_country,
            income_type,
            scope_conditions,
        )
        if unsupported:
            raise AssertionError(
                f"unsupported structured condition in {source_country}/{recipient_country}/{income_type}: {unsupported}"
            )
        for label, payload in scenarios:
            target_fact, target_value = scenario_target(
                source_country,
                recipient_country,
                income_type,
                label,
                payload,
            )
            if target_fact == "__determination__":
                continue
            result.append(
                {
                    "source_country": source_country,
                    "recipient_country": recipient_country,
                    "income_type": income_type,
                    "label": label,
                    "payload": payload,
                    "target_fact": target_fact,
                    "target_value": target_value,
                }
            )
    return result


def source_partner_count(source_country: str) -> int:
    return 102 if source_country == "CZ" else 76


def bootstrap(page: Page, source_country: str, lang: str) -> None:
    page.goto(
        f"{BASE_URL}/ui/{lang}",
        wait_until="domcontentloaded",
        timeout=20_000,
    )
    page.wait_for_function(
        "() => Boolean(window.TaxTreatWorkspaceSourceCountry && window.TaxTreatSourceCountries)"
    )
    page.wait_for_timeout(1500)

    if source_country == "SK":
        page.locator('[data-nav="payers"]').click()
        page.locator("[data-create-payer]:visible").click()
        form = page.locator("#payer-form")
        form.locator('[name="payer_id"]').fill("12345679")
        form.locator('[name="payer_name"]').fill("Matrix SK s.r.o.")
        form.locator('[name="payer_vat_id"]').fill("SK2020000000")
        form.locator('[name="payer_country"]').select_option("SK")
        form.locator("[data-save-payer]").click()
        page.wait_for_function("() => document.body.dataset.sourceCountry === 'SK'")

    page.wait_for_function(
        """(expected) => document.querySelectorAll(
            '#new-recipient-form [name="recipient_country"] option'
        ).length === expected""",
        arg=source_partner_count(source_country),
    )
    check(
        page.evaluate("document.body.dataset.sourceCountry") == source_country,
        f"source-country bootstrap mismatch: {source_country}",
    )
    check(
        page.evaluate("document.documentElement.lang") == lang,
        f"language bootstrap mismatch: {lang}",
    )


def set_recipient_country(page: Page, recipient_country: str) -> None:
    page.locator('[data-nav="recipients"]:visible').first.click()
    page.locator('[data-view="recipients"] [data-open-recipient]').click()
    page.locator('[data-view="recipient-detail"] [data-edit-recipient]:visible').click()
    dialog = page.locator("#recipient-edit-form")
    dialog.locator('[name="recipient_country"]').select_option(recipient_country)
    dialog.locator('[name="recipient_type"]').select_option(label="Společnost")
    dialog.locator('[name="beneficial_owner"]').select_option("")
    dialog.locator('[name="treaty_resident"]').select_option("")
    dialog.locator('[name="pe_connection"]').select_option("")
    dialog.locator('button[type="submit"]').click()
    page.wait_for_function(
        "(code) => document.querySelector('#recipient-edit-form [name=recipient_country]').value === code",
        arg=recipient_country,
    )


def start_flow(page: Page) -> None:
    start = page.locator("[data-start-flow]:visible")
    if start.count() == 0:
        page.locator('[data-nav="dashboard"]:visible').first.click()
        page.wait_for_function(
            "() => Boolean(document.querySelector('[data-view=dashboard].active'))"
        )
        start = page.locator("[data-start-flow]:visible")
    check(start.count() > 0, "no visible New calculation control")
    start.first.click()
    page.locator('[data-next-step="2"]:visible').click()
    page.locator('[data-next-step="3"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"3\"].active'))"
    )


def date_for_holding_months(months: int | float) -> str:
    mapping = {
        0: "2026-09-02",
        12: "2025-09-02",
        24: "2024-09-02",
    }
    rounded = int(round(float(months)))
    return mapping.get(rounded, "2024-01-01")


def set_radio(form, name: str, value: bool) -> None:
    form.locator(f'[name="{name}"][value="{str(bool(value)).lower()}"]').check()


def set_section19(page: Page, desired_facts: dict[str, Any]) -> None:
    company = page.locator('#workspace-payment [name="section19_company_form"]')
    taxable = page.locator('#workspace-payment [name="section19_taxable_company"]')
    if company.count() and company.is_visible():
        company.select_option(
            "true"
            if desired_facts.get("recipient_is_qualifying_company_form", True)
            else "false"
        )
    if taxable.count() and taxable.is_visible():
        tax_value = desired_facts.get("recipient_subject_to_qualifying_corporate_tax", True)
        no_exemption = desired_facts.get("recipient_has_no_tax_exemption_or_zero_rate_option", True)
        taxable.select_option("true" if tax_value and no_exemption else "false")


def fill_primary_controls(page: Page, scenario: dict[str, Any]) -> None:
    payload = scenario["payload"]
    facts = payload["facts"]
    income_type = scenario["income_type"]
    form = page.locator("#workspace-payment")

    form.locator('[name="income_type"]').select_option(income_type)
    form.locator('[name="transaction_date"]').fill(payload["transaction_date"])
    form.locator('[name="amount"]').fill(str(payload["transaction_amount"]["amount"]))

    set_radio(form, "beneficial_owner", bool(facts.get("beneficial_owner", True)))
    set_radio(
        form,
        "treaty_resident",
        bool(facts.get("recipient_is_treaty_resident", True)),
    )
    set_radio(
        form,
        "pe_connection",
        bool(facts.get("permanent_establishment_connection", False)),
    )

    if income_type == "dividend":
        ownership = facts.get("ownership_percent", 100)
        form.locator('[name="ownership_percent"]').fill(str(ownership))
        page.wait_for_timeout(15)

        direct = bool(facts.get("direct_ownership", True))
        form.locator('[name="direct_ownership"]').select_option(
            "true" if direct else "false"
        )
        page.wait_for_timeout(15)

        months = facts.get("holding_period_months", 24)
        form.locator('[name="holding_period_mode"]').select_option("known_date")
        page.wait_for_timeout(15)
        form.locator('[name="acquisition_date"]').fill(date_for_holding_months(months))

        voting = facts.get(
            "voting_ownership",
            facts.get("direct_or_indirect_voting_ownership", ownership),
        )
        if form.locator('[name="voting_ownership_percent"]').is_visible():
            form.locator('[name="voting_ownership_percent"]').fill(str(voting))

        set_section19(page, facts)

    elif income_type == "interest":
        arm = form.locator('[name="arm_length_amount"]')
        if arm.count():
            arm.select_option(
                "true" if facts.get("arm_length_amount", True) else "false"
            )

    elif income_type == "royalty":
        royalty = form.locator('[name="royalty_category"]')
        if royalty.count():
            category = str(facts.get("royalty_category", "computer_software"))
            option_values = royalty.locator("option").evaluate_all(
                "(opts) => opts.map(o => o.value)"
            )
            if category in option_values:
                royalty.select_option(category)


def desired_for_path(payload: dict[str, Any], path: str) -> tuple[bool, Any]:
    if path.startswith("facts."):
        key = path[6:]
        if key in payload["facts"]:
            return True, payload["facts"][key]
    return False, None


def fill_question(input_node, payload: dict[str, Any]) -> None:
    path = input_node.get_attribute("data-input-path") or ""
    response_type = input_node.get_attribute("data-response-type") or ""
    has_desired, desired = desired_for_path(payload, path)

    if input_node.get_attribute("class") and "structured-answer" in (input_node.get_attribute("class") or ""):
        input_node.locator('[name="czk_per_unit"]').fill("25")
        return

    tag = input_node.evaluate("node => node.tagName")

    if tag == "SELECT":
        options = input_node.locator("option")
        values = [options.nth(i).get_attribute("value") or "" for i in range(options.count())]

        if response_type == "boolean_rule_value":
            if has_desired:
                true_value = json.loads(input_node.get_attribute("data-true-value") or "null")
                false_value = json.loads(input_node.get_attribute("data-false-value") or "null")
                if value_equal(desired, true_value):
                    input_node.select_option("__yes__")
                    return
                if value_equal(desired, false_value):
                    input_node.select_option("__no__")
                    return
            input_node.select_option("__yes__")
            return

        if response_type == "boolean":
            if has_desired:
                input_node.select_option("true" if bool(desired) else "false")
            else:
                input_node.select_option("true")
            return

        if has_desired and str(desired) in values:
            input_node.select_option(str(desired))
            return

        nonempty = [value for value in values if value]
        if nonempty:
            input_node.select_option(nonempty[0])
        return

    if response_type == "date":
        input_node.fill("2024-01-01")
    elif response_type in ("decimal_percent", "number"):
        input_node.fill(str(desired if has_desired else 25))
    else:
        input_node.fill(str(desired if has_desired else 25))


def finish_dynamic_questions(page: Page, payload: dict[str, Any]) -> None:
    for _ in range(12):
        if page.locator('.flow-step[data-step="4"].active').count():
            return
        if page.locator("#workspace-error").is_visible():
            raise AssertionError(
                "workspace error: " + page.locator("#workspace-error").inner_text().strip()
            )

        questions = page.locator("#workspace-questions [data-input-path]")
        count = questions.count()
        if count == 0:
            page.wait_for_timeout(50)
            continue

        for index in range(count):
            fill_question(questions.nth(index), payload)

        page.locator("#workspace-submit").click()
        page.wait_for_timeout(80)

    raise AssertionError("dynamic questions did not resolve")


def assert_target_reached(
    scenario: dict[str, Any],
    submitted: dict[str, Any],
) -> None:
    target_fact = scenario["target_fact"]
    if not target_fact:
        return
    facts = submitted.get("facts") or {}
    check(
        target_fact in facts,
        f"unreachable UI fact {target_fact} for {scenario['label']}",
    )
    check(
        value_equal(facts[target_fact], scenario["target_value"]),
        (
            f"UI fact mismatch {target_fact} for {scenario['label']}: "
            f"expected={scenario['target_value']!r} actual={facts[target_fact]!r}"
        ),
    )


def run_matrix(args: argparse.Namespace) -> dict[str, Any]:
    scenarios = browser_scenarios(
        source_country=args.source_country,
        income_type=args.income_type,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
    )

    if args.count_only:
        return {
            "pass": True,
            "count_only": True,
            "source_country": args.source_country,
            "income_type": args.income_type,
            "lang": args.lang,
            "shard_index": args.shard_index,
            "shard_count": args.shard_count,
            "scenarios": len(scenarios),
            "countries": len({item["recipient_country"] for item in scenarios}),
        }

    issues: list[dict[str, Any]] = []
    completed = 0
    captured: list[dict[str, Any]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1365, "height": 900})
        page.set_default_timeout(10_000)
        page.set_default_navigation_timeout(20_000)

        console_errors: list[str] = []
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error" and "favicon" not in message.text.lower()
            else None,
        )

        def record_request(request) -> None:
            if "/analysis/intake" in request.url and request.method == "POST":
                try:
                    captured.append(request.post_data_json)
                except Exception:
                    pass

        page.on("request", record_request)
        bootstrap(page, args.source_country, args.lang)

        current_country = None
        for index, scenario in enumerate(scenarios, 1):
            try:
                if scenario["recipient_country"] != current_country:
                    set_recipient_country(page, scenario["recipient_country"])
                    current_country = scenario["recipient_country"]

                start_flow(page)
                fill_primary_controls(page, scenario)

                before = len(captured)
                page.locator("#workspace-submit").click()
                page.wait_for_function(
                    """() => Boolean(
                        document.querySelector('.flow-step[data-step="4"].active') ||
                        !document.querySelector('#workspace-follow-up').hidden ||
                        !document.querySelector('#workspace-error').hidden
                    )"""
                )
                finish_dynamic_questions(page, scenario["payload"])

                check(
                    len(captured) > before,
                    "no /analysis/intake request captured",
                )
                submitted = captured[-1]
                check(
                    submitted.get("source_country") == args.source_country,
                    "source_country payload mismatch",
                )
                check(
                    submitted.get("recipient_country") == scenario["recipient_country"],
                    "recipient_country payload mismatch",
                )
                check(
                    submitted.get("income_type") == args.income_type,
                    "income_type payload mismatch",
                )
                assert_target_reached(scenario, submitted)

                completed += 1
                if index % 25 == 0 or index == len(scenarios):
                    print(
                        f"PROGRESS {index}/{len(scenarios)} "
                        f"{args.source_country}/{args.income_type}/{args.lang}/shard{args.shard_index}"
                    )
            except Exception as exc:
                issues.append(
                    {
                        "recipient_country": scenario["recipient_country"],
                        "scenario": scenario["label"],
                        "target_fact": scenario["target_fact"],
                        "error": repr(exc),
                    }
                )
                print(
                    f"FAIL {scenario['recipient_country']} {scenario['label']}: {exc!r}"
                )
                if len(issues) >= args.max_issues:
                    break

        if console_errors:
            issues.append(
                {
                    "kind": "console_errors",
                    "errors": console_errors[:20],
                }
            )

        browser.close()

    return {
        "pass": not issues and completed == len(scenarios),
        "count_only": False,
        "source_country": args.source_country,
        "income_type": args.income_type,
        "lang": args.lang,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "scenarios": len(scenarios),
        "completed": completed,
        "countries": len({item["recipient_country"] for item in scenarios}),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-country", choices=("CZ", "SK"), required=True)
    parser.add_argument("--income-type", choices=INCOME_TYPES, required=True)
    parser.add_argument("--lang", choices=("cs", "en"), required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--max-issues", type=int, default=10)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    check(0 <= args.shard_index < args.shard_count, "invalid shard")
    result = run_matrix(args)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({k: result[k] for k in result if k != "issues"}, sort_keys=True))
    if result.get("issues"):
        print(json.dumps(result["issues"], ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
