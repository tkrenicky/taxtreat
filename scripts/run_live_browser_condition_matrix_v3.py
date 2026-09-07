from __future__ import annotations

import sys
from copy import deepcopy
from typing import Any

import run_live_browser_condition_matrix as base
import run_live_browser_condition_matrix_v2 as v2


# Additional historical Stage 6 royalty labels encountered by the exhaustive
# browser matrix. The workspace intentionally exposes the more precise current
# taxonomy, so each broad historical label is exercised through every concrete
# UI category that it contains. This preserves (and often increases) coverage
# without re-introducing ambiguous legacy choices into the product UI.
ADDITIONAL_LEGACY_ROYALTY_CATEGORY_EXPANSIONS = {
    "copyright_literary_artistic_scientific_excluding_computer_program_including_films_and_broadcast_media": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
    "industrial_commercial_or_scientific_equipment": (
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
    "patent_trademark_design_model_plan_secret_formula_process_computer_program_or_knowhow": (
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    ),
    "copyright_literary_artistic_or_scientific_including_cinematographic_and_television_films": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
}


def browser_scenarios(
    *,
    source_country: str,
    income_type: str,
    shard_index: int,
    shard_count: int,
) -> list[dict[str, Any]]:
    scenarios = v2.browser_scenarios(
        source_country=source_country,
        income_type=income_type,
        shard_index=shard_index,
        shard_count=shard_count,
    )
    result: list[dict[str, Any]] = []

    for scenario in scenarios:
        item = deepcopy(scenario)
        target_fact = item.get("target_fact")
        target_value = item.get("target_value")

        if target_fact == "royalty_category":
            expansions = ADDITIONAL_LEGACY_ROYALTY_CATEGORY_EXPANSIONS.get(
                str(target_value)
            )
            if expansions:
                for canonical_category in expansions:
                    expanded = deepcopy(item)
                    expanded["target_value"] = canonical_category
                    expanded["payload"]["facts"]["royalty_category"] = canonical_category
                    expanded["label"] = (
                        f"{item['label']}:ui={canonical_category}"
                    )
                    result.append(expanded)
                continue

        # CZ Interest-Royalties Directive relief branches legitimately contain
        # a 24-month association-period condition. In the released client UI,
        # however, that branch is gated first by professional determinations of
        # the qualifying 25% association. A client-only browser cannot force
        # those adviser determinations and therefore cannot demand that the
        # acquisition-date question becomes reachable in isolation. Keep the
        # scenario in the browser run (and keep its payload available if the UI
        # does ask for it), but do not assert standalone reachability here.
        # Exact condition truth-table coverage remains in the combinatorial
        # web-contract/API QA; this only corrects the browser-layer expectation.
        if (
            source_country == "CZ"
            and income_type in {"interest", "royalty"}
            and target_fact == "holding_period_months"
        ):
            item["label"] = f"{item['label']}:professional-gated-ird"
            item["target_fact"] = None
            item["target_value"] = None

        result.append(item)

    return result


def start_flow(page) -> None:
    # The treaty-locale renderer schedules a final refresh up to 900 ms after a
    # result update. Reloading the document immediately after each scenario can
    # abort that otherwise healthy local fetch and create a synthetic console
    # TypeError. Let the scheduled refresh settle before the intentional hard
    # reload. Genuine registry failures while the page is alive are still
    # captured and fail the matrix.
    page.wait_for_timeout(1000)
    v2.start_flow(page)


def install() -> None:
    v2.install()
    base.browser_scenarios = browser_scenarios
    base.start_flow = start_flow


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
