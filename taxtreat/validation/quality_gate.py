from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = (
    "payer",
    "recipient",
    "income_type",
    "domestic_rate",
    "treaty_rate",
    "effective_rate",
    "treaty_article",
    "treaty_source",
    "domestic_source",
)


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        value = record.get(field)

        if value is None or value == "":
            errors.append(f"Missing field: {field}")

    treaty_rate = record.get("treaty_rate")
    domestic_rate = record.get("domestic_rate")
    effective_rate = record.get("effective_rate")

    if (
        isinstance(treaty_rate, (int, float))
        and isinstance(domestic_rate, (int, float))
        and isinstance(effective_rate, (int, float))
    ):
        expected = min(treaty_rate, domestic_rate)

        if effective_rate != expected:
            errors.append(
                f"Effective rate should equal min({treaty_rate}, {domestic_rate}) = {expected}"
            )

    confidence = record.get("confidence")

    if isinstance(confidence, (int, float)):
        if confidence < 90 and not record.get("manual_review"):
            errors.append(
                "Confidence below threshold but manual_review=False"
            )

    return errors
