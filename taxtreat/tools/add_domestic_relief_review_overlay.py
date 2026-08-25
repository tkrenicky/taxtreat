from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _legal_basis_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _income_overlay(income_type: str, model: dict[str, Any]) -> dict[str, Any]:
    income = (model.get("income_types") or {}).get(income_type)
    if not isinstance(income, dict):
        raise ValueError(f"Domestic relief model missing income type: {income_type}")

    base = income.get("base_domestic_layer") or {}
    relief_paths: list[dict[str, Any]] = []
    legal_basis = _legal_basis_values(base.get("legal_basis"))

    for key, value in income.items():
        if key == "base_domestic_layer" or not isinstance(value, dict):
            continue
        basis = _legal_basis_values(value.get("legal_basis"))
        legal_basis.extend(basis)
        relief_paths.append({
            "path_id": key,
            "candidate_treatment": value.get("candidate_treatment"),
            "legal_basis": basis,
            "source_relief_state": value.get("source_relief_state"),
            "minimum_participation_percent": value.get("minimum_participation_percent"),
            "minimum_direct_participation_percent": value.get("minimum_direct_participation_percent"),
            "common_parent_direct_participation_alternative_percent": value.get("common_parent_direct_participation_alternative_percent"),
            "minimum_holding_period_months": value.get("minimum_holding_period_months"),
            "beneficial_owner_required": value.get("beneficial_owner_required"),
            "confirmations_must_be_available_at_payment_for_source_relief": value.get("confirmations_must_be_available_at_payment_for_source_relief"),
            "refund_route_if_holding_period_or_confirmation_missing_at_payment": value.get("refund_route_if_holding_period_or_confirmation_missing_at_payment"),
            "must_never_be_represented_as_relief_at_source": value.get("must_never_be_represented_as_relief_at_source"),
        })

    baseline_rate = base.get("candidate_rate_percent")
    if baseline_rate is None:
        baseline_rate = base.get("candidate_rate_percent_for_corporate_recipient_from_2024")
    if baseline_rate is None:
        baseline_rate = base.get("corporate_recipient_candidate_rate_percent")

    baseline_treatment = base.get("candidate_treatment")
    if baseline_treatment is None:
        baseline_treatment = base.get("corporate_recipient_current_treatment_candidate")

    return {
        "domestic_baseline_treatment_candidate": baseline_treatment,
        "domestic_baseline_rate_percent_candidate": baseline_rate,
        "domestic_relief_paths_candidate": relief_paths,
        "domestic_relief_legal_basis": sorted(set(legal_basis)),
        "domestic_relief_review_required": True,
        "reviewer_substantive_treatment": None,
        "reviewer_withholding_rate_now_percent": None,
        "reviewer_relief_mechanism": None,
        "reviewer_refund_eligibility": None,
        "reviewer_documentary_readiness": None,
        "reviewer_domestic_relief_facts_confirmed": None,
        "reviewer_domestic_relief_notes": None,
    }


def add_domestic_relief_overlay(
    review_pack: dict[str, Any],
    domestic_model: dict[str, Any],
) -> dict[str, Any]:
    source_country = str(review_pack.get("source_country") or "").upper()
    if source_country != str(domestic_model.get("source_country") or "").upper():
        raise ValueError("Review pack and domestic relief model source countries differ")
    if domestic_model.get("status") != "candidate_model_not_released":
        raise ValueError("Domestic relief overlay requires an unreleased candidate model")
    if review_pack.get("status") != "human_review_pack_not_reviewed_not_released":
        raise ValueError("Domestic relief overlay requires an unreleased human-review pack")

    rows: list[dict[str, Any]] = []
    for original in review_pack.get("rows", []):
        row = dict(original)
        income_type = str(row.get("income_type") or "")
        row.update(_income_overlay(income_type, domestic_model))
        row["promotable_to_canonical"] = False
        rows.append(row)

    result = dict(review_pack)
    result["schema_version"] = max(int(review_pack.get("schema_version") or 0), 3)
    result["status"] = "human_review_pack_with_domestic_relief_not_reviewed_not_released"
    result["rows"] = rows
    policy = dict(review_pack.get("policy") or {})
    policy.update({
        "domestic_precedence_must_be_reviewed_before_treaty_promotion": True,
        "substantive_treatment_is_separate_from_withholding_due_at_payment": True,
        "refund_eligibility_is_separate_from_relief_at_source": True,
        "treaty_rate_must_not_be_assumed_to_equal_payment_date_withholding": True,
        "reviewer_domestic_relief_fields_start_blank": True,
        "fail_closed": True,
    })
    result["policy"] = policy
    return result


def write_review_csv(pack: dict[str, Any], path: Path) -> None:
    if not pack.get("rows"):
        raise ValueError("Review pack contains no rows")
    preferred = [
        "source_country", "partner_label", "income_type", "review_priority",
        "domestic_baseline_treatment_candidate", "domestic_baseline_rate_percent_candidate",
        "domestic_relief_legal_basis", "domestic_relief_paths_candidate",
        "candidate_rates_percent_machine", "rate_branches_machine",
        "reviewer_substantive_treatment", "reviewer_withholding_rate_now_percent",
        "reviewer_relief_mechanism", "reviewer_refund_eligibility",
        "reviewer_documentary_readiness", "reviewer_domestic_relief_facts_confirmed",
        "reviewer_domestic_relief_notes", "reviewer_decision", "reviewer_notes",
        "official_source_urls", "review_ready", "review_blockers", "promotable_to_canonical",
    ]
    all_fields = {key for row in pack["rows"] for key in row}
    fields = [field for field in preferred if field in all_fields]
    fields.extend(sorted(all_fields - set(fields)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in pack["rows"]:
            output = dict(row)
            for key, value in list(output.items()):
                if isinstance(value, (list, dict)):
                    output[key] = json.dumps(value, ensure_ascii=False)
            writer.writerow({field: output.get(field) for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-pack", type=Path, required=True)
    parser.add_argument("--domestic-model", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    review_pack = json.loads(args.review_pack.read_text(encoding="utf-8"))
    domestic_model = json.loads(args.domestic_model.read_text(encoding="utf-8"))
    result = add_domestic_relief_overlay(review_pack, domestic_model)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review_csv(result, args.output_csv)
    print("Domestic relief review overlay:", result["source_country"], len(result["rows"]), "scopes")


if __name__ == "__main__":
    main()
