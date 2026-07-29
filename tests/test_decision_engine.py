import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taxtreat.engine.decision_engine import evaluate
from taxtreat.engine.models import ConditionType, Rule, WHTCondition, WHTRate


def build_rule() -> Rule:
    return Rule(
        article=10,
        transaction_type="dividend",
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                        unit="%",
                        description="minimum ownership",
                    )
                ],
                legal_basis="Art 10",
                priority=0,
            ),
            WHTRate(
                rate=15.0,
                conditions=[],
                legal_basis="default",
                priority=1,
            ),
        ],
    )


if __name__ == "__main__":
    rule = build_rule()

    scenarios = [
        ("ownership = 25, beneficial_owner = True", {"ownership": 25, "beneficial_owner": True}),
        ("ownership = 5, beneficial_owner = True", {"ownership": 5, "beneficial_owner": True}),
        ("beneficial_owner = True, ownership missing", {"beneficial_owner": True}),
    ]

    for label, facts in scenarios:
        result = evaluate(rule, facts)
        print(f"Scenario: {label}")
        print(f"  withholding_rate={result.withholding_rate}")
        print(f"  eligible={result.eligible}")
        print(f"  requires_review={result.requires_review}")
        print(f"  missing_facts={result.missing_facts}")
        print(f"  explanation={result.explanation}")
        print()
