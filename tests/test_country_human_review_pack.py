from __future__ import annotations

import csv
from pathlib import Path

import pytest

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
    pack = build_human_review_pack(_queue(), royalty_audit=audit, article_reconciliation=reconciliation)
    assert pack["scope_count"] == 6
    assert pack["high_priority_scope_count"] == 1
    assert pack["medium_priority_scope_count"] == 1
    assert pack["policy"]["machine_output_is_not_legal_approval"] is True
    assert pack["policy"]["canonical_materialization_requires_approved_review"] is True
    assert all(row["promotable_to_canonical"] is False for row in pack["rows"])
    assert pack["rows"][0]["partner_label"] == "Partner 0"
    assert pack["rows"][0]["income_type"] == "royalty"
    assert pack["rows"][0]["candidate_rates_percent_machine"] == [5.0, 10.0]


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
    pack = build_human_review_pack(_queue(), language_evidence=language)
    row = next(row for row in pack["rows"] if row["partner_label"] == "Partner 0")
    assert row["german_official_source_candidate_available"] is True
    assert row["english_official_source_candidate_available"] is True
    assert row["step4_de_wording_ready"] is False
    assert row["step4_en_wording_ready"] is False
    assert row["reviewer_decision"] == "not_reviewed"


def test_human_review_pack_csv_is_excel_compatible_utf8_bom(tmp_path: Path):
    pack = build_human_review_pack(_queue())
    path = tmp_path / "review.csv"
    write_csv(pack, path)
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    assert len(rows) == 6
    assert set(rows[0]) >= {"partner_label", "review_priority", "reviewer_decision", "official_source_urls"}


def test_human_review_pack_rejects_released_or_empty_queue():
    released = _queue()
    released["status"] = "released"
    with pytest.raises(ValueError, match="unreleased"):
        build_human_review_pack(released)

    empty = _queue()
    empty["scopes"] = []
    with pytest.raises(ValueError, match="no scopes"):
        build_human_review_pack(empty)
