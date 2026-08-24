from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "data/legal_reviews/at_outbound/treaty_source_inventory_machine.json"
)
DEFAULT_OUTPUT = Path(
    "data/legal_reviews/at_outbound/treaty_review_queue.json"
)
INCOME_TYPES = ("dividend", "interest", "royalty")


def build_review_queue(machine_inventory: dict[str, Any]) -> dict[str, Any]:
    if machine_inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian machine treaty inventory")
    if machine_inventory.get("status") != "machine_source_inventory_not_reviewed":
        raise ValueError("Austrian treaty inventory is not in machine discovery state")

    records = machine_inventory.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Austrian treaty machine inventory contains no records")

    scopes: list[dict[str, Any]] = []
    for treaty in records:
        partner_label = str(treaty.get("partner_label") or "").strip()
        if not partner_label:
            raise ValueError("Treaty record without partner label")
        treaty_links = treaty.get("treaty_links") or []
        if not isinstance(treaty_links, list):
            raise ValueError(f"Treaty links must be a list for {partner_label}")

        for income_type in INCOME_TYPES:
            scopes.append(
                {
                    "source_country": "AT",
                    "partner_label": partner_label,
                    "income_type": income_type,
                    "status": "needs_primary_text_review",
                    "machine_mli_flag": treaty.get("mli_flag") is True,
                    "instrument_chain": {
                        "base_treaty_resolved": False,
                        "protocols_resolved": False,
                        "current_text_resolved": False,
                        "official_links": list(treaty_links),
                    },
                    "rate_extraction": {
                        "article_number": None,
                        "base_rate_percent": None,
                        "qualifying_rate_percent": None,
                        "qualifying_conditions": [],
                        "reviewed": False,
                    },
                    "mli": {
                        "bilateral_matching_completed": False,
                        "wht_effective_date_completed": False,
                        "result_changing_effects": [],
                    },
                    "release_eligible": False,
                }
            )

    return {
        "schema_version": 1,
        "source_country": "AT",
        "status": "review_queue_not_released",
        "treaty_partner_count": len(records),
        "scope_count": len(scopes),
        "scopes": scopes,
        "promotion_requirements": [
            "authoritative current treaty instrument chain resolved",
            "income article and all candidate rates reviewed from primary text",
            "all qualifying conditions mapped without inference",
            "bilateral MLI matching completed where potentially applicable",
            "withholding-tax effective date completed for every result-changing MLI effect",
            "domestic-law precedence remains independently satisfied",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    machine_inventory = json.loads(args.input.read_text(encoding="utf-8"))
    queue = build_review_queue(machine_inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"AT treaty review queue: {queue['treaty_partner_count']} partners / "
        f"{queue['scope_count']} scopes"
    )


if __name__ == "__main__":
    main()
