from __future__ import annotations

import re
from typing import Literal

IncomeType = Literal["dividend", "interest", "royalty"]

INCOME_PATTERNS: dict[IncomeType, tuple[re.Pattern[str], ...]] = {
    "dividend": (
        re.compile(r"\bdividends?\b", re.IGNORECASE),
        re.compile(r"\bdividenden\b", re.IGNORECASE),
    ),
    "interest": (
        re.compile(r"\binterest\b", re.IGNORECASE),
        re.compile(r"\bzinsen\b", re.IGNORECASE),
    ),
    "royalty": (
        re.compile(r"\broyalt(?:y|ies)\b", re.IGNORECASE),
        re.compile(r"\blizenzgeb(?:ü|ue)hren?\b", re.IGNORECASE),
    ),
}

ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(token: str) -> int:
    value = token.strip().upper()
    if not value or any(char not in ROMAN_VALUES for char in value):
        raise ValueError(f"Invalid Roman numeral: {token}")
    total = 0
    previous = 0
    for char in reversed(value):
        current = ROMAN_VALUES[char]
        if current < previous:
            total -= current
        else:
            total += current
            previous = current
    if total <= 0 or total > 99:
        raise ValueError(f"Unsupported Roman article number: {token}")
    return total


def article_number(token: str) -> int:
    normalized = token.strip().upper()
    if normalized.isdigit():
        number = int(normalized)
        if number <= 0:
            raise ValueError(f"Invalid article number: {token}")
        return number
    return roman_to_int(normalized)


def classify_income(text: str, *, scan_chars: int = 480) -> IncomeType | None:
    if scan_chars <= 0:
        raise ValueError("scan_chars must be positive")
    probe = text[:scan_chars]
    matches: list[tuple[int, IncomeType]] = []
    for income_type, patterns in INCOME_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(probe)
            if match:
                matches.append((match.start(), income_type))
                break
    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    first_position = matches[0][0]
    first_types = {income for position, income in matches if position == first_position}
    if len(first_types) != 1:
        return None
    first_type = matches[0][1]
    # A heading/lead-clause classification must be materially earlier than a
    # competing cross-reference. If two income labels occur nearly together,
    # preserve ambiguity rather than guessing.
    competing = [position for position, income in matches if income != first_type]
    if competing and min(competing) - first_position < 80:
        return None
    return first_type


def expected_oecd_article(income_type: IncomeType) -> int:
    return {"dividend": 10, "interest": 11, "royalty": 12}[income_type]
