from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from taxtreat.engine.legal_rule_engine import LegalCondition, LegalRule
from taxtreat.engine.legal_rule_validator import validate_legal_rules


def _parse_date(value: str | None) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(value)


def load_legal_rules(path: str | Path) -> list[LegalRule]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_rules = payload.get("rules")

    if not isinstance(raw_rules, list):
        raise ValueError("Legal-rule file must contain a 'rules' list.")

    rules: list[LegalRule] = []
    seen_ids: set[str] = set()

    for raw_rule in raw_rules:
        rule_id = raw_rule["rule_id"]
        if rule_id in seen_ids:
            raise ValueError(f"Duplicate legal-rule id: {rule_id}")
        seen_ids.add(rule_id)

        conditions = [
            LegalCondition(
                fact=condition["fact"],
                operator=condition["operator"],
                value=condition.get("value"),
                fact_source=condition.get("fact_source", "transaction"),
            )
            for condition in raw_rule.get("conditions", [])
        ]

        rules.append(
            LegalRule(
                rule_id=rule_id,
                income_type=raw_rule["income_type"],
                source_country=raw_rule["source_country"],
                recipient_country=raw_rule["recipient_country"],
                legal_instrument=raw_rule["legal_instrument"],
                legal_layer=raw_rule.get(
                    "legal_layer",
                    raw_rule["legal_instrument"],
                ),
                article=raw_rule.get("article"),
                paragraph=raw_rule.get("paragraph"),
                rate=raw_rule.get("rate"),
                priority=raw_rule.get("priority", 100),
                conditions=conditions,
                effect=raw_rule.get("effect", "rate"),
                effective_from=_parse_date(raw_rule.get("effective_from")),
                effective_to=_parse_date(raw_rule.get("effective_to")),
                overrides_rule_id=raw_rule.get("overrides_rule_id"),
                verification_status=raw_rule.get(
                    "verification_status",
                    "needs_review",
                ),
                source_text=raw_rule.get("source_text"),
                source_id=raw_rule.get("source_id"),
                source_url=raw_rule.get("source_url"),
                source_excerpt_hash=raw_rule.get("source_excerpt_hash"),
                reviewer_id=raw_rule.get("reviewer_id"),
                reviewed_at=_parse_date(raw_rule.get("reviewed_at")),
                approved_by=raw_rule.get("approved_by"),
                approved_at=_parse_date(raw_rule.get("approved_at")),
                verification_authority=raw_rule.get(
                    "verification_authority"
                ),
                review_package_sha256=raw_rule.get(
                    "review_package_sha256"
                ),
                approval_dataset_release=raw_rule.get(
                    "approval_dataset_release"
                ),
                approval_created_at=_parse_date(
                    raw_rule.get("approval_created_at")
                ),
                dataset_release=raw_rule.get("dataset_release"),
                evidence_source_ids=list(
                    raw_rule.get("evidence_source_ids", [])
                ),
                applies_to_layers=list(
                    raw_rule.get("applies_to_layers", [])
                ),
            )
        )

    country_pair = payload.get("country_pair") or {}
    for rule in rules:
        if (
            rule.source_country != country_pair.get("source_country")
            or rule.recipient_country != country_pair.get("recipient_country")
        ):
            raise ValueError(
                f"Rule {rule.rule_id} does not match top-level country_pair."
            )

    issues = validate_legal_rules(rules)
    if issues:
        raise ValueError("Invalid legal-rule file:\n- " + "\n- ".join(issues))

    return rules
