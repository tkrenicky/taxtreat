from __future__ import annotations

import json
from dataclasses import replace
from datetime import date

from taxtreat.countries.registry import get_country_config
from taxtreat.countries.sk import evaluate_domestic_precedence
from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    TaxTreatment,
)
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    _apply_source_country_release_manifest_gate,
    analyze_transaction,
)


def request():
    return CanonicalAnalysisRequest(
        source_country="SK",
        recipient_country="CZ",
        income_type="dividend",
        transaction_date=date(2026, 8, 21),
        facts={
            "recipient_entity_type": "corporate",
            "distribution_is_tax_deductible_for_payer": False,
            "recipient_is_non_cooperating_state_taxpayer": False,
            "distribution_category_is_section_3_1_f": False,
        },
    )


def domestic_result():
    req = request()
    return evaluate_domestic_precedence(
        recipient_country=req.recipient_country,
        income_type=req.income_type,
        transaction_date=req.transaction_date,
        facts=req.facts,
    )


def test_underlying_sk_legal_result_is_complete_non_rate_result():
    result = domestic_result()

    assert result is not None
    assert result.status == DecisionStatus.FINAL
    assert result.requires_review is False
    assert result.eligible is True

    assert result.rate is None
    assert result.candidate_rate is None
    assert (
        result.tax_treatment
        == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )
    assert (
        result.selected_rule_id
        == "SK-DIV-DOMESTIC-SECTION-12-7-C"
    )


def test_current_manifest_fails_closed_until_structured_rules_are_materialized():
    result = analyze_transaction(request())

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.requires_review is True
    assert result.eligible is False
    assert result.rate is None
    assert result.tax_treatment is None
    assert result.selected_rule_id is None
    assert result.candidate_rule_id == "SK-DIV-DOMESTIC-SECTION-12-7-C"
    assert result.candidate_tax_treatment == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    assert "source_country_release_manifest" in result.missing_legal_layers


def test_open_manifest_allows_same_calculated_result_to_be_final(
    tmp_path,
):
    manifest = tmp_path / "release.json"
    manifest.write_text(
        json.dumps({
            "release_eligible": True,
            "release_status": "released",
            "blockers": [],
        }),
        encoding="utf-8",
    )

    config = replace(
        get_country_config("SK"),
        release_manifest_path=manifest,
    )

    result = domestic_result()
    assert result is not None

    gated = _apply_source_country_release_manifest_gate(
        request(),
        result,
        country_config=config,
    )

    assert gated.status == DecisionStatus.FINAL
    assert gated.requires_review is False
    assert gated.eligible is True
    assert (
        gated.selected_rule_id
        == "SK-DIV-DOMESTIC-SECTION-12-7-C"
    )
    assert (
        gated.tax_treatment
        == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )
    assert gated.rate is None


def test_missing_manifest_fails_closed(
    tmp_path,
):
    missing = tmp_path / "does-not-exist.json"

    config = replace(
        get_country_config("SK"),
        release_manifest_path=missing,
    )

    result = domestic_result()
    assert result is not None

    gated = _apply_source_country_release_manifest_gate(
        request(),
        result,
        country_config=config,
    )

    assert gated.status == DecisionStatus.REVIEW_REQUIRED
    assert gated.requires_review is True
    assert gated.eligible is False

    assert gated.selected_rule_id is None
    assert (
        gated.candidate_rule_id
        == "SK-DIV-DOMESTIC-SECTION-12-7-C"
    )

    assert any(
        "manifest_unavailable" in line
        for line in gated.explanation
    )


def test_cz_has_no_country_specific_release_manifest_gate():
    config = get_country_config("CZ")

    assert config.release_manifest_path is None
    assert config.domestic_precedence_handler is None
