import json
from pathlib import Path

from taxtreat.tools.audit_sk_royalty_categories import BASE_CATEGORIES, build_audit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "legal_reviews" / "sk_outbound" / "treaty_article_machine_extraction.json"


def _audit():
    return build_audit(json.loads(SOURCE.read_text(encoding="utf-8")))


def _scope(audit, country):
    return next(row for row in audit["scopes"] if row["scope_key"] == ["SK", country, "royalty"])


def test_sk_royalty_audit_covers_all_75_scopes_and_releases_nothing():
    audit = _audit()
    assert audit["royalty_scope_count"] == 75
    assert audit["status"] == "royalty_category_audit_not_released"
    assert len(BASE_CATEGORIES) == 7
    assert all(row["projection_released"] is False for row in audit["scopes"])
    assert all(row["legal_review_completed"] is False for row in audit["scopes"])


def test_finland_proves_seven_broad_categories_need_precise_lease_and_copyright_semantics():
    row = _scope(_audit(), "FI")
    assert row["multiple_rate_tokens_present"] is True
    assert row["base_category_keyword_flags"]["software"] is True
    assert row["base_category_keyword_flags"]["equipment_financial_lease"] is True
    assert "copyright_exclusive_residence_treatment" in row["additional_discriminators_required"]
    assert "financial_vs_operating_equipment_lease" in row["additional_discriminators_required"]
    assert row["category_projection_review_required"] is True


def test_vietnam_cannot_be_safely_collapsed_into_one_industrial_ip_knowhow_category():
    row = _scope(_audit(), "VN")
    assert row["multiple_rate_tokens_present"] is True
    assert "trademark_vs_patent_design_process" in row["additional_discriminators_required"]
    assert "commercial_vs_industrial_or_scientific_knowhow" in row["additional_discriminators_required"]
    assert row["category_projection_review_required"] is True


def test_brazil_flags_trademark_split_and_historical_rate_token_for_review():
    row = _scope(_audit(), "BR")
    assert row["multiple_rate_tokens_present"] is True
    assert "trademark_vs_other_industrial_ip" in row["additional_discriminators_required"]
    assert "historical_related_party_transition_clause" in row["additional_discriminators_required"]
    assert row["category_projection_review_required"] is True


def test_tunisia_flags_nonstandard_technical_service_royalty_discriminators():
    row = _scope(_audit(), "TN")
    assert "technical_or_economic_studies" in row["additional_discriminators_required"]
    assert "technical_assistance" in row["additional_discriminators_required"]


def test_machine_audit_never_treats_keyword_flags_as_legal_projection():
    audit = _audit()
    assert audit["policy"]["machine_keyword_detection_is_not_legal_interpretation"] is True
    assert audit["policy"]["seven_base_categories_are_not_assumed_to_be_legally_exhaustive"] is True
    assert audit["policy"]["multiple_applicable_branches_with_different_results_must_fail_closed"] is True
