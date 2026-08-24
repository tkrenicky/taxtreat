from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("artifacts/at/article_candidate_inventory.json")
DEFAULT_OUTPUT = Path("artifacts/at/royalty_category_audit.json")

BASE_CATEGORIES = (
    "copyright_general",
    "film_tv_radio",
    "software",
    "industrial_ip_knowhow",
    "equipment_financial_lease",
    "equipment_other",
    "other_royalty",
)

PERCENT_PATTERNS = (
    re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:%|prozent|percent|per\s+cent)", flags=re.IGNORECASE),
    re.compile(r"(\d+(?:[.,]\d+)?)\s+vom\s+hundert", flags=re.IGNORECASE),
)

RISK_PATTERNS = {
    "software": (r"software", r"computerprogramm", r"computer program"),
    "film_tv_radio": (r"kinematograph", r"film", r"fernseh", r"rundfunk", r"radio", r"television"),
    "equipment": (r"ausrüstung", r"ausruestung", r"equipment"),
    "financial_lease": (r"finanzierungsleasing", r"financial lease", r"finance lease"),
    "operating_lease": (r"operatives leasing", r"operating lease", r"betriebsleasing"),
    "technical_services": (r"technische dienstleistung", r"technical services", r"technical assistance", r"technische hilfe"),
    "ownership_condition": (r"kapital", r"capital", r"stimmrecht", r"voting power", r"beteiligung", r"holding"),
}

OWNERSHIP_BEFORE_RE = re.compile(
    r"(?:kapital|capital|stimmrecht|voting\s+power|beteiligung|holding|shares?|anteil).{0,45}$",
    flags=re.IGNORECASE | re.DOTALL,
)
OWNERSHIP_AFTER_RE = re.compile(
    r"^\s*(?:des|der|am|of\s+(?:the\s+)?|in\s+(?:the\s+)?)?(?:kapitals?|capital|stimmrechte?|voting\s+power|shares?|anteile?)\b",
    flags=re.IGNORECASE,
)


def _artifact_text(path: Path, artifact_root: Path) -> str:
    parts = path.parts
    if len(parts) >= 2 and parts[0] == "artifacts" and parts[1] == "at":
        path = Path(*parts[2:])
    resolved = artifact_root / path
    if not resolved.is_file():
        raise ValueError(f"Missing AT article candidate text: {resolved}")
    return resolved.read_text(encoding="utf-8", errors="replace")


def _percentage_mentions(text: str) -> list[tuple[float, int, int]]:
    mentions: list[tuple[float, int, int]] = []
    for pattern in PERCENT_PATTERNS:
        for match in pattern.finditer(text):
            mentions.append((float(match.group(1).replace(",", ".")), match.start(), match.end()))
    return sorted(mentions, key=lambda item: (item[1], item[2], item[0]))


def _percentage_tokens(text: str) -> list[float]:
    return sorted({value for value, _, _ in _percentage_mentions(text)})


def _ownership_threshold_tokens(text: str) -> list[float]:
    values: set[float] = set()
    for value, start, end in _percentage_mentions(text):
        before = text[max(0, start - 70):start]
        after = text[end:min(len(text), end + 45)]
        if OWNERSHIP_BEFORE_RE.search(before) or OWNERSHIP_AFTER_RE.search(after):
            values.add(value)
    return sorted(values)


def _rate_candidates(text: str) -> list[float]:
    raw = set(_percentage_tokens(text))
    ownership = set(_ownership_threshold_tokens(text))
    return sorted(raw - ownership)


def _flags(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        name: any(re.search(pattern, lowered, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)
        for name, patterns in RISK_PATTERNS.items()
    }


def build_audit(candidate_inventory: dict[str, Any], *, artifact_root: Path) -> dict[str, Any]:
    if candidate_inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian article candidate inventory")
    if candidate_inventory.get("partner_count") != 89:
        raise ValueError(f"Expected 89 current AT treaty partners, got {candidate_inventory.get('partner_count')}")

    rows: list[dict[str, Any]] = []
    for partner in candidate_inventory.get("partners", []):
        label = str(partner.get("partner_label") or "")
        source_texts: list[str] = []
        rejected_count = 0
        for source in partner.get("sources", []):
            for candidate in source.get("article_candidates", []):
                if candidate.get("article_number") != 12:
                    continue
                if candidate.get("substantive_article_candidate") is not True:
                    rejected_count += 1
                    continue
                source_texts.append(_artifact_text(Path(str(candidate["artifact_path"])), artifact_root))
        combined = "\n".join(source_texts)
        percentages = _percentage_tokens(combined)
        ownership_thresholds = _ownership_threshold_tokens(combined)
        rates = _rate_candidates(combined)
        flags = _flags(combined)
        machine_risk_reasons: list[str] = []
        if not source_texts:
            machine_risk_reasons.append("no_substantive_article_12_candidate")
        if len(rates) > 1:
            machine_risk_reasons.append("multiple_rate_candidates_after_condition_filter")
        if flags["financial_lease"] or flags["operating_lease"]:
            machine_risk_reasons.append("lease_subcategory_language")
        if flags["technical_services"]:
            machine_risk_reasons.append("technical_services_or_assistance_language")
        if ownership_thresholds:
            machine_risk_reasons.append("ownership_percentage_condition_present")

        rows.append({
            "partner_label": label,
            "candidate_text_count": len(source_texts),
            "rejected_candidate_count": rejected_count,
            "percentage_tokens_raw": percentages,
            "ownership_threshold_tokens_machine": ownership_thresholds,
            "rate_candidates_machine": rates,
            "non_rate_percentage_tokens": sorted(set(percentages) - set(rates)),
            "keyword_flags": flags,
            "machine_risk_reasons": machine_risk_reasons,
            "category_projection_review_required": bool(machine_risk_reasons),
            "treaty_specific_discriminators_resolved": False,
            "projection_released": False,
            "legal_review_completed": False,
        })

    risk_rows = [row for row in rows if row["category_projection_review_required"]]
    return {
        "schema_version": 2,
        "source_country": "AT",
        "status": "royalty_category_machine_risk_queue_not_released",
        "base_user_facing_categories": list(BASE_CATEGORIES),
        "partner_count": len(rows),
        "risk_partner_count": len(risk_rows),
        "policy": {
            "seven_base_categories_are_not_assumed_to_be_legally_exhaustive": True,
            "treaty_specific_discriminators_may_be_required": True,
            "raw_percentage_tokens_are_not_rate_candidates": True,
            "ownership_threshold_percentages_cannot_create_rate_branches": True,
            "machine_rate_candidates_do_not_establish_category_rates": True,
            "ownership_or_service_rate_conditions_must_not_be_misclassified_as_royalty_categories": True,
            "multiple_applicable_branches_with_different_results_must_fail_closed": True,
            "no_rate_projection_is_released_by_this_audit": True,
        },
        "partners": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--artifact-root", type=Path, default=Path("artifacts/at"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_audit(source, artifact_root=args.artifact_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("AT royalty category audit:", result["partner_count"], "partners /", result["risk_partner_count"], "machine-risk partners")


if __name__ == "__main__":
    main()
