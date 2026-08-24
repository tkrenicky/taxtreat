from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("artifacts/at/treaty_source_inventory_machine.json")
DEFAULT_OUTPUT = Path("artifacts/at/mli_bilateral_review_queue.json")


def build_mli_review_queue(inventory: dict[str, Any]) -> dict[str, Any]:
    if inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian treaty inventory")
    if inventory.get("status") != "machine_source_inventory_not_reviewed":
        raise ValueError("Austrian treaty inventory is not in discovery state")

    relationships: list[dict[str, Any]] = []
    for row in inventory.get("records", []):
        if row.get("release_universe_candidate") is not True or row.get("mli_flag") is not True:
            continue
        partner = str(row.get("partner_label") or "")
        if not partner:
            raise ValueError("MLI-flagged Austrian treaty record without partner label")
        relationships.append(
            {
                "partner_label": partner,
                "austria_machine_mli_flag": True,
                "official_treaty_links": list(row.get("treaty_links") or []),
                "partner_mli_party_status_verified": False,
                "partner_cta_notification_verified": False,
                "austria_cta_notification_verified": False,
                "article_7": {
                    "austria_position_verified": False,
                    "partner_position_verified": False,
                    "bilateral_match_resolved": False,
                    "result_changing_effects": [],
                },
                "article_8": {
                    "austria_position_verified": False,
                    "partner_position_verified": False,
                    "bilateral_match_resolved": False,
                    "result_changing_effects": [],
                },
                "other_wht_relevant_articles": [],
                "article_35": {
                    "austria_entry_into_force_verified": False,
                    "partner_entry_into_force_verified": False,
                    "withholding_tax_effective_date_resolved": False,
                    "withholding_tax_effective_date": None,
                },
                "synthesized_text_cross_check_completed": False,
                "bilateral_adjudication_completed": False,
                "release_eligible": False,
            }
        )

    if not relationships:
        raise ValueError("No current Austrian MLI discovery relationships found")
    return {
        "schema_version": 1,
        "source_country": "AT",
        "status": "bilateral_mli_review_queue_not_adjudicated",
        "relationship_count": len(relationships),
        "relationships": relationships,
        "release_constraints": [
            "Austria-side machine MLI flags are discovery signals only.",
            "Partner CTA notification and partner-side positions must be verified independently.",
            "Reservations and optional provisions must be matched bilaterally before any legal effect is recorded.",
            "Article 35 withholding-tax effective date must be resolved pair by pair.",
            "PPT applicability alone does not make a package elevated; complexity classification requires an additional country-specific issue.",
            "No MLI result-changing effect is released by this queue."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inventory = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_mli_review_queue(inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AT bilateral MLI review queue: {result['relationship_count']} relationships")


if __name__ == "__main__":
    main()
