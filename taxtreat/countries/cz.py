from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any


def apply_rule_overlays(
    *,
    scoped_rules: list[Any],
    income_type: str,
    transaction_date: date,
) -> list[Any]:
    """Apply Czech source-country historical rule overlays.

    The released Stage 6 projection uses 2026 as a source-version date.
    For Czech dividends, the verified historical Section 19 window from
    1 July 2008 must therefore be represented without projecting current
    conditions into earlier periods.
    """
    rules = list(scoped_rules)

    if (
        income_type == "dividend"
        and date(2008, 7, 1) <= transaction_date < date(2026, 4, 1)
    ):
        historical_relief = []
        for rule in rules:
            if rule.legal_layer != "eu_relief" or rule.effect != "rate":
                continue

            historical_relief.append(
                replace(
                    rule,
                    rule_id=f"{rule.rule_id}-HIST-2008",
                    effective_from=date(2008, 7, 1),
                    effective_to=date(2026, 3, 31),
                    source_id="CZ-ZDP-2008-07-01-HISTORICAL-ESBIRKA",
                    source_url="https://e-sbirka.gov.cz/sb/1992/586/2008-07-01",
                    source_text=(
                        "Historical Czech Income Taxes Act as of 1 July 2008: "
                        "domestic parent-subsidiary dividend exemption under "
                        "Section 19 with a 10% participation threshold and "
                        "12-month holding period."
                    ),
                    source_excerpt_hash=None,
                    evidence_source_ids=[
                        *rule.evidence_source_ids,
                        "CZ-ZDP-2008-07-01-HISTORICAL-ESBIRKA",
                    ],
                    verification_authority=(
                        "official_historical_statute_runtime_equivalence"
                    ),
                    review_package_sha256=None,
                    approval_dataset_release=None,
                    approval_created_at=None,
                )
            )

        rules.extend(historical_relief)

    return rules
