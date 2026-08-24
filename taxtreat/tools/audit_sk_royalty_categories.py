from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "legal_reviews" / "sk_outbound" / "treaty_article_machine_extraction.json"
DEFAULT_OUTPUT = ROOT / "data" / "legal_reviews" / "sk_outbound" / "royalty_category_audit_2026.json"

BASE_CATEGORIES = (
    "copyright_general",
    "film_tv_radio",
    "software",
    "industrial_ip_knowhow",
    "equipment_financial_lease",
    "equipment_other",
    "other_royalty",
)

KEYWORDS = {
    "software": (r"softv", r"software", r"computer", r"počítač"),
    "film_tv_radio": (r"kinematograf", r"film", r"telev", r"rozhlas", r"radio", r"nahráv", r"pásk"),
    "industrial_ip_knowhow": (r"patent", r"ochrann", r"trademark", r"dizajn", r"návrh", r"model", r"tajného vzorca", r"postup", r"skúsenost"),
    "equipment_other": (r"zariaden", r"equipment"),
    "equipment_financial_lease": (r"finančn.{0,20}prenáj", r"financial.{0,20}lease"),
}

# These are not machine conclusions. They are explicit review seeds for treaty drafting
# that cannot be represented safely by the seven broad user-facing categories alone.
KNOWN_ADDITIONAL_DISCRIMINATORS: dict[str, tuple[str, ...]] = {
    "BR": ("trademark_vs_other_industrial_ip", "historical_related_party_transition_clause"),
    "BY": ("transport_vehicles"),
    "FI": ("copyright_exclusive_residence_treatment", "financial_vs_operating_equipment_lease"),
    "TN": ("technical_or_economic_studies", "technical_assistance"),
    "VN": ("trademark_vs_patent_design_process", "commercial_vs_industrial_or_scientific_knowhow"),
}


def _rate_tokens(text: str) -> list[float]:
    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:%|percent)", text, flags=re.IGNORECASE)
    return sorted({float(token.replace(",", ".")) for token in matches})


def _keyword_flags(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        category: any(re.search(pattern, lowered, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)
        for category, patterns in KEYWORDS.items()
    }


def build_audit(source: dict[str, Any]) -> dict[str, Any]:
    royalty_scopes = [row for row in source.get("scopes", []) if row.get("income_type") == "royalty"]
    if len(royalty_scopes) != 75:
        raise ValueError(f"Expected 75 SK royalty scopes, got {len(royalty_scopes)}")

    scopes: list[dict[str, Any]] = []
    for row in royalty_scopes:
        country = str(row.get("recipient_country") or "")
        text = str(row.get("article_text") or "")
        if not country or not text:
            raise ValueError("Royalty scope missing recipient country or article text")
        rates = _rate_tokens(text)
        flags = _keyword_flags(text)
        extra = list(KNOWN_ADDITIONAL_DISCRIMINATORS.get(country, ()))
        split_rate = len(rates) > 1
        requires_review = split_rate or bool(extra)
        scopes.append({
            "scope_key": ["SK", country, "royalty"],
            "article": row.get("actual_article"),
            "article_text_sha256": row.get("article_text_sha256"),
            "source_url": row.get("source_url"),
            "rate_tokens_machine": rates,
            "base_category_keyword_flags": flags,
            "additional_discriminators_required": extra,
            "multiple_rate_tokens_present": split_rate,
            "category_projection_review_required": requires_review,
            "projection_released": False,
            "legal_review_completed": False,
        })

    elevated = [row for row in scopes if row["category_projection_review_required"]]
    return {
        "schema_version": 1,
        "source_country": "SK",
        "status": "royalty_category_audit_not_released",
        "base_user_facing_categories": list(BASE_CATEGORIES),
        "royalty_scope_count": len(scopes),
        "category_review_required_count": len(elevated),
        "category_review_required_countries": [row["scope_key"][1] for row in elevated],
        "policy": {
            "seven_base_categories_are_not_assumed_to_be_legally_exhaustive": True,
            "treaty_specific_discriminators_may_be_required": True,
            "multiple_applicable_branches_with_different_results_must_fail_closed": True,
            "machine_keyword_detection_is_not_legal_interpretation": True,
            "no_rate_or_category_projection_is_released_by_this_audit": True,
        },
        "scopes": scopes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_audit(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "SK royalty category audit:",
        result["royalty_scope_count"], "scopes /",
        result["category_review_required_count"], "review-required",
    )
    print("Review-required countries:", result["category_review_required_countries"])


if __name__ == "__main__":
    main()
