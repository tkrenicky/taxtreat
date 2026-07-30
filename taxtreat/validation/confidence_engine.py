from __future__ import annotations

from typing import Any


def calculate_confidence(record: dict[str, Any]) -> dict[str, Any]:
    """
    Calculates confidence score (0-100) and whether manual review is required.
    """

    score = 100
    reasons: list[str] = []

    if not record.get("treaty_rate"):
        score -= 35
        reasons.append("Missing treaty rate")

    if not record.get("domestic_rate"):
        score -= 20
        reasons.append("Missing domestic rate")

    if not record.get("treaty_source"):
        score -= 15
        reasons.append("Missing treaty source")

    if not record.get("domestic_source"):
        score -= 15
        reasons.append("Missing domestic source")

    if not record.get("treaty_article"):
        score -= 10
        reasons.append("Missing treaty article")

    if record.get("parser_warnings"):
        score -= 20
        reasons.append("Parser warnings")

    score = max(0, min(score, 100))

    return {
        **record,
        "confidence": score,
        "manual_review": score < 90,
        "confidence_reasons": reasons,
    }
