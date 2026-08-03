from __future__ import annotations

"""Legacy parser-analysis adapter.

Do not use this module for production decisions. New requests must use
``taxtreat.services.decision.analyze_transaction``.
"""

from dataclasses import dataclass, field
from typing import Any

from taxtreat.db.repository import TreatyRepository
from taxtreat.engine.decision_engine import DecisionResult, evaluate
from taxtreat.engine.models import Rule
from taxtreat.engine.validation import RuleValidator, ValidationResult
from taxtreat.services.rule_builder import RuleBuilder


@dataclass
class AnalysisRequest:
    treaty_id: int
    transaction_type: str
    facts: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisReport:
    treaty_id: int
    transaction_type: str
    rule: Rule | None = None
    validation_result: ValidationResult | None = None
    decision_result: DecisionResult | None = None
    errors: list[str] = field(default_factory=list)


class WHTAnalyzer:
    def __init__(self, repository: TreatyRepository, rule_builder: RuleBuilder | None = None):
        self.repository = repository
        self.rule_builder = rule_builder or RuleBuilder(repository=repository)
        self.validator = RuleValidator()

    def analyze(self, request: AnalysisRequest) -> AnalysisReport:
        report = AnalysisReport(
            treaty_id=request.treaty_id,
            transaction_type=request.transaction_type,
        )

        rules = self.rule_builder.build_rules(request.treaty_id)
        if not rules:
            report.errors.append("No rules could be built for the requested treaty")
            return report

        selected_rule = self._select_rule(rules, request.transaction_type)
        if selected_rule is None:
            report.errors.append(
                f"No rule found for transaction type {request.transaction_type}"
            )
            return report

        report.rule = selected_rule
        report.validation_result = self.validator.validate([selected_rule])
        report.decision_result = evaluate(selected_rule, request.facts)
        return report

    def _select_rule(self, rules: list[Rule], transaction_type: str) -> Rule | None:
        for rule in rules:
            if getattr(rule, "transaction_type", None) == transaction_type:
                return rule
        return None
