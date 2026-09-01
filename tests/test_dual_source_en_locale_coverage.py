from scripts.verify_dual_source_en_locale_coverage_20260901 import (
    verify_dual_source_en_locale_coverage,
)


def test_dual_source_english_locale_coverage_is_complete_and_isolated():
    result = verify_dual_source_en_locale_coverage()

    assert result["cz_partner_count"] == 100
    assert result["cz_pass_count"] == 100
    assert result["cz_coverage_percent"] == 100.0
    assert result["sk_partner_count"] == 75
    assert result["sk_income_scope_count"] == 225
    assert result["sk_rule_summary_count"] > 225
    assert result["sk_verified_summary_count"] > 0
    assert result["sk_review_required_summary_count"] > 0
