import re

from taxtreat.engine.models import ConditionType, Rule, WHTCondition, WHTRate

RATE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|procent)")


def extract_conditions(text: str) -> list[WHTCondition]:
    if not text:
        return []

    conditions: list[WHTCondition] = []
    lowered = text.lower()

    ownership_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|procent)", lowered)
    if ownership_match:
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.minimum_ownership,
                operator=">=",
                value=ownership_match.group(1),
                unit="%",
                description="minimum ownership",
                source_text=text,
            )
        )

    if re.search(r"(?:holding period|doba držení|doba drzen)", lowered):
        period_match = re.search(r"(\d+)\s*(?:months|měsíců|mesicu|month|months)", lowered)
        if period_match:
            conditions.append(
                WHTCondition(
                    condition_type=ConditionType.minimum_holding_period,
                    operator=">=",
                    value=period_match.group(1),
                    unit="months",
                    description="minimum holding period",
                    source_text=text,
                )
            )

    if re.search(r"(?:beneficial owner|oprávněný vlastník|opravneny vlastnik)", lowered):
        conditions.append(
            WHTCondition(
                condition_type=ConditionType.beneficial_owner,
                operator="=",
                value="true",
                description="beneficial owner required",
                source_text=text,
            )
        )

    return conditions


def dividend_rule(article_text: str):
    rule = Rule(
        article=10,
        transaction_type="dividend",
        extraction_status="needs_review",
        source_text=article_text,
    )

    raw_rates = [float(x) for x in RATE_RE.findall(article_text)]
    if raw_rates:
        conditions = extract_conditions(article_text)
        rule.rates = [
            WHTRate(
                rate=rate,
                conditions=[] if len(raw_rates) > 1 else conditions,
                legal_basis=None,
                source_text=article_text,
                source_paragraph=None,
                priority=index,
            )
            for index, rate in enumerate(raw_rates)
        ]
        rule.rate = rule.rates[0].rate
        rule.conditions = conditions
        rule.extraction_status = "confirmed" if len(raw_rates) == 1 else "needs_review"
    else:
        rule.rate = None

    return rule
