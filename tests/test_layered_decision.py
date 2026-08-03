from datetime import date

import pytest

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalCondition,
    LegalRule,
)
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.engine.layered_decision import evaluate_layered_rules


def _interest_facts(recipient: str) -> dict:
    return {
        "income_type": "interest",
        "source_country": "CZ",
        "recipient_country": recipient,
        "recipient_is_treaty_resident": True,
        "beneficial_owner": True,
        "permanent_establishment_connection": False,
        "arm_length_amount": True,
        "recipient_is_qualifying_company": False,
    }


@pytest.mark.parametrize(
    ("country", "recipient", "before_mli", "from_mli"),
    [
        ("rakousko", "AT", date(2020, 12, 31), date(2021, 1, 1)),
        ("svycarsko", "CH", date(2021, 12, 31), date(2022, 1, 1)),
    ],
)
def test_mli_withholding_effective_date_boundary(
    country: str,
    recipient: str,
    before_mli: date,
    from_mli: date,
):
    rules = load_legal_rules(f"data/legal_rules/{country}.json")
    facts = _interest_facts(recipient)

    before = evaluate_layered_rules(rules, facts, as_of=before_mli)
    assert before.candidate_rate == 0.0
    assert not any(row["layer"] == "mli" for row in before.layer_results)

    gated = evaluate_layered_rules(rules, facts, as_of=from_mli)
    assert gated.candidate_rate is None
    assert gated.missing_facts == ["determination:treaty_ppt_passed"]

    after = evaluate_layered_rules(
        rules,
        facts,
        as_of=from_mli,
        determinations={"treaty_ppt_passed": True},
    )
    assert after.candidate_rate == 0.0
    assert any(
        row["layer"] == "mli" and row["outcome"] == "passed"
        for row in after.layer_results
    )


def test_failed_ppt_blocks_treaty_benefit():
    rules = load_legal_rules("data/legal_rules/rakousko.json")
    result = evaluate_layered_rules(
        rules,
        _interest_facts("AT"),
        as_of=date(2021, 1, 1),
        determinations={"treaty_ppt_passed": False},
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.candidate_rate is None
    assert "treaty_ppt_passed" in result.failed_conditions


def _verified_rule(rule_id: str, **overrides) -> LegalRule:
    values = {
        "rule_id": rule_id,
        "income_type": "interest",
        "source_country": "CZ",
        "recipient_country": "AT",
        "legal_instrument": "domestic_law",
        "legal_layer": "domestic",
        "rate": 15.0,
        "effective_from": date(2020, 1, 1),
        "verification_status": "verified",
        "source_text": "source",
        "source_id": "SOURCE",
        "source_url": "https://example.test/source",
        "source_excerpt_hash": "a" * 64,
        "dataset_release": "release-1",
    }
    values.update(overrides)
    return LegalRule(**values)


def test_layered_engine_handles_scope_release_and_final_paths():
    facts = _interest_facts("AT")
    out_of_scope = evaluate_layered_rules([], facts, as_of=date(2026, 1, 1))
    assert out_of_scope.status == DecisionStatus.OUT_OF_SCOPE

    inconsistent = evaluate_layered_rules(
        [
            _verified_rule("A"),
            _verified_rule("B", dataset_release="release-2"),
        ],
        facts,
        as_of=date(2026, 1, 1),
    )
    assert inconsistent.candidate_rate is None
    assert "inconsistent dataset releases" in inconsistent.explanation[0]

    no_release = evaluate_layered_rules(
        [_verified_rule("NO-RELEASE", dataset_release=None)],
        facts,
        as_of=date(2026, 1, 1),
    )
    assert no_release.dataset_release is None
    assert no_release.status == DecisionStatus.FINAL

    final = evaluate_layered_rules(
        [_verified_rule("DOMESTIC")],
        facts,
        as_of=date(2026, 1, 1),
    )
    assert final.status == DecisionStatus.FINAL
    assert final.rate == 15.0
    assert final.selected_rule_id == "DOMESTIC"


def test_verified_gate_and_missing_better_rule_are_fail_closed():
    facts = _interest_facts("AT")
    gate = _verified_rule(
        "PPT",
        legal_instrument="mli",
        legal_layer="mli",
        effect="eligibility_gate",
        rate=None,
        applies_to_layers=["treaty"],
        conditions=[
            LegalCondition(
                "treaty_ppt_passed", "==", True, "determination"
            )
        ],
    )
    treaty = _verified_rule(
        "TREATY",
        legal_instrument="treaty",
        legal_layer="treaty",
        rate=0.0,
    )
    final = evaluate_layered_rules(
        [gate, treaty],
        facts,
        as_of=date(2026, 1, 1),
        determinations={"treaty_ppt_passed": True},
    )
    assert final.status == DecisionStatus.FINAL
    assert final.rate == 0.0

    unresolved_relief = _verified_rule(
        "RELIEF",
        legal_instrument="eu_directive",
        legal_layer="eu_relief",
        rate=0.0,
        conditions=[LegalCondition("relief_eligible", "==", True)],
    )
    review = evaluate_layered_rules(
        [_verified_rule("DOMESTIC"), unresolved_relief],
        facts,
        as_of=date(2026, 1, 1),
    )
    assert review.status == DecisionStatus.REVIEW_REQUIRED
    assert review.candidate_rate == 15.0
    assert review.missing_facts == ["relief_eligible"]
