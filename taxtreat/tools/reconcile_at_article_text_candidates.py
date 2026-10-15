from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("artifacts/at/article_candidate_inventory.json")
DEFAULT_OUTPUT = Path("artifacts/at/article_candidate_reconciliation.json")
ARTICLE_NUMBERS = (10, 11, 12)
INCOME_TYPES = ("dividend", "interest", "royalty")
EXPECTED_ARTICLE = {"dividend": 10, "interest": 11, "royalty": 12}


def _review_strategy(candidates: list[dict[str, Any]]) -> str:
    roles = {str(row.get("role_candidate") or "") for row in candidates}
    if not candidates:
        return "no_substantive_candidate_fail_closed"
    if "synthesized_mli_text" in roles and "current_consolidated_view" in roles:
        return "compare_synthesized_mli_to_current_consolidated_and_published_chain"
    if "current_consolidated_view" in roles:
        return "review_current_consolidated_against_published_chain"
    if "synthesized_mli_text" in roles:
        return "review_synthesized_mli_against_published_chain"
    return "resolve_from_published_instruments"


def _candidate_row(source: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_order": source.get("source_order"),
        "final_url": source.get("final_url"),
        "role_candidate": source.get("role_candidate"),
        "source_sha256": source.get("source_sha256"),
        "article_number": candidate.get("article_number"),
        "semantic_income_detected": candidate.get("semantic_income_detected") or candidate.get("semantic_income_candidate"),
        "text_sha256": candidate.get("text_sha256"),
        "character_count": candidate.get("character_count"),
        "artifact_path": candidate.get("artifact_path"),
        "quality_flags": candidate.get("quality_flags") or [],
    }


def _all_candidates(partner: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    substantive: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for source in partner.get("sources", []):
        for candidate in source.get("article_candidates", []):
            target = substantive if candidate.get("substantive_article_candidate") is True else rejected
            target.append(_candidate_row(source, candidate))
    return substantive, rejected


def reconcile_article_candidates(candidate_inventory: dict[str, Any]) -> dict[str, Any]:
    if candidate_inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian article candidate inventory")
    if candidate_inventory.get("status") != "article_text_candidates_not_reviewed":
        raise ValueError("Austrian article candidates are not in machine-candidate state")

    partners: list[dict[str, Any]] = []
    for partner in candidate_inventory.get("partners", []):
        partner_label = str(partner.get("partner_label") or "")
        if not partner_label:
            raise ValueError("Article candidate record without partner label")

        substantive, rejected = _all_candidates(partner)
        article_rows: list[dict[str, Any]] = []
        for number in ARTICLE_NUMBERS:
            candidates = [row for row in substantive if row.get("article_number") == number]
            rejected_candidates = [row for row in rejected if row.get("article_number") == number]
            hashes = {row["text_sha256"] for row in candidates if row.get("text_sha256")}
            article_rows.append(
                {
                    "article_number": number,
                    "candidate_count": len(candidates),
                    "rejected_candidate_count": len(rejected_candidates),
                    "unique_text_variant_count": len(hashes),
                    "candidate_roles": sorted({row["role_candidate"] for row in candidates}),
                    "review_strategy": _review_strategy(candidates),
                    "candidates": candidates,
                    "rejected_candidates": rejected_candidates,
                    "controlling_text_selected": False,
                    "legal_review_completed": False,
                    "rate_interpretation_released": False,
                }
            )

        income_rows: list[dict[str, Any]] = []
        for income_type in INCOME_TYPES:
            expected = EXPECTED_ARTICLE[income_type]
            candidates = [
                row for row in substantive
                if row.get("semantic_income_detected") == income_type
                or (
                    row.get("semantic_income_detected") is None
                    and row.get("article_number") == expected
                )
            ]
            rejected_candidates = [
                row for row in rejected
                if row.get("semantic_income_detected") == income_type
            ]
            hashes = {row["text_sha256"] for row in candidates if row.get("text_sha256")}
            actual_articles = sorted({
                int(row["article_number"])
                for row in candidates
                if isinstance(row.get("article_number"), int)
            })
            nonstandard = bool(actual_articles and actual_articles != [expected])
            income_rows.append(
                {
                    "income_type": income_type,
                    "expected_oecd_article_number": expected,
                    "actual_article_numbers_machine": actual_articles,
                    "nonstandard_article_number_machine": nonstandard,
                    "candidate_count": len(candidates),
                    "rejected_candidate_count": len(rejected_candidates),
                    "unique_text_variant_count": len(hashes),
                    "candidate_roles": sorted({row["role_candidate"] for row in candidates}),
                    "review_strategy": _review_strategy(candidates),
                    "candidates": candidates,
                    "rejected_candidates": rejected_candidates,
                    "controlling_text_selected": False,
                    "conditions_mapped": False,
                    "legal_review_completed": False,
                    "rate_interpretation_released": False,
                }
            )

        partners.append(
            {
                "partner_label": partner_label,
                "articles": article_rows,
                "income_scopes": income_rows,
                "instrument_chain_reconciliation_completed": False,
                "release_eligible": False,
            }
        )

    return {
        "schema_version": 3,
        "source_country": "AT",
        "status": "article_variant_reconciliation_queue_not_reviewed",
        "partner_count": len(partners),
        "partners": partners,
        "release_constraints": [
            "Candidates rejected by the article-quality gate remain auditable but cannot enter legal text reconciliation.",
            "Income-scope reconciliation uses conservative semantic classification and retains actual treaty article numbering; nonstandard numbering never gets silently remapped.",
            "Different hashes are evidence variants, not automatically legal conflicts; formatting, language and protocol history may explain differences.",
            "A current consolidated RIS view and an MLI synthesized BMF text must be compared where both exist; neither is selected automatically as the controlling text.",
            "MLI presence by itself does not increase legal-risk classification and does not establish a result-changing modification.",
            "No treaty rate or condition is released until controlling text, instrument chronology, rate-to-condition mapping and any bilateral MLI effect are reviewed."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    inventory = json.loads(args.input.read_text(encoding="utf-8"))
    result = reconcile_article_candidates(inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"AT article reconciliation queue: {result['partner_count']} partners")
    for partner in result["partners"]:
        print(
            partner["partner_label"],
            [(row["income_type"], row["actual_article_numbers_machine"], row["unique_text_variant_count"], row["review_strategy"]) for row in partner["income_scopes"]],
        )


if __name__ == "__main__":
    main()
