from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ConditionType(str, Enum):
    minimum_ownership = "minimum_ownership"
    minimum_holding_period = "minimum_holding_period"
    beneficial_owner = "beneficial_owner"
    permanent_establishment_connection = "permanent_establishment_connection"
    recipient_type = "recipient_type"
    voting_rights = "voting_rights"


@dataclass
class WHTCondition:
    condition_type: ConditionType
    operator: str | None = None
    value: str | None = None
    unit: str | None = None
    description: str | None = None
    source_text: str | None = None
    source_paragraph: str | None = None


@dataclass
class WHTRate:
    rate: float | None = None
    conditions: list[WHTCondition] = field(default_factory=list)
    legal_basis: str | None = None
    source_text: str | None = None
    source_paragraph: str | None = None
    priority: int = 0


@dataclass
class Rule:
    article: int | None = None
    paragraph: str | None = None
    transaction_type: str | None = None
    rate: float | None = None
    rates: list[WHTRate] = field(default_factory=list)
    conditions: list[WHTCondition] = field(default_factory=list)
    legal_basis: str | None = None
    source_text: str | None = None
    extraction_status: str = "needs_review"
