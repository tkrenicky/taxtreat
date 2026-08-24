from pathlib import Path

from taxtreat.engine.legal_rule_engine import TaxTreatment, resolve_tax_treatment
from taxtreat.engine.legal_rule_loader import load_legal_rules


RULE_DIR = Path("data/legal_rules_stage6")


def _all_verified_rate_rules():
    for path in sorted(RULE_DIR.glob("*.json")):
        for rule in load_legal_rules(path):
            if rule.effect == "rate" and rule.verification_status == "verified":
                yield rule


def test_non_taxing_treatments_never_carry_positive_rate():
    bad = []
    for rule in _all_verified_rate_rules():
        treatment = resolve_tax_treatment(rule)
        if treatment in {
            TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION,
            TaxTreatment.DOMESTIC_EXEMPTION,
        } and rule.rate not in {0, 0.0}:
            bad.append((rule.rule_id, rule.rate, treatment.value))
    assert not bad, f"Non-taxing treatment with positive rate: {bad}"


def test_positive_verified_rates_are_taxable_at_rate():
    bad = []
    for rule in _all_verified_rate_rules():
        if rule.rate is None or float(rule.rate) <= 0:
            continue
        treatment = resolve_tax_treatment(rule)
        if treatment != TaxTreatment.TAXABLE_AT_RATE:
            bad.append((rule.rule_id, rule.rate, treatment.value if treatment else None))
    assert not bad, f"Positive rate classified as non-taxing treatment: {bad}"


def test_zero_treaty_protocol_mli_rates_are_exclusive_foreign_taxation():
    bad = []
    for rule in _all_verified_rate_rules():
        if rule.rate not in {0, 0.0} or rule.legal_layer not in {"treaty", "protocol", "mli"}:
            continue
        treatment = resolve_tax_treatment(rule)
        if treatment != TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION:
            bad.append((rule.rule_id, treatment.value if treatment else None))
    assert not bad, f"Zero treaty-like rate not classified as exclusive foreign taxation: {bad}"


def test_zero_eu_relief_rates_are_domestic_exemptions():
    bad = []
    for rule in _all_verified_rate_rules():
        if rule.rate not in {0, 0.0} or rule.legal_layer != "eu_relief":
            continue
        treatment = resolve_tax_treatment(rule)
        if treatment != TaxTreatment.DOMESTIC_EXEMPTION:
            bad.append((rule.rule_id, treatment.value if treatment else None))
    assert not bad, f"Zero EU-relief rate not classified as domestic exemption: {bad}"
