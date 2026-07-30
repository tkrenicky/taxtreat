from pathlib import Path

import pytest
import yaml

from taxtreat.engine.decision_engine import evaluate
from taxtreat.engine.models import (
    ConditionType,
    Rule,
    WHTCondition,
    WHTRate,
)


REFERENCE_DIR = Path("reference_cases")


def load_cases():
    for file in sorted(REFERENCE_DIR.rglob("*.yaml")):
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        yield pytest.param(data, id=data.get("id", file.stem))


def build_rule(case):
    expected = case["expected"]
    treaty = expected["treaty"]
    facts = case["facts"]

    conditions = []

    ownership = facts.get("ownership_percent")
    if ownership is not None:
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.minimum_ownership,
                operator=">=",
                value=str(ownership),
                unit="%",
            )
        )

    holding_days = facts.get("holding_days")
    if holding_days is not None:
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.minimum_holding_period,
                operator=">=",
                value=str(holding_days),
                unit="days",
            )
        )

    beneficial_owner = facts.get("beneficial_owner")
    if beneficial_owner is not None:
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.beneficial_owner,
                operator="==",
                value=str(beneficial_owner).lower(),
            )
        )

    return Rule(
        article=int(treaty["article"]),
        transaction_type=case["income_type"].rstrip("s"),
        rates=[
            WHTRate(
                rate=float(treaty["rate"]),
                conditions=conditions,
            )
        ],
    )


def build_context(case):
    facts = case["facts"]

    return {
        "ownership": facts.get("ownership_percent"),
        "holding_period_days": facts.get("holding_days"),
        "beneficial_owner": facts.get("beneficial_owner"),
        "listed_company": facts.get("listed_company"),
    }


@pytest.mark.parametrize("case", load_cases())
def test_reference_case_structure(case):
    required = {
        "id",
        "payer_country",
        "recipient_country",
        "income_type",
        "facts",
        "expected",
        "verified_sources",
        "status",
    }

    assert required.issubset(case)

    expected = case["expected"]
    assert "domestic_rate" in expected
    assert "treaty" in expected
    assert "documentation" in expected
    assert "conclusion" in expected

    treaty = expected["treaty"]
    assert "article" in treaty
    assert "paragraph" in treaty
    assert isinstance(treaty["rate"], (int, float))

    assert case["status"] in {"draft", "reviewed", "verified"}
    assert case["verified_sources"]


@pytest.mark.parametrize("case", load_cases())
def test_reference_case_decision_engine(case):
    rule = build_rule(case)
    context = build_context(case)

    result = evaluate(rule, context)

    expected_rate = float(case["expected"]["treaty"]["rate"])

    assert result.requires_review is False
    assert result.eligible is True
    assert result.rate == expected_rate
