from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REVIEW_DECISIONS = ("not_reviewed", "approve", "correct", "escalate")
PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "STANDARD": 2}


def _index_by_partner(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not payload:
        return {}
    return {
        str(row.get("partner_label") or ""): row
        for row in payload.get("partners", [])
        if row.get("partner_label")
    }


def build_human_review_pack(
    review_queue: dict[str, Any],
    *,
    royalty_audit: dict[str, Any] | None = None,
    language_evidence: dict[str, Any] | None = None,
    article_reconciliation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_country = str(review_queue.get("source_country") or "").strip().upper()
    scopes = review_queue.get("scopes")
    if not source_country:
        raise ValueError("Human-review queue is missing source_country")
    if review_queue.get("status") != "review_queue_not_released":
        raise ValueError("Human-review pack requires an unreleased review queue")
    if not isinstance(scopes, list) or not scopes:
        raise ValueError("Human-review queue contains no scopes")

    royalty_by_partner = _index_by_partner(royalty_audit)
    language_by_partner = _index_by_partner(language_evidence)
    reconciliation_by_partner = _index_by_partner(article_reconciliation)

    rows: list[dict[str, Any]] = []
    for scope in scopes:
        partner = str(scope.get("partner_label") or "").strip()
        income_type = str(scope.get("income_type") or "").strip()
        if not partner or not income_type:
            raise ValueError("Human-review scope requires partner_label and income_type")

        risk_reasons: list[str] = []
        candidate_rates: list[Any] = []
        ownership_thresholds: list[Any] = []
        article_number: int | None = None
        unique_variant_count = 0

        if income_type == "royalty" and partner in royalty_by_partner:
            royalty = royalty_by_partner[partner]
            risk_reasons = list(royalty.get("machine_risk_reasons") or [])
            candidate_rates = list(royalty.get("rate_candidates_machine") or [])
            ownership_thresholds = list(royalty.get("ownership_threshold_tokens_machine") or [])
            numbers = list(royalty.get("royalty_article_numbers_machine") or [])
            article_number = numbers[0] if len(numbers) == 1 else None

        reconciliation = reconciliation_by_partner.get(partner, {})
        if article_number is None:
            expected_number = {"dividend": 10, "interest": 11, "royalty": 12}.get(income_type)
            if expected_number is not None:
                article_number = expected_number
        for article in reconciliation.get("articles", []) or []:
            if article.get("article_number") == article_number:
                unique_variant_count = int(article.get("unique_text_variant_count") or 0)
                break

        if risk_reasons:
            priority = "HIGH"
            review_reason = "; ".join(risk_reasons)
        elif unique_variant_count > 1:
            priority = "MEDIUM"
            review_reason = f"{unique_variant_count} text variants require controlling-instrument review"
        else:
            priority = "STANDARD"
            review_reason = "Routine controlling-text confirmation"

        language = language_by_partner.get(partner, {})
        coverage = language.get("language_evidence_coverage_machine") or {}
        step4 = language.get("step4_web_wording_readiness") or {}

        rows.append(
            {
                "source_country": source_country,
                "partner_label": partner,
                "income_type": income_type,
                "article_number_machine": article_number,
                "review_priority": priority,
                "machine_review_reason": review_reason,
                "machine_risk_reasons": risk_reasons,
                "candidate_rates_percent_machine": candidate_rates,
                "ownership_thresholds_percent_machine": ownership_thresholds,
                "unique_text_variant_count_machine": unique_variant_count,
                "machine_mli_flag": scope.get("machine_mli_flag") is True,
                "machine_status_instrument_flag": scope.get("machine_status_instrument_flag") is True,
                "official_source_urls": list((scope.get("instrument_chain") or {}).get("official_links") or []),
                "german_official_source_candidate_available": coverage.get("german_official_source_candidate_available") is True,
                "english_official_source_candidate_available": coverage.get("english_official_source_candidate_available") is True,
                "step4_de_wording_ready": step4.get("de") is True,
                "step4_en_wording_ready": step4.get("en") is True,
                "reviewer_decision": "not_reviewed",
                "reviewer_corrected_conclusion": None,
                "reviewer_notes": None,
                "reviewer_evidence_references": [],
                "reviewer_name": None,
                "reviewed_at": None,
                "independent_approval_status": "not_started",
                "promotable_to_canonical": False,
            }
        )

    rows.sort(key=lambda row: (PRIORITY_ORDER[row["review_priority"]], row["partner_label"], row["income_type"]))
    high = sum(row["review_priority"] == "HIGH" for row in rows)
    medium = sum(row["review_priority"] == "MEDIUM" for row in rows)

    return {
        "schema_version": 1,
        "source_country": source_country,
        "status": "human_review_pack_not_reviewed_not_released",
        "scope_count": len(rows),
        "high_priority_scope_count": high,
        "medium_priority_scope_count": medium,
        "standard_scope_count": len(rows) - high - medium,
        "policy": {
            "machine_output_is_not_legal_approval": True,
            "human_primary_review_required": True,
            "independent_approval_required": True,
            "reviewer_decision_values": list(REVIEW_DECISIONS),
            "machine_translation_never_establishes_authentic_treaty_wording": True,
            "canonical_materialization_requires_approved_review": True,
            "fail_closed": True,
        },
        "rows": rows,
    }


def write_csv(pack: dict[str, Any], path: Path) -> None:
    fields = [
        "source_country",
        "partner_label",
        "income_type",
        "article_number_machine",
        "review_priority",
        "machine_review_reason",
        "candidate_rates_percent_machine",
        "ownership_thresholds_percent_machine",
        "unique_text_variant_count_machine",
        "machine_mli_flag",
        "machine_status_instrument_flag",
        "german_official_source_candidate_available",
        "english_official_source_candidate_available",
        "step4_de_wording_ready",
        "step4_en_wording_ready",
        "official_source_urls",
        "reviewer_decision",
        "reviewer_corrected_conclusion",
        "reviewer_notes",
        "reviewer_evidence_references",
        "reviewer_name",
        "reviewed_at",
        "independent_approval_status",
        "promotable_to_canonical",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in pack["rows"]:
            output = dict(row)
            for field in (
                "candidate_rates_percent_machine",
                "ownership_thresholds_percent_machine",
                "official_source_urls",
                "reviewer_evidence_references",
            ):
                output[field] = " | ".join(str(value) for value in output.get(field) or [])
            writer.writerow({field: output.get(field) for field in fields})


def _load_optional(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--royalty-audit", type=Path)
    parser.add_argument("--language-evidence", type=Path)
    parser.add_argument("--article-reconciliation", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    pack = build_human_review_pack(
        queue,
        royalty_audit=_load_optional(args.royalty_audit),
        language_evidence=_load_optional(args.language_evidence),
        article_reconciliation=_load_optional(args.article_reconciliation),
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(pack, args.output_csv)
    print(
        "Human review pack:",
        pack["source_country"],
        pack["scope_count"],
        "scopes /",
        pack["high_priority_scope_count"],
        "high /",
        pack["medium_priority_scope_count"],
        "medium",
    )


if __name__ == "__main__":
    main()
