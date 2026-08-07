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


def _pair_id(
    source_country: str,
    recipient_country: str,
) -> str:
    return (
        f"{source_country.upper()}-"
        f"{recipient_country.upper()}"
    )


def _fact_available(
    field: str,
    facts: dict[str, Any],
    *,
    recipient_country: str,
) -> bool:
    if field == "recipient_tax_residence":
        return bool(
            facts.get("recipient_tax_residence")
            or recipient_country
        )

    if field == "beneficial_owner_confirmed":
        return (
            facts.get("beneficial_owner_confirmed")
            is not None
            or facts.get("beneficial_owner")
            is not None
        )

    return facts.get(field) is not None


def evaluate_runtime_gate(
    *,
    source_country: str,
    recipient_country: str,
    income_type: str,
    transaction_date: date,
    facts: dict[str, Any],
    review_path: str | Path = DEFAULT_FINAL_LEGAL_REVIEW,
) -> RuntimeGateResult:
    review = _load_final_legal_review(
        review_path
    )

    records = {
        record["treaty_pair_id"]: record
        for record in review.get(
            "records",
            [],
        )
    }

    pair_id = _pair_id(
        source_country,
        recipient_country,
    )

    record = records.get(pair_id)

    if record is None:
        return RuntimeGateResult(
            applies=False,
            allowed=True,
            missing_facts=[],
        )

    protocol = (
        record.get("protocol_conclusion")
        or {}
    )

    suspension_date = protocol.get(
        "suspension_effective_from"
    )

    if (
        pair_id == "CZ-RU"
        and suspension_date
        and transaction_date
        >= date.fromisoformat(
            suspension_date
        )
    ):
        return RuntimeGateResult(
            applies=True,
            allowed=False,
            missing_facts=[],
            explanation=(
                "Treaty benefits for CZ-RU are blocked "
                "for this transaction date because the "
                "relevant treaty provisions are suspended."
            ),
        )

    gate_model = review.get(
        "domestic_wht_gate_model",
        {},
    )

    required_fields = []

    for item in gate_model.get(
        "common_required_inputs",
        [],
    ):
        field = item.get("field")

        if (
            field
            and field != "payment_date"
        ):
            required_fields.append(
                field
            )

    missing = sorted(
        field
        for field in required_fields
        if not _fact_available(
            field,
            facts,
            recipient_country=recipient_country,
        )
    )

    if missing:
        return RuntimeGateResult(
            applies=True,
            allowed=False,
            missing_facts=missing,
            explanation=(
                "The country-level legal review is complete, "
                "but mandatory transaction-level facts are "
                "missing. Reduced WHT treatment therefore "
                "remains fail-closed."
            ),
        )

    income_key = income_type.lower()

    if income_key in {"dividend", "dividends"}:
        dividend_fields = [
            "ownership_percent",
            "holding_period_months",
            "recipient_is_qualifying_company",
        ]

        dividend_missing = sorted(
            field
            for field in dividend_fields
            if facts.get(field) is None
        )

        if dividend_missing:
            return RuntimeGateResult(
                applies=True,
                allowed=False,
                missing_facts=dividend_missing,
                explanation=(
                    "Dividend treatment requires transaction-specific "
                    "ownership, holding-period and qualifying-company facts."
                ),
            )

    elif income_key == "interest":
        interest_fields = [
            "related_party_status",
        ]

        interest_missing = sorted(
            field
            for field in interest_fields
            if facts.get(field) is None
        )

        if interest_missing:
            return RuntimeGateResult(
                applies=True,
                allowed=False,
                missing_facts=interest_missing,
                explanation=(
                    "Interest treatment requires transaction-specific "
                    "related-party eligibility facts."
                ),
            )

    elif income_key in {"royalty", "royalties"}:
        royalty_fields = [
            "royalty_classification",
        ]

        royalty_missing = sorted(
            field
            for field in royalty_fields
            if facts.get(field) is None
        )

        if royalty_missing:
            return RuntimeGateResult(
                applies=True,
                allowed=False,
                missing_facts=royalty_missing,
                explanation=(
                    "Royalty treatment requires a transaction-specific "
                    "royalty classification."
                ),
            )

    return RuntimeGateResult(
        applies=True,
        allowed=True,
        missing_facts=[],
    )
