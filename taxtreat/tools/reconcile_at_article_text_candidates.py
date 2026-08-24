from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("artifacts/at/article_candidate_inventory.json")
DEFAULT_OUTPUT = Path("artifacts/at/article_candidate_reconciliation.json")
ARTICLE_NUMBERS = (10, 11, 12)


def _review_strategy(candidates: list[dict[str, Any]]) -> str:
    roles = {str(row.get("role_candidate") or "") for row in candidates}
    if "synthesized_mli_text" in roles and "current_consolidated_view" in roles:
        return "compare_synthesized_mli_to_current_consolidated_and_published_chain"
    if "current_consolidated_view" in roles:
        return "review_current_consolidated_against_published_chain"
    if "synthesized_mli_text" in roles:
        return "review_synthesized_mli_against_published_chain"
    return "resolve_from_published_instruments"


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

        article_rows: list[dict[str, Any]] = []
        for number in ARTICLE_NUMBERS:
            candidates: list[dict[str, Any]] = []
            for source in partner.get("sources", []):
                for candidate in source.get("article_candidates", []):
                    if candidate.get("article_number") != number:
                        continue
                    candidates.append(
                        {
                            "source_order": source.get("source_order"),
                            "final_url": source.get("final_url"),
                            "role_candidate": source.get("role_candidate"),
                            "source_sha256": source.get("source_sha256"),
                            "text_sha256": candidate.get("text_sha256"),
                            "character_count": candidate.get("character_count"),
                            "artifact_path": candidate.get("artifact_path"),
                        }
                    )
            hashes = {row["text_sha256"] for row in candidates if row.get("text_sha256")}
            article_rows.append(
                {
                    "article_number": number,
                    "candidate_count": len(candidates),
                    "unique_text_variant_count": len(hashes),
                    "candidate_roles": sorted({row["role_candidate"] for row in candidates}),
                    "review_strategy": _review_strategy(candidates),
                    "candidates": candidates,
                    "controlling_text_selected": False,
                    "legal_review_completed": False,
                    "rate_interpretation_released": False,
                }
            )

        partners.append(
            {
                "partner_label": partner_label,
                "articles": article_rows,
                "instrument_chain_reconciliation_completed": False,
                "release_eligible": False,
            }
        )

    return {
        "schema_version": 1,
        "source_country": "AT",
        "status": "article_variant_reconciliation_queue_not_reviewed",
        "partner_count": len(partners),
        "partners": partners,
        "release_constraints": [
            "Different hashes are text variants, not automatically legal conflicts; formatting, language and protocol history may explain differences.",
            "A current consolidated RIS view and an MLI synthesized BMF text must be compared where both exist; neither is selected automatically as the controlling text.",
            "MLI presence by itself does not increase legal-risk classification and does not establish a result-changing modification.",
            "No treaty rate or condition is released until controlling text, instrument chronology and any bilateral MLI effect are reviewed."
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
            [(a["article_number"], a["unique_text_variant_count"], a["review_strategy"]) for a in partner["articles"]],
        )


if __name__ == "__main__":
    main()
