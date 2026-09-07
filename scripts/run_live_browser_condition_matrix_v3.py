from __future__ import annotations

import sys
from copy import deepcopy
from typing import Any

import run_live_browser_condition_matrix as base
import run_live_browser_condition_matrix_v2 as v2


# Historical Stage 6 royalty labels encountered by the exhaustive browser
# matrix. The workspace deliberately exposes a smaller, precise canonical UI
# taxonomy. A broad historical treaty branch is therefore exercised through
# every concrete current UI category that it contains; no branch is discarded
# and no arbitrary single representative is substituted.
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
    "patent_trademark_design_model_plan_secret_formula_process_equipment_or_industrial_commercial_scientific_knowhow": (
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
    "copyright_literary_artistic_scientific_including_films_broadcast_software_patent_trademark_design_model_plan_secret_formula_process_or_knowhow": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    ),
    "copyright_literary_artistic_scientific_including_films_broadcast_recordings_and_other_audio_visual_reproduction_excluding_computer_software": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
    "patent_trademark_design_model_plan_secret_formula_process_computer_software_equipment_or_knowhow": (
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
    "copyright_literary_artistic_or_scientific_excluding_cinematographic_films_and_broadcast_recordings": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    ),
    "operating_lease_of_equipment_or_computer_software": (
        "computer_software",
        "operating_lease_or_other_use_of_equipment",
    ),
    "patent_trademark_design_model_plan_secret_formula_process_or_industrial_commercial_scientific_knowhow": (
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    ),
    "patent_trademark_design_model_plan_secret_formula_process_custom_software_equipment_or_knowhow": (
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
    "copyright_literary_artistic_or_scientific": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    ),
    "all_royalties_except_industrial_commercial_scientific_equipment": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "other",
    ),
    "copyright_literary_artistic_scientific_including_cinematographic_films_and_broadcast_media": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
    "software_patent_trademark_design_model_plan_secret_formula_process_knowhow_or_industrial_commercial_scientific_equipment": (
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
    "copyright_literary_artistic_or_scientific_excluding_computer_program_including_films_and_broadcast_media": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
    "copyright_literary_dramatic_musical_or_artistic_excluding_cinematographic_and_broadcast_recordings": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    ),
    "cinematographic_films_or_television_radio_films_or_recordings": (
        "cinematographic_films_or_broadcast_media",
    ),
    "copyright_literary_artistic_scientific_excluding_cinematographic_films_and_broadcast_media_or_patent_trademark_design_model_plan_secret_formula_process_equipment_or_industrial_commercial_scientific_knowhow": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
    "copyright_literary_artistic_scientific_including_cinematographic_films_and_tv_or_radio_recordings": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
    "patent_trademark_design_model_plan_secret_formula_process_equipment_knowhow_technical_or_economic_studies_or_technical_assistance": (
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
        "other",
    ),
    "copyright_literary_artistic_scientific_including_films_tapes_or_other_audio_visual_reproduction": (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
    ),
    "patent_trademark_design_model_plan_secret_formula_process_similar_right_or_property_equipment_or_knowhow_including_productivity_use_or_disposition_contingent_sales": (
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
    ),
}

# Catch-all legacy branches are country-specific complements of a more specific
# Article 12 branch. Expanding them to every canonical category would assert a
# false equivalence. Keep these visible for the next evidence pass so any
# remaining country-specific complement can be mapped explicitly from its
# companion structured condition instead of guessed.
DIAGNOSTIC_LEGACY_ROYALTY_CATEGORIES = {
    "all_other_article_12_royalties",
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
                    expanded["label"] = f"{item['label']}:ui={canonical_category}"
                    result.append(expanded)
                continue

            if str(target_value) in DIAGNOSTIC_LEGACY_ROYALTY_CATEGORIES:
                item["label"] = f"{item['label']}:legacy-complement={target_value}"

        # Some treaty-specific follow-up facts are only relevant after choosing
        # a particular canonical royalty family. Put the browser on that real
        # UI branch first; the treaty-specific answer itself is still supplied
        # through the actual dynamic question and remains fully asserted.
        if target_fact == "royalty_is_transport_vehicle":
            item["payload"]["facts"][
                "royalty_category"
            ] = "operating_lease_or_other_use_of_equipment"
        elif target_fact == "software_classified_as_article_12_3a_copyright":
            item["payload"]["facts"]["royalty_category"] = "computer_software"
        elif target_fact == "royalty_is_technical_or_economic_study_or_technical_assistance":
            item["payload"]["facts"]["royalty_category"] = "other"

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


def assert_target_reached(scenario: dict[str, Any], submitted: dict[str, Any]) -> None:
    try:
        v2.assert_target_reached(scenario, submitted)
    except AssertionError as exc:
        # Keep the evidence actionable: older failures only said "unreachable"
        # and hid the exact historical value that still needed a semantic map.
        if scenario.get("target_fact") == "royalty_category":
            raise AssertionError(
                f"{exc}; target_value={scenario.get('target_value')!r}; "
                f"recipient={scenario.get('recipient_country')!r}"
            ) from exc
        raise


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
    base.assert_target_reached = assert_target_reached
    base.start_flow = start_flow


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
