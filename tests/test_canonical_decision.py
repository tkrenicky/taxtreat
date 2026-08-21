from datetime import date
from pathlib import Path

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction as canonical_analyze_transaction,
)
from taxtreat.services.runtime_gate import RuntimeGateResult
import taxtreat.engine.legal_rule_engine as legal_engine
import taxtreat.services.decision as decision_service

LEGACY_RULE_DIR = (
    Path(__file__).parents[1]
    / "data"
    / "legal_rules"
)


def analyze_transaction(request):
    return canonical_analyze_transaction(
        request,
        rule_dir=LEGACY_RULE_DIR,
    )


def request(**overrides):
    values = {
        "source_country": "CZ",
        "recipient_country": "CH",
        "income_type": "royalties",
        "transaction_date": date(2026, 8, 3),
        "facts": {
            "recipient_is_treaty_resident": True,
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "arm_length_amount": True,
            "recipient_is_qualifying_company": False,
            "recipient_country_imposes_royalty_wht_on_nonresidents": False,
        },
        "determinations": {"treaty_ppt_passed": True},
    }
    values.update(overrides)
    return CanonicalAnalysisRequest(**values)


def test_canonical_decision_ignores_user_supplied_legal_conclusion():
    result = analyze_transaction(request())

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == [
        "legal_fact:recipient_country_imposes_royalty_wht_on_nonresidents"
    ]
    assert result.candidate_rate == 5.0
    assert result.candidate_rule_id == "CZ-CH-ROY-PROTOCOL-5"


def test_canonical_decision_distinguishes_pending_from_out_of_scope():
    pending_country = analyze_transaction(
        request(recipient_country="DE")
    )
    unsupported_country = analyze_transaction(
        request(recipient_country="ZZ")
    )
    unsupported_income = analyze_transaction(
        request(income_type="service_fee")
    )

    assert pending_country.status == DecisionStatus.REVIEW_REQUIRED
    assert pending_country.requires_review is True
    assert pending_country.candidate_rate is None
    assert pending_country.missing_legal_layers == [
        "domestic",
        "eu_relief",
        "mli",
        "treaty_or_protocol",
    ]
    assert unsupported_country.status == DecisionStatus.OUT_OF_SCOPE
    assert unsupported_country.requires_review is False
    assert unsupported_country.requires_review is False
    assert unsupported_income.status == DecisionStatus.OUT_OF_SCOPE
    assert unsupported_income.requires_review is False


def test_registered_released_sk_dividend_enters_domestic_first_evaluation():
    result = canonical_analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="SK",
            recipient_country="CZ",
            income_type="dividend",
            transaction_date=date(2026, 8, 18),
            facts={},
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.requires_review is True
    assert result.rate is None
    assert result.tax_treatment is None
    assert result.missing_legal_layers == []
    assert result.missing_facts == [
        "distribution_category_is_section_3_1_f",
        "distribution_is_tax_deductible_for_payer",
        "recipient_entity_type",
        "recipient_is_non_cooperating_state_taxpayer",
    ]


def test_unknown_source_country_preserves_out_of_scope_behavior():
    result = analyze_transaction(
        request(source_country="ZZ", recipient_country="CH")
    )

    assert result.status == DecisionStatus.OUT_OF_SCOPE
    assert result.requires_review is False


def test_canonical_decision_without_legal_fact_condition_still_uses_rule_gate():
    result = analyze_transaction(
        request(
            recipient_country="AT",
            income_type="interest",
            facts={
                "recipient_is_treaty_resident": True,
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
                "arm_length_amount": True,
                "recipient_is_qualifying_company": False,
            },
            determinations={},
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.candidate_rate == 15.0
    assert result.missing_facts == ["determination:treaty_ppt_passed"]


def test_canonical_scoped_result_can_have_no_candidate_rate():
    result = analyze_transaction(
        request(
            recipient_country="AT",
            income_type="interest",
            transaction_date=date(2021, 1, 1),
            facts={
                "recipient_is_treaty_resident": True,
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
                "arm_length_amount": True,
                "recipient_is_qualifying_company": False,
            },
            determinations={},
        )
    )

    assert result.candidate_rule_id is None
    assert result.missing_facts == ["determination:treaty_ppt_passed"]


def test_runtime_gate_block_remains_review_required(monkeypatch):
    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        lambda **kwargs: RuntimeGateResult(
            applies=True,
            allowed=False,
            missing_facts=["official_status_instrument_effect"],
            explanation="Status-instrument effect requires legal review.",
        ),
    )

    result = analyze_transaction(request())

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.requires_review is True
    assert result.rate is None
    assert result.eligible is False
    assert result.missing_facts == ["official_status_instrument_effect"]
    assert result.explanation == [
        "Status-instrument effect requires legal review."
    ]


def test_legal_normalizers_cover_legacy_boundary_values():
    assert legal_engine._boolean_like(False) is False
    assert legal_engine._boolean_like(" NO ") is False
    assert legal_engine._boolean_like("unknown") is None
    assert legal_engine._boolean_like(None) is None

    assert legal_engine._royalty_category_groups(None) == set()
    assert legal_engine._royalty_category_groups(
        "all_other_article_12_royalties"
    ) == {"other"}
    assert legal_engine._royalty_category_groups("financial_lease") == {
        "equipment"
    }
    assert legal_engine._royalty_category_groups("other") == {"other"}
    assert legal_engine._royalty_category_groups("technical_assistance") == {
        "industrial_ip"
    }

    assert legal_engine._numeric_like(True) is None
    assert legal_engine._numeric_like(5) == 5.0
    assert legal_engine._numeric_like(" 12.5% ") == 12.5
    assert legal_engine._numeric_like("not-a-number") is None
    assert legal_engine._numeric_like(None) is None


def test_royalty_category_matching_covers_residual_and_empty_groups():
    assert legal_engine._royalty_categories_match("other", "other") is True
    assert legal_engine._royalty_categories_match(
        "copyright_literary_artistic_or_scientific",
        "all_other_article_12_royalties",
    ) is True
    assert legal_engine._royalty_categories_match(
        "industrial_commercial_or_scientific_equipment",
        "other",
    ) is False
    assert legal_engine._royalty_categories_match("unknown", "unknown-2") is False


def test_condition_evaluation_covers_control_boolean_numeric_and_type_error():
    assert legal_engine._evaluate_condition(
        legal_engine.LegalCondition("fallback_case", "==", True),
        {},
        {},
    ) == (True, None)

    assert legal_engine._evaluate_condition(
        legal_engine.LegalCondition(
            "missing_legal_fact",
            "==",
            True,
            fact_source="legal",
        ),
        {},
        {},
    ) == (None, "legal_fact:missing_legal_fact")

    assert legal_engine._evaluate_condition(
        legal_engine.LegalCondition("royalty_category", "!=", "other"),
        {"royalty_category": "other"},
        {},
    ) == (False, None)

    assert legal_engine._evaluate_condition(
        legal_engine.LegalCondition("beneficial_owner", "!=", "false"),
        {"beneficial_owner": True},
        {},
    ) == (True, None)

    assert legal_engine._evaluate_condition(
        legal_engine.LegalCondition("ownership", ">=", "10%"),
        {"ownership": 12},
        {},
    ) == (True, None)

    assert legal_engine._evaluate_condition(
        legal_engine.LegalCondition("ownership", ">", 10),
        {"ownership": "not-numeric"},
        {},
    ) == (False, None)

    assert legal_engine._evaluate_condition(
        legal_engine.LegalCondition("value", "in", 3),
        {"value": 1},
        {},
    ) == (False, None)
