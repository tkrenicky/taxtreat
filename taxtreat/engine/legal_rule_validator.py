from __future__ import annotations

import hashlib
import re

from taxtreat.engine.legal_rule_engine import (
    LegalRule,
    TaxTreatment,
    _SUPPORTED_OPERATORS,
    resolve_tax_treatment,
)


_ALLOWED_EFFECTS = {"rate", "exclude", "eligibility_gate", "review_gate"}
_ALLOWED_INCOME_TYPES = {"dividend", "interest", "royalty"}
_ALLOWED_INSTRUMENTS = {
    "treaty",
    "protocol",
    "mli",
    "domestic_law",
    "eu_directive",
}
_ALLOWED_LAYERS = {
    "domestic",
    "treaty",
    "protocol",
    "mli",
    "eu_relief",
}
_ALLOWED_STATUSES = {"verified", "needs_review", "rejected"}
_ALLOWED_FACT_SOURCES = {"transaction", "legal", "determination"}
_VERIFICATION_FIELDS = (
    "effective_from",
    "source_id",
    "source_url",
    "source_excerpt_hash",
    "reviewer_id",
    "reviewed_at",
    "approved_by",
    "approved_at",
    "dataset_release",
)


def validate_legal_rules(rules: list[LegalRule]) -> list[str]:
    issues: list[str] = []
    rule_ids = [rule.rule_id for rule in rules]
    rules_by_id = {rule.rule_id: rule for rule in rules}

    for rule_id in sorted(set(rule_ids)):
        if rule_ids.count(rule_id) > 1:
            issues.append(f"Duplicate legal-rule id: {rule_id}")

    for rule in rules:
        prefix = f"Rule {rule.rule_id or '<missing id>'}:"

        if not rule.rule_id:
            issues.append(f"{prefix} rule_id is required.")
        if rule.income_type not in _ALLOWED_INCOME_TYPES:
            issues.append(f"{prefix} unsupported income_type.")
        if not rule.source_country or not rule.recipient_country:
            issues.append(f"{prefix} country scope is incomplete.")
        if rule.legal_instrument not in _ALLOWED_INSTRUMENTS:
            issues.append(f"{prefix} unsupported legal_instrument.")
        if rule.legal_layer not in _ALLOWED_LAYERS:
            issues.append(f"{prefix} unsupported legal_layer.")
        if rule.effect not in _ALLOWED_EFFECTS:
            issues.append(f"{prefix} unsupported effect.")
        if rule.verification_status not in _ALLOWED_STATUSES:
            issues.append(f"{prefix} unsupported verification_status.")
        if rule.verification_status == "verified":
            stage6_governance = (
                rule.verification_authority
                == "stage6_governance_policy"
            )

            if stage6_governance:
                stage6_required = (
                    "effective_from",
                    "source_id",
                    "source_url",
                    "source_excerpt_hash",
                    "review_package_sha256",
                    "approval_dataset_release",
                    "approval_created_at",
                    "dataset_release",
                )

                missing_stage6 = [
                    field_name
                    for field_name in stage6_required
                    if getattr(rule, field_name) in (None, "")
                ]

                if missing_stage6:
                    issues.append(
                        f"{prefix} Stage 6 verified rule lacks "
                        "governance provenance: "
                        + ", ".join(missing_stage6)
                        + "."
                    )

                if (
                    rule.review_package_sha256
                    and not re.fullmatch(
                        r"[0-9a-fA-F]{64}",
                        rule.review_package_sha256,
                    )
                ):
                    issues.append(
                        f"{prefix} review_package_sha256 must be "
                        "full SHA-256."
                    )

                # Stage 6 production approval is deterministic
                # governance over an already completed primary
                # human review. It is explicitly not a second
                # human review and therefore must not fabricate
                # per-rule reviewer / approver identities.
            else:
                missing_verification = [
                    field_name
                    for field_name in _VERIFICATION_FIELDS
                    if getattr(rule, field_name) in (None, "")
                ]

                if missing_verification:
                    issues.append(
                        f"{prefix} verified rule lacks "
                        "provenance/approval: "
                        + ", ".join(missing_verification)
                        + "."
                    )

                if (
                    rule.reviewer_id is not None
                    and rule.approved_by is not None
                    and rule.reviewer_id == rule.approved_by
                ):
                    issues.append(
                        f"{prefix} reviewer and approver must "
                        "be independent."
                    )

            if rule.source_excerpt_hash and not re.fullmatch(
                r"[0-9a-fA-F]{64}",
                rule.source_excerpt_hash,
            ):
                issues.append(
                    f"{prefix} source_excerpt_hash must be full SHA-256."
                )
            if rule.source_url and not rule.source_url.startswith("https://"):
                issues.append(f"{prefix} source_url must use HTTPS.")

        if not isinstance(rule.priority, int) or isinstance(rule.priority, bool):
            issues.append(f"{prefix} priority must be an integer.")
        elif rule.priority < 0:
            issues.append(f"{prefix} priority cannot be negative.")

        if rule.effect == "rate":
            if (
                not isinstance(rule.rate, (int, float))
                or isinstance(rule.rate, bool)
            ):
                issues.append(f"{prefix} rate must be numeric.")
            elif not 0 <= float(rule.rate) <= 100:
                issues.append(f"{prefix} rate must be between 0 and 100.")
            treatment = resolve_tax_treatment(rule)
            if (
                treatment in {
                    TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION,
                    TaxTreatment.DOMESTIC_EXEMPTION,
                }
                and rule.rate != 0
            ):
                issues.append(
                    f"{prefix} non-taxing treatment must use structural "
                    "rate 0 in the rule catalog."
                )

        if rule.effect == "exclude" and rule.rate is not None:
            issues.append(f"{prefix} exclusion rule must not contain a rate.")

        if rule.effect == "review_gate" and rule.rate is not None:
            issues.append(f"{prefix} review gate must not contain a rate.")

        if rule.effect == "eligibility_gate":
            if rule.rate is not None:
                issues.append(f"{prefix} eligibility gate must not contain a rate.")
            if not rule.applies_to_layers:
                issues.append(
                    f"{prefix} eligibility gate must identify affected layers."
                )
            invalid_layers = sorted(
                set(rule.applies_to_layers).difference(_ALLOWED_LAYERS)
            )
            if invalid_layers:
                issues.append(
                    f"{prefix} eligibility gate has unsupported target layers."
                )

        if rule.verification_status in {"verified", "needs_review"}:
            candidate_fields = (
                "effective_from",
                "source_id",
                "source_url",
                "source_text",
                "source_excerpt_hash",
                "dataset_release",
            )
            missing_candidate_fields = [
                name
                for name in candidate_fields
                if getattr(rule, name) in (None, "")
            ]
            if missing_candidate_fields:
                issues.append(
                    f"{prefix} reviewable rule lacks date/provenance: "
                    + ", ".join(missing_candidate_fields)
                    + "."
                )
            if not rule.evidence_source_ids:
                issues.append(
                    f"{prefix} reviewable rule lacks evidence_source_ids."
                )

        if rule.source_text and rule.source_excerpt_hash:
            actual_hash = hashlib.sha256(
                rule.source_text.encode("utf-8")
            ).hexdigest()
            if actual_hash != rule.source_excerpt_hash.lower():
                issues.append(
                    f"{prefix} source_excerpt_hash does not match source_text."
                )

        if (
            rule.effective_from is not None
            and rule.effective_to is not None
            and rule.effective_to < rule.effective_from
        ):
            issues.append(f"{prefix} effective_to precedes effective_from.")

        for condition in rule.conditions:
            if not condition.fact:
                issues.append(f"{prefix} condition fact is required.")
            if condition.operator not in _SUPPORTED_OPERATORS:
                issues.append(
                    f"{prefix} unsupported condition operator "
                    f"{condition.operator!r}."
                )
            if condition.fact_source not in _ALLOWED_FACT_SOURCES:
                issues.append(
                    f"{prefix} unsupported condition fact_source "
                    f"{condition.fact_source!r}."
                )

        if rule.overrides_rule_id is None:
            continue

        target = rules_by_id.get(rule.overrides_rule_id)
        if target is None:
            issues.append(f"{prefix} overridden rule does not exist.")
            continue

        if rule.overrides_rule_id == rule.rule_id:
            issues.append(f"{prefix} rule cannot override itself.")

        source_scope = (
            rule.income_type,
            rule.source_country,
            rule.recipient_country,
        )
        target_scope = (
            target.income_type,
            target.source_country,
            target.recipient_country,
        )
        if source_scope != target_scope:
            issues.append(f"{prefix} override target has different scope.")

        if rule.priority >= target.priority:
            issues.append(
                f"{prefix} overriding rule must have higher precedence."
            )

    return issues
