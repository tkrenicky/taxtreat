from taxtreat.tools.audit_sk_royalty_categories import CATEGORY_SENSITIVE_REVIEW_COUNTRIES
from taxtreat.tools.build_sk_structured_treaty_rules import (
    _category_sensitive_royalty_requires_explicit_branch,
)


def test_all_audit_sensitive_royalty_countries_require_explicit_branch():
    assert len(CATEGORY_SENSITIVE_REVIEW_COUNTRIES) == 20
    for country in CATEGORY_SENSITIVE_REVIEW_COUNTRIES:
        assert _category_sensitive_royalty_requires_explicit_branch({
            "income_type": "royalty",
            "recipient_country": country,
        })


def test_non_sensitive_or_non_royalty_scope_can_use_normal_fallback_path():
    assert _category_sensitive_royalty_requires_explicit_branch({
        "income_type": "royalty",
        "recipient_country": "US",
    }) is False
    assert _category_sensitive_royalty_requires_explicit_branch({
        "income_type": "interest",
        "recipient_country": "FI",
    }) is False
