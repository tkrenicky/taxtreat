from datetime import date
from pathlib import Path

import pytest

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalCondition,
    LegalRule,
    TaxTreatment,
    _evaluate_rule,
    resolve_tax_treatment,
)
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.engine.layered_decision import evaluate_layered_rules
from taxtreat.services.calculation import (
    build_withholding_compliance_schedule,
    build_withholding_tax_calculation,
)


def _verified_zero_rule(layer: str) -> LegalRule:
    instrument = "eu_directive" if layer == "eu_relief" else "treaty"
    return LegalRule(
        rule_id=f"ZERO-{layer}",
        income_type="dividend",
        source_country="CZ",
        recipient_country="AT",
        legal_instrument=instrument,
        legal_layer=layer,
        rate=0.0,
        effective_from=date(2020, 1, 1),
        verification_status="verified",
        source_text="source",
        source_id="SOURCE",
        source_url="https://example.test/source",
        source_excerpt_hash="a" * 64,
        dataset_release="release-1",
    )


@pytest.mark.parametrize(
    ("layer", "treatment"),
    [
        ("treaty", TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION),
        ("eu_relief", TaxTreatment.DOMESTIC_EXEMPTION),
    ],
)
def test_final_non_taxing_result_is_not_presented_as_zero_rate(
    layer,
    treatment,
):
    result = evaluate_layered_rules(
        [_verified_zero_rule(layer)],
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "AT",
        },
        as_of=date(2026, 8, 15),
    )

    assert result.status == DecisionStatus.FINAL
    assert result.tax_treatment == treatment
    assert result.rate is None
    assert result.candidate_rate == 0.0
    assert result.candidate_tax_treatment == treatment
    assert result.citations[0]["tax_treatment"] == treatment.value


def test_treaty_result_keeps_domestic_starting_rate_in_audit_path():
    domestic = LegalRule(
        rule_id="DOMESTIC-15",
        income_type="dividend",
        source_country="CZ",
        recipient_country="AT",
        legal_instrument="domestic_law",
        legal_layer="domestic",
        rate=15.0,
        effective_from=date(2020, 1, 1),
        verification_status="verified",
        source_text="Domestic standard rate.",
        source_id="DOMESTIC-SOURCE",
        source_url="https://example.test/domestic",
        source_excerpt_hash="b" * 64,
        dataset_release="release-1",
    )
    treaty = LegalRule(
        rule_id="TREATY-10",
        income_type="dividend",
        source_country="CZ",
        recipient_country="AT",
        legal_instrument="treaty",
        legal_layer="treaty",
        rate=10.0,
        effective_from=date(2020, 1, 1),
        verification_status="verified",
        source_text="Treaty maximum rate.",
        source_id="TREATY-SOURCE",
        source_url="https://example.test/treaty",
        source_excerpt_hash="c" * 64,
        dataset_release="release-1",
    )

    result = evaluate_layered_rules(
        [domestic, treaty],
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "AT",
        },
        as_of=date(2026, 8, 15),
    )

    assert result.status == DecisionStatus.FINAL
    assert result.rate == 10.0
    assert result.selected_rule_id == "TREATY-10"
    assert {
        (citation["legal_layer"], citation["rate"])
        for citation in result.citations
    } == {("domestic", 15.0), ("treaty", 10.0)}


def test_every_stage6_zero_rule_has_unambiguous_non_taxing_semantics():
    zero_rules = []
    for path in sorted(Path("data/legal_rules_stage6").glob("*.json")):
        zero_rules.extend(
            rule
            for rule in load_legal_rules(path)
            if rule.effect == "rate" and rule.rate == 0
        )

    assert len(zero_rules) == 555
    assert {rule.legal_layer for rule in zero_rules} == {
        "treaty",
        "eu_relief",
    }
    assert all(
        resolve_tax_treatment(rule)
        == (
            TaxTreatment.DOMESTIC_EXEMPTION
            if rule.legal_layer == "eu_relief"
            else TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION
        )
        for rule in zero_rules
    )


@pytest.mark.parametrize(
    "treatment",
    ["exclusive_foreign_taxation", "domestic_exemption"],
)
def test_non_taxing_calculation_keeps_tax_amount_without_fake_rate(
    treatment,
):
    calculation = build_withholding_tax_calculation(
        {"amount": "100000", "currency": "CZK"},
        decision_status="FINAL",
        rate_percent=None,
        tax_treatment=treatment,
    )

    assert calculation["status"] == "CALCULATED"
    assert calculation["tax_treatment"] == treatment
    assert calculation["rate_percent"] is None
    assert calculation["withholding_tax_czk"] == "0"
    assert calculation["net_amount_czk"] == "100000.00"


def test_non_taxing_treatment_drives_notification_schedule():
    schedule = build_withholding_compliance_schedule(
        "2026-08-12",
        income_type="dividend",
        decision_status="FINAL",
        rate_percent=None,
        tax_treatment="exclusive_foreign_taxation",
    )

    assert schedule["tax_treatment"] == "exclusive_foreign_taxation"
    assert schedule["tax_remittance_deadline"] is None
    assert schedule["notification_deadline"] == "2027-02-01"


def test_catalog_string_boolean_matches_ui_boolean_fact():
    rule = LegalRule(
        rule_id="BOOLEAN-SERIALIZATION",
        income_type="royalty",
        source_country="CZ",
        recipient_country="AT",
        legal_instrument="treaty",
        conditions=[
            LegalCondition("beneficial_owner", "==", "true"),
        ],
    )

    matches, missing, failed = _evaluate_rule(
        rule,
        {"beneficial_owner": True},
        {},
    )

    assert matches is True
    assert missing == []
    assert failed == []


@pytest.mark.parametrize(
    ("ui_category", "catalog_category"),
    [
        (
            "copyright_literary_artistic_or_scientific",
            "copyright_literary_artistic_scientific_including_films_and_broadcast_media",
        ),
        (
            "software_patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
            "patent_trademark_design_model_plan_secret_formula_process_software_equipment_or_knowhow",
        ),
        (
            "industrial_commercial_or_scientific_equipment",
            "patent_trademark_design_model_plan_secret_formula_process_software_equipment_or_knowhow",
        ),
        (
            "industrial_commercial_or_scientific_equipment",
            "industrial_commercial_scientific_equipment",
        ),
        (
            "software_patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
            "other",
        ),
    ],
)
def test_ui_royalty_category_matches_treaty_taxonomy(
    ui_category,
    catalog_category,
):
    rule = LegalRule(
        rule_id="ROYALTY-TAXONOMY",
        income_type="royalty",
        source_country="CZ",
        recipient_country="AT",
        legal_instrument="treaty",
        conditions=[
            LegalCondition("royalty_category", "==", catalog_category),
        ],
    )

    matches, missing, failed = _evaluate_rule(
        rule,
        {"royalty_category": ui_category},
        {},
    )

    assert matches is True
    assert missing == []
    assert failed == []
