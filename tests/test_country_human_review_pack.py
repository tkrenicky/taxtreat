from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

from taxtreat.tools import build_country_human_review_pack as review_module
from taxtreat.tools.build_country_human_review_pack import build_human_review_pack, write_csv


def _queue() -> dict:
    scopes = []
    for index in range(2):
        for income_type in ("dividend", "interest", "royalty"):
            scopes.append({
                "source_country": "AT",
                "partner_label": f"Partner {index}",
                "income_type": income_type,
                "machine_mli_flag": index == 0,
                "machine_status_instrument_flag": False,
                "instrument_chain": {"official_links": [f"https://ris.bka.gv.at/{index}/{income_type}"]},
            })
    return {
        "source_country": "AT",
        "status": "review_queue_not_released",
        "scopes": scopes,
    }


def _scope_evidence() -> dict:
    scopes = []
    for index in range(2):
        for income_type in ("dividend", "interest", "royalty"):
            scopes.append({
                "partner_label": f"Partner {index}",
                "income_type": income_type,
                "rate_branches_machine": [{
                    "rate_percent": 10.0,
                    "treatment_candidate": None,
                    "condition_evidence_text": "Beneficial owner condition from the operative treaty branch.",
                    "source_url": f"https://ris.bka.gv.at/{index}/{income_type}",
                    "beneficial_owner_required_machine": True,
                    "ownership_threshold_percent_machine": 25.0 if income_type == "dividend" else None,
                    "holding_period_value_machine": 365 if income_type == "dividend" else None,
                    "holding_period_unit_machine": "days" if income_type == "dividend" else None,
                    "category_discriminator_machine": "software" if income_type == "royalty" else None,
                    "pe_carveout_machine": True,
                }],
            })
    return {"scopes": scopes}


def test_human_review_pack_prioritizes_machine_risk_and_variant_review():
    audit = {
        "partners": [{
            "partner_label": "Partner 0",
            "machine_risk_reasons": ["multiple_rate_candidates_after_condition_filter"],
            "rate_candidates_machine": [5.0, 10.0],
            "ownership_threshold_tokens_machine": [],
            "royalty_article_numbers_machine": [12],
        }]
    }
    reconciliation = {
        "partners": [{
            "partner_label": "Partner 1",
            "articles": [
                {"article_number": 10, "unique_text_variant_count": 2},
                {"article_number": 11, "unique_text_variant_count": 1},
                {"article_number": 12, "unique_text_variant_count": 1},
            ],
        }]
    }
    pack = build_human_review_pack(
        _queue(),
        royalty_audit=audit,
        article_reconciliation=reconciliation,
        scope_evidence=_scope_evidence(),
    )
    assert pack["scope_count"] == 6
    assert pack["review_ready_scope_count"] == 6
    assert pack["blocked_scope_count"] == 0
    assert pack["high_priority_scope_count"] == 1
    assert pack["medium_priority_scope_count"] == 1
    assert pack["policy"]["machine_output_is_not_legal_approval"] is True
    assert pack["policy"]["canonical_materialization_requires_approved_review"] is True
    assert pack["policy"]["review_ready_requires_complete_rate_to_condition_mapping"] is True
    assert all(row["promotable_to_canonical"] is False for row in pack["rows"])
    high = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0" and row["income_type"] == "royalty")
    assert high["review_priority"] == "HIGH"
    assert high["candidate_rates_percent_machine"] == [10.0]
    assert high["conditions_complete_machine"] is True


def test_human_review_pack_preserves_condition_dimensions_instead_of_flattening_them():
    pack = build_human_review_pack(_queue(), scope_evidence=_scope_evidence())
    dividend = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0" and row["income_type"] == "dividend")
    branch = dividend["rate_branches_machine"][0]
    assert branch["beneficial_owner_required_machine"] is True
    assert branch["ownership_threshold_percent_machine"] == 25.0
    assert branch["holding_period_value_machine"] == 365
    assert branch["holding_period_unit_machine"] == "days"
    assert branch["pe_carveout_machine"] is True


def test_human_review_pack_propagates_language_evidence_without_unlocking_step4():
    language = {
        "partners": [{
            "partner_label": "Partner 0",
            "language_evidence_coverage_machine": {
                "german_official_source_candidate_available": True,
                "english_official_source_candidate_available": True,
            },
            "step4_web_wording_readiness": {"de": False, "en": False},
        }]
    }
    pack = build_human_review_pack(_queue(), language_evidence=language, scope_evidence=_scope_evidence())
    row = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0")
    assert row["german_official_source_candidate_available"] is True
    assert row["english_official_source_candidate_available"] is True
    assert row["step4_de_wording_ready"] is False
    assert row["step4_en_wording_ready"] is False
    assert row["reviewer_decision"] == "not_reviewed"


def test_human_review_pack_uses_semantic_income_reconciliation_and_actual_article_number():
    reconciliation = {
        "partners": [{
            "partner_label": "Partner 0",
            "income_scopes": [{
                "income_type": "dividend",
                "actual_article_numbers_machine": [8],
                "nonstandard_article_number_machine": True,
                "unique_text_variant_count": 1,
            }],
        }]
    }
    pack = build_human_review_pack(_queue(), article_reconciliation=reconciliation, scope_evidence=_scope_evidence())
    row = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0" and row["income_type"] == "dividend")
    assert row["article_number_machine"] == 8
    assert row["actual_article_numbers_machine"] == [8]
    assert row["nonstandard_article_number_machine"] is True
    assert row["review_priority"] == "HIGH"
    assert "nonstandard_income_article_number" in row["machine_review_reason"]


def test_human_review_pack_blocks_missing_or_incomplete_rate_condition_evidence():
    incomplete = _scope_evidence()
    incomplete["scopes"][0]["rate_branches_machine"][0]["condition_evidence_text"] = ""
    pack = build_human_review_pack(_queue(), scope_evidence=incomplete)
    row = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0" and row["income_type"] == "dividend")
    assert row["review_ready"] is False
    assert row["conditions_complete_machine"] is False
    assert "branch_1_condition_evidence_missing" in row["review_blockers"]
    assert pack["blocked_scope_count"] == 1

    no_evidence = build_human_review_pack(_queue())
    assert no_evidence["review_ready_scope_count"] == 0
    assert no_evidence["blocked_scope_count"] == 6
    assert all("scope_machine_evidence_missing" in row["review_blockers"] for row in no_evidence["rows"])


def test_human_review_pack_blocks_invalid_branch_shapes_rate_and_source():
    evidence = _scope_evidence()
    first = evidence["scopes"][0]
    first["rate_branches_machine"] = [
        "invalid",
        {
            "rate_percent": None,
            "treatment_candidate": "",
            "condition_evidence_text": "",
            "source_url": "http://invalid.example",
        },
    ]
    pack = build_human_review_pack(_queue(), scope_evidence=evidence)
    row = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0" and row["income_type"] == "dividend")
    assert row["review_ready"] is False
    assert set(row["review_blockers"]) >= {
        "branch_1_invalid",
        "branch_2_rate_or_treatment_missing",
        "branch_2_condition_evidence_missing",
        "branch_2_official_source_missing",
    }


def test_human_review_pack_blocks_empty_branch_list():
    evidence = _scope_evidence()
    evidence["scopes"][0]["rate_branches_machine"] = []
    row = next(
        row for row in build_human_review_pack(_queue(), scope_evidence=evidence)["rows"]
        if row["partner_label"] == "Partner 0" and row["income_type"] == "dividend"
    )
    assert row["review_blockers"] == ["rate_or_treatment_branch_missing"]


def test_human_review_pack_accepts_non_rate_treatment_branch_with_exact_evidence():
    evidence = _scope_evidence()
    branch = evidence["scopes"][0]["rate_branches_machine"][0]
    branch["rate_percent"] = None
    branch["treatment_candidate"] = "residence_only"
    pack = build_human_review_pack(_queue(), scope_evidence=evidence)
    row = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0" and row["income_type"] == "dividend")
    assert row["review_ready"] is True
    assert row["rate_branches_machine"][0]["treatment_candidate"] == "residence_only"
    assert row["candidate_rates_percent_machine"] == []


def test_human_review_pack_rejects_duplicate_or_invalid_scope_evidence():
    evidence = _scope_evidence()
    evidence["scopes"].append(dict(evidence["scopes"][0]))
    with pytest.raises(ValueError, match="Duplicate scope evidence"):
        build_human_review_pack(_queue(), scope_evidence=evidence)

    with pytest.raises(ValueError, match="must be a list"):
        build_human_review_pack(_queue(), scope_evidence={"scopes": {}})

    evidence = _scope_evidence()
    evidence["scopes"][0]["income_type"] = "capital_gain"
    with pytest.raises(ValueError, match="supported income_type"):
        build_human_review_pack(_queue(), scope_evidence=evidence)


def test_human_review_pack_csv_is_excel_compatible_utf8_bom(tmp_path: Path):
    pack = build_human_review_pack(_queue(), scope_evidence=_scope_evidence())
    path = tmp_path / "review.csv"
    write_csv(pack, path)
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    assert len(rows) == 6
    assert set(rows[0]) >= {"partner_label", "review_priority", "reviewer_decision", "official_source_urls", "review_ready", "rate_branches_machine"}
    assert "holding_period_value_machine" in rows[0]["rate_branches_machine"]


def test_human_review_pack_rejects_released_empty_or_countryless_queue():
    released = _queue()
    released["status"] = "released"
    with pytest.raises(ValueError, match="unreleased"):
        build_human_review_pack(released)

    empty = _queue()
    empty["scopes"] = []
    with pytest.raises(ValueError, match="no scopes"):
        build_human_review_pack(empty)

    countryless = _queue()
    countryless["source_country"] = ""
    with pytest.raises(ValueError, match="missing source_country"):
        build_human_review_pack(countryless)


def test_human_review_pack_rejects_invalid_scope_identity():
    queue = _queue()
    queue["scopes"][0]["income_type"] = "capital_gain"
    with pytest.raises(ValueError, match="supported income_type"):
        build_human_review_pack(queue, scope_evidence=_scope_evidence())


def test_human_review_pack_cli_writes_json_and_csv(tmp_path: Path, monkeypatch):
    queue_path = tmp_path / "queue.json"
    evidence_path = tmp_path / "scope.json"
    output_json = tmp_path / "review.json"
    output_csv = tmp_path / "review.csv"
    queue_path.write_text(json.dumps(_queue()), encoding="utf-8")
    evidence_path.write_text(json.dumps(_scope_evidence()), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "build_country_human_review_pack",
        "--queue", str(queue_path),
        "--scope-evidence", str(evidence_path),
        "--output-json", str(output_json),
        "--output-csv", str(output_csv),
    ])
    review_module.main()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["scope_count"] == 6
    assert payload["review_ready_scope_count"] == 6
    assert output_csv.read_bytes().startswith(b"\xef\xbb\xbf")
