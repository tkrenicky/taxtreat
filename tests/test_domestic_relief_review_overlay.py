import csv
import json
import sys
from pathlib import Path

import pytest

from taxtreat.tools import add_domestic_relief_review_overlay as overlay_module
from taxtreat.tools.add_domestic_relief_review_overlay import (
    _income_overlay,
    _legal_basis_values,
    add_domestic_relief_overlay,
    write_review_csv,
)


def _pack():
    return {
        "schema_version": 2,
        "source_country": "AT",
        "status": "human_review_pack_not_reviewed_not_released",
        "policy": {"fail_closed": True},
        "rows": [
            {
                "source_country": "AT",
                "partner_label": "Partner",
                "income_type": income_type,
                "review_priority": "STANDARD",
                "candidate_rates_percent_machine": [5],
                "rate_branches_machine": [],
                "reviewer_decision": "not_reviewed",
                "reviewer_notes": None,
                "official_source_urls": ["https://example.invalid"],
                "review_ready": True,
                "review_blockers": [],
                "promotable_to_canonical": False,
            }
            for income_type in ("dividend", "interest", "royalty")
        ],
    }


def _model():
    return {
        "source_country": "AT",
        "status": "candidate_model_not_released",
        "income_types": {
            "dividend": {
                "base_domestic_layer": {
                    "candidate_treatment": "taxable_at_rate",
                    "candidate_rate_percent_for_corporate_recipient_from_2024": 23,
                    "legal_basis": ["§ 93 EStG"],
                },
                "eu_parent_relief": {
                    "candidate_treatment": "domestic_exemption",
                    "legal_basis": "§ 94 Z 2 EStG",
                    "minimum_participation_percent": 10,
                    "minimum_holding_period_months": 12,
                },
            },
            "interest": {
                "base_domestic_layer": {
                    "corporate_recipient_current_treatment_candidate": "outside_limited_tax_liability",
                    "corporate_recipient_candidate_rate_percent": 0,
                    "legal_basis": ["§ 98 EStG"],
                },
            },
            "royalty": {
                "base_domestic_layer": {
                    "candidate_treatment": "taxable_at_rate",
                    "candidate_rate_percent": 20,
                    "legal_basis": ["§ 99 EStG", "§ 100 EStG"],
                },
                "eu_interest_royalty_relief": {
                    "candidate_treatment": "domestic_exemption",
                    "legal_basis": "§ 99a EStG",
                    "beneficial_owner_required": True,
                    "minimum_direct_participation_percent": 25,
                    "minimum_holding_period_months": 12,
                    "confirmations_must_be_available_at_payment_for_source_relief": True,
                    "refund_route_if_holding_period_or_confirmation_missing_at_payment": True,
                },
            },
        },
    }


def test_overlay_adds_separate_substantive_collection_and_refund_review_fields():
    result = add_domestic_relief_overlay(_pack(), _model())
    assert result["schema_version"] == 4
    assert result["status"] == "human_review_pack_with_separate_domestic_review_not_reviewed_not_released"
    assert result["policy"]["substantive_treatment_is_separate_from_withholding_due_at_payment"] is True
    assert result["policy"]["refund_eligibility_is_separate_from_relief_at_source"] is True
    assert result["policy"]["treaty_rate_must_not_be_assumed_to_equal_payment_date_withholding"] is True
    dividend = result["rows"][0]
    assert dividend["domestic_baseline_rate_percent_candidate"] == 23
    assert "§ 94 Z 2 EStG" in dividend["domestic_relief_legal_basis"]
    assert dividend["domestic_reviewer_substantive_treatment"] is None
    assert dividend["domestic_reviewer_withholding_rate_now_percent"] is None
    assert dividend["domestic_reviewer_refund_eligibility"] is None
    assert dividend["promotable_to_canonical"] is False


def test_overlay_carries_current_interest_zero_and_royalty_twenty_as_distinct_baselines():
    result = add_domestic_relief_overlay(_pack(), _model())
    by_income = {row["income_type"]: row for row in result["rows"]}
    assert by_income["interest"]["domestic_baseline_treatment_candidate"] == "outside_limited_tax_liability"
    assert by_income["interest"]["domestic_baseline_rate_percent_candidate"] == 0
    assert by_income["royalty"]["domestic_baseline_rate_percent_candidate"] == 20
    royalty_paths = {row["path_id"]: row for row in by_income["royalty"]["domestic_relief_paths_candidate"]}
    assert royalty_paths["eu_interest_royalty_relief"]["minimum_direct_participation_percent"] == 25
    assert royalty_paths["eu_interest_royalty_relief"]["beneficial_owner_required"] is True


def test_overlay_csv_surfaces_new_fields_for_excel_review(tmp_path: Path):
    result = add_domestic_relief_overlay(_pack(), _model())
    path = tmp_path / "review.csv"
    write_review_csv(result, path)
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    assert len(rows) == 3
    assert "domestic_reviewer_withholding_rate_now_percent" in rows[0]
    assert "domestic_reviewer_relief_mechanism" in rows[0]
    assert "domestic_reviewer_refund_eligibility" in rows[0]
    assert json.loads(rows[0]["domestic_relief_paths_candidate"])[0]["path_id"] == "eu_parent_relief"


def test_overlay_rejects_country_mismatch_or_released_input():
    model = _model()
    model["source_country"] = "SK"
    with pytest.raises(ValueError, match="source countries differ"):
        add_domestic_relief_overlay(_pack(), model)

    model = _model()
    model["status"] = "released"
    with pytest.raises(ValueError, match="unreleased candidate model"):
        add_domestic_relief_overlay(_pack(), model)

    pack = _pack()
    pack["status"] = "released"
    with pytest.raises(ValueError, match="unreleased human-review pack"):
        add_domestic_relief_overlay(pack, _model())


def test_overlay_helper_normalizes_legal_basis_values_and_missing_income():
    assert _legal_basis_values(None) == []
    assert _legal_basis_values("§ 99a EStG") == ["§ 99a EStG"]
    assert _legal_basis_values(["§ 99 EStG", 100]) == ["§ 99 EStG", "100"]
    with pytest.raises(ValueError, match="missing income type"):
        _income_overlay("dividend", {"income_types": {}})


def test_overlay_ignores_non_dict_relief_entries_and_uses_empty_legal_basis():
    model = _model()
    model["income_types"]["dividend"]["note"] = "not a relief mapping"
    model["income_types"]["dividend"]["eu_parent_relief"]["legal_basis"] = None
    overlay = _income_overlay("dividend", model)
    assert [item["path_id"] for item in overlay["domestic_relief_paths_candidate"]] == ["eu_parent_relief"]
    assert overlay["domestic_relief_paths_candidate"][0]["legal_basis"] == []


def test_overlay_csv_rejects_empty_rows(tmp_path: Path):
    with pytest.raises(ValueError, match="no rows"):
        write_review_csv({"rows": []}, tmp_path / "empty.csv")


def test_overlay_cli_writes_json_and_csv(tmp_path: Path, monkeypatch, capsys):
    review_path = tmp_path / "pack.json"
    model_path = tmp_path / "model.json"
    output_json = tmp_path / "out" / "review.json"
    output_csv = tmp_path / "out" / "review.csv"
    review_path.write_text(json.dumps(_pack()), encoding="utf-8")
    model_path.write_text(json.dumps(_model()), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "add_domestic_relief_review_overlay",
            "--review-pack", str(review_path),
            "--domestic-model", str(model_path),
            "--output-json", str(output_json),
            "--output-csv", str(output_csv),
        ],
    )
    overlay_module.main()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["status"] == "human_review_pack_with_separate_domestic_review_not_reviewed_not_released"
    assert output_csv.exists()
    assert "Domestic relief review overlay: AT 3 scopes" in capsys.readouterr().out
