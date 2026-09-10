from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from pathlib import Path
from typing import Any


SUPPORTED_STATUSES = {
    "human_review_pack_not_reviewed_not_released",
    "human_review_pack_with_domestic_relief_not_reviewed_not_released",
}


def _searchable(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).casefold()


def _is_swiss_partner(label: str) -> bool:
    text = _searchable(label)
    return "schweiz" in text or "switzerland" in text


def _royalty_collection_candidates() -> list[dict[str, Any]]:
    return [
        {
            "route": "section_99_gross_basis",
            "withholding_base": "gross_revenue",
            "rate_percent_candidate": 20.0,
            "legal_basis": "§ 99 Abs. 2 Z 1 / § 100 Abs. 1 EStG 1988",
        },
        {
            "route": "section_99_net_expense_basis_corporate",
            "withholding_base": "net_revenue_after_admissible_direct_expenses",
            "rate_percent_candidate": 23.0,
            "legal_basis": "§ 99 Abs. 2 Z 2 / § 100 Abs. 1a Z 1 EStG 1988",
            "conditions": [
                "recipient is EU/EEA limited taxpayer",
                "directly related expenses disclosed in writing before payment",
                "section 99 expense-payee taxation security test satisfied where applicable",
            ],
            "expense_security_threshold_eur": 2463.0,
        },
    ]


def add_at_wht_review_fields(pack: dict[str, Any]) -> dict[str, Any]:
    if str(pack.get("source_country") or "").upper() != "AT":
        raise ValueError("AT WHT review fields require an Austrian review pack")
    if pack.get("status") not in SUPPORTED_STATUSES:
        raise ValueError("AT WHT review fields require an unreleased review pack")

    rows: list[dict[str, Any]] = []
    for original in pack.get("rows", []):
        row = dict(original)
        income_type = str(row.get("income_type") or "")
        swiss = _is_swiss_partner(str(row.get("partner_label") or ""))
        royalty = income_type == "royalty"

        row.update({
            "payment_date_wht_review_required": True,
            "reviewer_selected_legal_route": None,
            "reviewer_withholding_base": None,
            "reviewer_payment_date_wht_rate_percent": None,
            "reviewer_relief_at_source_available": None,
            "reviewer_refund_route_available": None,
            "reviewer_required_form_or_documentation": None,
            "reviewer_procedure_notes": None,
            "reviewer_refund_prenotification_required": None,
            "reviewer_refund_competent_authority": None,
            "reviewer_refund_period_confirmed": None,
            "swiss_article9_review_required": swiss,
            "reviewer_eu_swiss_article9_eligible": None if swiss else False,
            "reviewer_dtt_more_favourable_than_special_agreement": None if swiss else False,
            "reviewer_special_international_relief_notes": None,
            "royalty_collection_candidates": _royalty_collection_candidates() if royalty else [],
            "reviewer_expense_deduction_option_elected": None if royalty else False,
            "reviewer_expense_deduction_conditions_confirmed": None if royalty else False,
            "reviewer_net_expense_amount": None,
            "reviewer_section99_expense_security_test_confirmed": None if royalty else False,
            "reviewer_recipient_has_austrian_pe": None if royalty else False,
            "reviewer_royalty_attributable_to_austrian_pe": None if royalty else False,
            "reviewer_assessment_character": None if royalty else "not_applicable",
            "reviewer_withholding_creditable_in_assessment": None if royalty else False,
            "promotable_to_canonical": False,
        })
        rows.append(row)

    result = dict(pack)
    result["schema_version"] = max(int(pack.get("schema_version") or 0), 4)
    result["status"] = "at_wht_human_review_pack_not_reviewed_not_released"
    result["rows"] = rows
    policy = dict(pack.get("policy") or {})
    policy.update({
        "reviewer_must_confirm_payment_date_withholding_not_only_treaty_rate": True,
        "reviewer_must_confirm_withholding_base_for_royalties": True,
        "gross_and_net_royalty_rates_are_not_comparable_without_tax_base": True,
        "royalty_pe_attribution_changes_assessment_character_not_automatically_payment_date_rate": True,
        "refund_filing_procedure_is_separate_from_refund_substantive_entitlement": True,
        "swiss_article9_and_dtt_must_be_compared_where_applicable": True,
        "current_section99_expense_security_threshold_eur": 2463.0,
        "corporate_net_expense_wht_rate_from_2024_percent": 23.0,
        "future_faster_rules_must_not_affect_2026_review": True,
        "all_new_reviewer_fields_start_unreviewed": True,
        "fail_closed": True,
    })
    result["policy"] = policy
    return result


def write_csv(pack: dict[str, Any], path: Path) -> None:
    rows = pack.get("rows") or []
    if not rows:
        raise ValueError("AT review pack contains no rows")
    preferred = [
        "partner_label", "income_type", "review_priority",
        "domestic_baseline_treatment_candidate", "domestic_baseline_rate_percent_candidate",
        "candidate_rates_percent_machine", "reviewer_selected_legal_route",
        "reviewer_withholding_base", "reviewer_payment_date_wht_rate_percent",
        "reviewer_relief_at_source_available", "reviewer_refund_route_available",
        "reviewer_required_form_or_documentation", "reviewer_procedure_notes",
        "reviewer_refund_prenotification_required", "reviewer_refund_competent_authority",
        "reviewer_refund_period_confirmed",
        "royalty_collection_candidates", "reviewer_expense_deduction_option_elected",
        "reviewer_expense_deduction_conditions_confirmed", "reviewer_net_expense_amount",
        "reviewer_section99_expense_security_test_confirmed",
        "reviewer_recipient_has_austrian_pe", "reviewer_royalty_attributable_to_austrian_pe",
        "reviewer_assessment_character", "reviewer_withholding_creditable_in_assessment",
        "swiss_article9_review_required", "reviewer_eu_swiss_article9_eligible",
        "reviewer_dtt_more_favourable_than_special_agreement",
        "reviewer_special_international_relief_notes", "reviewer_decision",
        "reviewer_notes", "official_source_urls", "review_ready", "review_blockers",
        "promotable_to_canonical",
    ]
    fields_all = {key for row in rows for key in row}
    fields = [field for field in preferred if field in fields_all]
    fields.extend(sorted(fields_all - set(fields)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            output = dict(row)
            for key, value in list(output.items()):
                if isinstance(value, (dict, list)):
                    output[key] = json.dumps(value, ensure_ascii=False)
            writer.writerow({field: output.get(field) for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-pack", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()
    pack = json.loads(args.review_pack.read_text(encoding="utf-8"))
    result = add_at_wht_review_fields(pack)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(result, args.output_csv)
    print("AT WHT review fields:", len(result["rows"]), "scopes")


if __name__ == "__main__":
    main()
