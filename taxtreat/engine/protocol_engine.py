from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

from taxtreat.engine.models import ConditionType, Protocol, ProtocolChange, Rule, WHTCondition, WHTRate


class ProtocolEngine:
    def apply(self, rule: Rule, protocols: list[Protocol], effective_date: date | None = None) -> Rule:
        if not protocols:
            return deepcopy(rule)

        effective_date = effective_date or date.today()
        applicable_protocols = [
            protocol
            for protocol in protocols
            if self._is_applicable(protocol, rule, effective_date)
        ]
        applicable_protocols.sort(key=lambda protocol: protocol.effective_date)

        updated_rule = deepcopy(rule)
        for protocol in applicable_protocols:
            for change in protocol.changes:
                self._apply_change(updated_rule, change)

        return updated_rule

    def _is_applicable(self, protocol: Protocol, rule: Rule, effective_date: date) -> bool:
        if protocol.effective_date > effective_date:
            return False
        if protocol.article is not None and protocol.article != rule.article:
            return False
        if protocol.transaction_type is not None and protocol.transaction_type != rule.transaction_type:
            return False
        if protocol.paragraph is not None and protocol.paragraph != rule.paragraph:
            return False
        return True

    def _apply_change(self, rule: Rule, change: ProtocolChange) -> None:
        if change.rate is not None:
            rule.rate = change.rate
            for rate in rule.rates:
                rate.rate = change.rate

        if change.legal_basis is not None:
            rule.legal_basis = change.legal_basis
            for rate in rule.rates:
                rate.legal_basis = change.legal_basis

        if change.add_conditions:
            for condition in change.add_conditions:
                if condition not in rule.conditions:
                    rule.conditions.append(deepcopy(condition))
            for rate in rule.rates:
                for condition in change.add_conditions:
                    if condition not in rate.conditions:
                        rate.conditions.append(deepcopy(condition))

        if change.remove_condition_types:
            rule.conditions = [
                condition
                for condition in rule.conditions
                if condition.condition_type not in change.remove_condition_types
            ]
            for rate in rule.rates:
                rate.conditions = [
                    condition
                    for condition in rate.conditions
                    if condition.condition_type not in change.remove_condition_types
                ]
