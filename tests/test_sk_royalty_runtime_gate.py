from taxtreat.tools.audit_sk_royalty_categories import (
    CATEGORY_SENSITIVE_REVIEW_COUNTRIES,
    ROYALTY_EXPLICIT_BRANCH_REQUIRED_COUNTRIES,
    category_sensitive_royalty_requires_explicit_branch,
    royalty_requires_explicit_branch,
)


def test_all_audit_sensitive_royalty_countries_require_explicit_branch():
    assert len(CATEGORY_SENSITIVE_REVIEW_COUNTRIES) == 25
    for country in CATEGORY_SENSITIVE_REVIEW_COUNTRIES:
        assert category_sensitive_royalty_requires_explicit_branch({
            "income_type": "royalty",
            "recipient_country": country,
        })


def test_non_sensitive_or_non_royalty_scope_can_use_normal_fallback_path():
    assert category_sensitive_royalty_requires_explicit_branch({
        "income_type": "royalty",
        "recipient_country": "US",
    }) is False
    assert category_sensitive_royalty_requires_explicit_branch({
        "income_type": "interest",
        "recipient_country": "FI",
    }) is False


def test_all_explicit_branch_review_countries_are_gated_before_simple_fallback():
    assert len(ROYALTY_EXPLICIT_BRANCH_REQUIRED_COUNTRIES) == 27
    for country in ROYALTY_EXPLICIT_BRANCH_REQUIRED_COUNTRIES:
        assert royalty_requires_explicit_branch({
            "income_type": "royalty",
            "recipient_country": country,
        })


def test_ae_is_special_exemption_sensitive_but_not_category_sensitive():
    scope = {"income_type": "royalty", "recipient_country": "AE"}
    assert category_sensitive_royalty_requires_explicit_branch(scope) is False
    assert royalty_requires_explicit_branch(scope) is True


def test_oman_is_special_legal_condition_sensitive_but_not_category_sensitive():
    scope = {"income_type": "royalty", "recipient_country": "OM"}
    assert category_sensitive_royalty_requires_explicit_branch(scope) is False
    assert royalty_requires_explicit_branch(scope) is True
