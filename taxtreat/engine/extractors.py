import re

from taxtreat.engine.models import ConditionType, Rule, WHTCondition, WHTRate


PERCENT_RE = re.compile(
    r"(?P<value>\d+(?:[.,]\d+)?)\s*(?:%|percent|per\s+cent|procent(?:a|o|u|y)?|proc\.)",
    re.IGNORECASE,
)

CLAUSE_MARKER_RE = re.compile(
    r"(?:^|\n|(?<=[;:]))\s*(?:\(?[a-z]\)|\(?\d+\)|\d+\.)\s*",
    re.IGNORECASE,
)

BENEFICIAL_OWNER_RE = re.compile(
    r"(?:beneficial\s+owner|beneficially\s+owned|"
    r"skutečný\s+vlastník|oprávněný\s+vlastník|"
    r"skutecny\s+vlastnik|opravneny\s+vlastnik)",
    re.IGNORECASE,
)

OWNERSHIP_BEFORE_RE = re.compile(
    r"(?:holds?|owns?|controls?|participation|interest|"
    r"vlastní|drží|ovládá|podíl|účast)",
    re.IGNORECASE,
)

OWNERSHIP_AFTER_RE = re.compile(
    r"(?:capital|voting\s+power|shares?|participation|interest|"
    r"základní(?:ho|m)?\s+kapitál(?:u|e)?|hlasovac(?:ích|í)\s+práv|"
    r"podíl(?:u|em)?|účast)",
    re.IGNORECASE,
)

HOLDING_PERIOD_RE = re.compile(
    r"(?:(?:for\s+(?:an?\s+)?(?:uninterrupted|continuous)?\s*period\s+of\s+at\s+least)|"
    r"(?:held\s+(?:for\s+)?at\s+least)|"
    r"(?:po\s+dobu\s+alespoň)|"
    r"(?:po\s+dobu\s+nejméně)|"
    r"(?:nepřetržitě\s+po\s+dobu\s+alespoň)|"
    r"(?:nepřetržitě\s+po\s+dobu\s+nejméně)|"
    r"(?:doba\s+držení.{0,35}?(?:alespoň|nejméně)))\s*"
    r"(?P<value>\d+)\s*"
    r"(?P<unit>days?|months?|years?|dn(?:ů|y|i)?|měsíc(?:e|ů)?|rok(?:y|ů)?)",
    re.IGNORECASE | re.DOTALL,
)


def _to_float(value: str) -> float:
    return float(value.replace(",", "."))


def _normalise_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _normalise_unit(unit: str) -> str:
    lowered = unit.lower()
    if lowered.startswith(("day", "dn")):
        return "days"
    if lowered.startswith(("month", "měsíc")):
        return "months"
    return "years"


def _deduplicate_conditions(conditions: list[WHTCondition]) -> list[WHTCondition]:
    result: list[WHTCondition] = []
    seen: set[tuple] = set()

    for condition in conditions:
        key = (
            condition.condition_type,
            condition.operator,
            str(condition.value),
            condition.unit,
        )
        if key not in seen:
            seen.add(key)
            result.append(condition)

    return result


def _is_ownership_percentage(text: str, match: re.Match) -> bool:
    before = text[max(0, match.start() - 60):match.start()]
    after = text[match.end():min(len(text), match.end() + 55)]

    return bool(
        OWNERSHIP_BEFORE_RE.search(before)
        or OWNERSHIP_AFTER_RE.search(after)
    )


def _ownership_values(text: str) -> list[float]:
    values: list[float] = []

    for match in PERCENT_RE.finditer(text):
        if _is_ownership_percentage(text, match):
            values.append(_to_float(match.group("value")))

    return values


def extract_conditions(text: str) -> list[WHTCondition]:
    if not text:
        return []

    conditions: list[WHTCondition] = []

    ownership_values = _ownership_values(text)
    if ownership_values:
        value = min(ownership_values)
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.minimum_ownership,
                operator=">=",
                value=_normalise_number(value),
                unit="%",
                description="minimum ownership",
                source_text=text,
            )
        )

    holding_match = HOLDING_PERIOD_RE.search(text)
    if holding_match:
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.minimum_holding_period,
                operator=">=",
                value=holding_match.group("value"),
                unit=_normalise_unit(holding_match.group("unit")),
                description="minimum holding period",
                source_text=text,
            )
        )

    if BENEFICIAL_OWNER_RE.search(text):
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.beneficial_owner,
                operator="==",
                value="true",
                description="beneficial owner required",
                source_text=text,
            )
        )

    return _deduplicate_conditions(conditions)


def _split_clauses(text: str) -> list[str]:
    matches = list(CLAUSE_MARKER_RE.finditer(text))
    if not matches:
        return [text.strip()]

    clauses: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        clause = text[start:end].strip()
        if clause:
            clauses.append(clause)

    return clauses or [text.strip()]


def _rate_candidates(clause: str) -> list[tuple[float, re.Match]]:
    candidates: list[tuple[float, re.Match]] = []

    for match in PERCENT_RE.finditer(clause):
        if _is_ownership_percentage(clause, match):
            continue
        candidates.append((_to_float(match.group("value")), match))

    return candidates


def _extract_rate_clauses(text: str) -> list[tuple[float, str]]:
    clauses = _split_clauses(text)
    extracted: list[tuple[float, str]] = []

    if len(clauses) > 1:
        for clause in clauses:
            candidates = _rate_candidates(clause)
            if not candidates:
                continue
            rate, _ = candidates[0]
            extracted.append((rate, clause))

    if extracted:
        return extracted

    # Treaty texts without clear a)/b) formatting:
    # identify every non-ownership percentage and create a local source segment.
    candidates = _rate_candidates(text)
    for index, (rate, match) in enumerate(candidates):
        start = 0 if index == 0 else candidates[index - 1][1].end()
        end = candidates[index + 1][1].start() if index + 1 < len(candidates) else len(text)
        extracted.append((rate, text[start:end].strip()))

    return extracted


def dividend_rule(article_text: str) -> Rule:
    rule = Rule(
        article=10,
        transaction_type="dividend",
        extraction_status="needs_review",
        source_text=article_text,
    )

    if not article_text or not article_text.strip():
        rule.rate = None
        rule.extraction_status = "incomplete"
        return rule

    extracted = _extract_rate_clauses(article_text)
    if not extracted:
        rule.rate = None
        rule.extraction_status = "incomplete"
        return rule

    global_conditions = extract_conditions(article_text)
    global_beneficial_owner = [
        condition
        for condition in global_conditions
        if condition.condition_type == ConditionType.beneficial_owner
    ]

    rates: list[WHTRate] = []
    seen: set[tuple] = set()

    for rate, clause in extracted:
        local_conditions = extract_conditions(clause)

        if global_beneficial_owner and not any(
            condition.condition_type == ConditionType.beneficial_owner
            for condition in local_conditions
        ):
            local_conditions.extend(global_beneficial_owner)

        local_conditions = _deduplicate_conditions(local_conditions)
        signature = tuple(
            (
                condition.condition_type,
                condition.operator,
                str(condition.value),
                condition.unit,
            )
            for condition in local_conditions
        )
        key = (rate, signature)
        if key in seen:
            continue
        seen.add(key)

        rates.append(
            WHTRate(
                rate=rate,
                conditions=local_conditions,
                legal_basis="Article 10",
                source_text=clause,
                source_paragraph=None,
                priority=len(rates),
            )
        )

    rule.rates = rates
    rule.rate = rates[0].rate if rates else None
    rule.conditions = global_conditions
    rule.extraction_status = "confirmed" if rates else "incomplete"
    return rule
