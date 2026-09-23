import json
from pathlib import Path

from taxtreat.tools.audit_sk_royalty_categories import (
    BASE_CATEGORIES,
    CATEGORY_SENSITIVE_REVIEW_COUNTRIES,
    ROYALTY_EXPLICIT_BRANCH_REQUIRED_COUNTRIES,
    SPECIAL_EXEMPTION_REVIEW_COUNTRIES,
    build_audit,
)

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


def test_category_sensitive_reconciliation_queue_includes_second_wave_countries():
    audit = _audit()
    assert len(CATEGORY_SENSITIVE_REVIEW_COUNTRIES) == 25
    assert audit["category_review_required_count"] == 25
    assert audit["category_review_required_countries"] == list(CATEGORY_SENSITIVE_REVIEW_COUNTRIES)
    assert {"FR", "JP", "LK", "LU", "SE"} <= set(CATEGORY_SENSITIVE_REVIEW_COUNTRIES)


def test_explicit_branch_queue_also_captures_ae_public_institution_exemption():
    audit = _audit()
    assert SPECIAL_EXEMPTION_REVIEW_COUNTRIES == ("AE",)
    assert len(ROYALTY_EXPLICIT_BRANCH_REQUIRED_COUNTRIES) == 26
    assert audit["special_exemption_review_required_count"] == 1
    assert audit["explicit_branch_review_required_count"] == 26
    assert "AE" in audit["explicit_branch_review_required_countries"]
    assert _scope(audit, "AE")["special_exemption_review_required"] is True


def test_finland_requires_precise_lease_and_copyright_semantics():
    row = _scope(_audit(), "FI")
    assert row["multiple_rate_candidates_present"] is True
    assert row["base_category_keyword_flags"]["software"] is True
    assert row["base_category_keyword_flags"]["equipment_financial_lease"] is True
    assert "copyright_exclusive_residence_treatment" in row["additional_discriminators_required"]
    assert "financial_vs_operating_equipment_lease" in row["additional_discriminators_required"]
    assert row["category_projection_review_required"] is True


def test_vietnam_cannot_be_collapsed_into_one_industrial_ip_category():
    row = _scope(_audit(), "VN")
    assert row["multiple_rate_candidates_present"] is True
    assert "trademark_vs_patent_design_process" in row["additional_discriminators_required"]
    assert "commercial_vs_industrial_or_scientific_knowhow" in row["additional_discriminators_required"]


def test_brazil_ownership_threshold_is_not_a_rate_candidate():
    row = _scope(_audit(), "BR")
    assert 50.0 in row["percentage_tokens_raw"]
    assert row["rate_candidates_machine"] == [15.0, 25.0]
    assert 50.0 in row["non_rate_percentage_tokens"]
    assert "trademark_vs_other_industrial_ip" in row["additional_discriminators_required"]


def test_tunisia_flags_nonstandard_service_discriminators():
    row = _scope(_audit(), "TN")
    assert "technical_or_economic_studies" in row["additional_discriminators_required"]
    assert "technical_assistance" in row["additional_discriminators_required"]


def test_audit_never_promotes_keyword_or_percentage_flags_to_legal_projection():
    audit = _audit()
    assert audit["policy"]["machine_keyword_detection_is_not_legal_interpretation"] is True
    assert audit["policy"]["seven_base_categories_are_not_assumed_to_be_legally_exhaustive"] is True
    assert audit["policy"]["raw_percentage_tokens_are_not_rate_candidates"] is True
    assert audit["policy"]["ownership_and_historical_condition_percentages_cannot_create_rate_branches"] is True
    assert audit["policy"]["multiple_applicable_branches_with_different_results_must_fail_closed"] is True


def test_audit_rejects_incomplete_scope_count():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source["scopes"] = [row for row in source["scopes"] if row.get("income_type") != "royalty"]
    import pytest
    with pytest.raises(ValueError, match="Expected 75 SK royalty scopes"):
        build_audit(source)


def test_audit_rejects_missing_country_or_article_text():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    royalty = next(row for row in source["scopes"] if row.get("income_type") == "royalty")
    royalty["article_text"] = ""
    import pytest
    with pytest.raises(ValueError, match="missing recipient country or article text"):
        build_audit(source)


def test_cli_writes_fail_closed_audit(tmp_path, monkeypatch, capsys):
    from taxtreat.tools import audit_sk_royalty_categories as module

    output = tmp_path / "audit.json"
    monkeypatch.setattr(
        "sys.argv",
        ["audit_sk_royalty_categories", "--input", str(SOURCE), "--output", str(output)],
    )
    module.main()

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["royalty_scope_count"] == 75
    assert payload["category_review_required_count"] == 25
    assert payload["explicit_branch_review_required_count"] == 26
    assert payload["status"] == "royalty_category_audit_not_released"
    stdout = capsys.readouterr().out
    assert "75 scopes / 26 explicit-branch-review-required" in stdout


def test_audit_rejects_category_queue_country_outside_scope(monkeypatch):
    from taxtreat.tools import audit_sk_royalty_categories as module
    import pytest

    monkeypatch.setattr(
        module,
        "CATEGORY_SENSITIVE_REVIEW_COUNTRIES",
        (*module.CATEGORY_SENSITIVE_REVIEW_COUNTRIES, "ZZ"),
    )
    with pytest.raises(ValueError, match="countries missing from the 75-scope universe"):
        module.build_audit(json.loads(SOURCE.read_text(encoding="utf-8")))


def test_audit_rejects_explicit_branch_queue_drift(monkeypatch):
    from taxtreat.tools import audit_sk_royalty_categories as module
    import pytest

    monkeypatch.setattr(
        module,
        "ROYALTY_EXPLICIT_BRANCH_REQUIRED_COUNTRIES",
        (*module.ROYALTY_EXPLICIT_BRANCH_REQUIRED_COUNTRIES, "ZZ"),
    )
    with pytest.raises(ValueError, match="explicit-branch review queue membership drifted"):
        module.build_audit(json.loads(SOURCE.read_text(encoding="utf-8")))
