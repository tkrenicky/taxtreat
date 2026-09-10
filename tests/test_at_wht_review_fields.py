import csv
import json
from pathlib import Path

import pytest

from taxtreat.tools.add_at_wht_review_fields import add_at_wht_review_fields, write_csv


def _pack():
    return {
        "schema_version": 3,
        "source_country": "AT",
        "status": "human_review_pack_with_domestic_relief_not_reviewed_not_released",
        "policy": {"fail_closed": True},
        "rows": [
            {
                "partner_label": "Schweiz / Switzerland",
                "income_type": "royalty",
                "review_priority": "HIGH",
                "reviewer_decision": "not_reviewed",
                "reviewer_notes": None,
                "official_source_urls": ["https://www.ris.bka.gv.at/"],
                "review_ready": True,
                "review_blockers": [],
                "promotable_to_canonical": False,
            },
            {
                "partner_label": "Deutschland / Germany",
                "income_type": "dividend",
                "review_priority": "STANDARD",
                "reviewer_decision": "not_reviewed",
                "reviewer_notes": None,
                "official_source_urls": ["https://www.ris.bka.gv.at/"],
                "review_ready": True,
                "review_blockers": [],
                "promotable_to_canonical": False,
            },
        ],
    }


def test_at_review_fields_force_payment_date_rate_and_tax_base_review():
    result = add_at_wht_review_fields(_pack())
    assert result["schema_version"] == 4
    assert result["status"] == "at_wht_human_review_pack_not_reviewed_not_released"
    assert result["policy"]["reviewer_must_confirm_payment_date_withholding_not_only_treaty_rate"] is True
    assert result["policy"]["reviewer_must_confirm_withholding_base_for_royalties"] is True
    assert result["policy"]["current_section99_expense_security_threshold_eur"] == 2463.0
    royalty = result["rows"][0]
    assert royalty["reviewer_withholding_base"] is None
    assert royalty["reviewer_payment_date_wht_rate_percent"] is None
    assert royalty["reviewer_selected_legal_route"] is None
    assert royalty["promotable_to_canonical"] is False


def test_at_royalty_review_shows_gross_20_and_corporate_net_23_as_different_bases():
    royalty = add_at_wht_review_fields(_pack())["rows"][0]
    candidates = {row["route"]: row for row in royalty["royalty_collection_candidates"]}
    gross = candidates["section_99_gross_basis"]
    net = candidates["section_99_net_expense_basis_corporate"]
    assert gross["rate_percent_candidate"] == 20.0
    assert gross["withholding_base"] == "gross_revenue"
    assert net["rate_percent_candidate"] == 23.0
    assert net["withholding_base"] == "net_revenue_after_admissible_direct_expenses"
    assert net["expense_security_threshold_eur"] == 2463.0


def test_at_swiss_rows_require_special_agreement_vs_dtt_review_only_for_switzerland():
    rows = add_at_wht_review_fields(_pack())["rows"]
    swiss, germany = rows
    assert swiss["swiss_article9_review_required"] is True
    assert swiss["reviewer_eu_swiss_article9_eligible"] is None
    assert swiss["reviewer_dtt_more_favourable_than_special_agreement"] is None
    assert germany["swiss_article9_review_required"] is False
    assert germany["reviewer_eu_swiss_article9_eligible"] is False


def test_at_review_csv_contains_new_excel_columns(tmp_path: Path):
    result = add_at_wht_review_fields(_pack())
    path = tmp_path / "at-review.csv"
    write_csv(result, path)
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    assert len(rows) == 2
    assert "reviewer_withholding_base" in rows[0]
    assert "reviewer_payment_date_wht_rate_percent" in rows[0]
    assert "reviewer_eu_swiss_article9_eligible" in rows[0]
    candidates = json.loads(rows[0]["royalty_collection_candidates"])
    assert candidates[1]["rate_percent_candidate"] == 23.0


def test_at_review_fields_fail_closed_on_wrong_country_or_released_pack():
    wrong = _pack()
    wrong["source_country"] = "SK"
    with pytest.raises(ValueError, match="Austrian"):
        add_at_wht_review_fields(wrong)

    released = _pack()
    released["status"] = "released"
    with pytest.raises(ValueError, match="unreleased"):
        add_at_wht_review_fields(released)
