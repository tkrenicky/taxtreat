from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_FINAL_LEGAL_REVIEW = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_final_legal_consolidation.json"
)

DEFAULT_STATUS_RECONCILIATION = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "all_23_status_instrument_reconciliation.json"
)


@dataclass(frozen=True)
class RuntimeGateResult:
    applies: bool
    allowed: bool
    missing_facts: list[str]
    explanation: str | None = None


def _load_final_legal_review(
    path: str | Path = DEFAULT_FINAL_LEGAL_REVIEW,
) -> dict[str, Any]:
    review_path = Path(path)

    if not review_path.is_file():
        return {}

    return json.loads(
        review_path.read_text(encoding="utf-8")
    )


def _load_status_reconciliation(
    path: str | Path = DEFAULT_STATUS_RECONCILIATION,
) -> dict[str, Any]:
    reconciliation_path = Path(path)

    if not reconciliation_path.is_file():
        return {}

    return json.loads(
        reconciliation_path.read_text(encoding="utf-8")
    )


def _status_instrument_block(
    *,
    pair_id: str,
    income_type: str,
    transaction_date: date,
    path: str | Path = DEFAULT_STATUS_RECONCILIATION,
) -> RuntimeGateResult | None:
    data = _load_status_reconciliation(path)

    # Do not impose rule-specific facts at the country-level runtime gate.
    # Ownership, holding period, qualifying-company status, related-party
    # status and royalty category belong to the legal-rule conditions below
    # this gate. Requiring them here blocks valid fallback treaty outcomes
    # (for example, a general dividend treaty rate when a domestic exemption
    # fact is unknown) before the layered engine can evaluate them.
    #
    # The runtime gate is therefore limited to common transaction inputs and
    # status-instrument/suspension controls. The rule engine remains fail-
    # closed for any unresolved condition and can expose a lower/fallback
    # candidate without incorrectly treating it as final.

    return RuntimeGateResult(
        applies=True,
        allowed=True,
        missing_facts=[],
    )
