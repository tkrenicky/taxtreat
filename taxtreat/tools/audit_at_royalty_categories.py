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
    re.compile(r"(\d+(?:[.,]\d+)?)\s*v\.?\s*h\.?", flags=re.IGNORECASE),
)
ROYALTY_TEXT_RE = re.compile(r"(?:lizenzgebühr|royalt)", flags=re.IGNORECASE)
TECHNICAL_SERVICE_RE = re.compile(
    r"(?:technische\w*\s+(?:dienstleistung|hilfe)|technical\s+(?:services?|assistance))",
    flags=re.IGNORECASE,
)
ROYALTY_SOURCE_EXEMPTION_RE = re.compile(
    r"(?:lizenzgebühr|royalt).{0,260}(?:von\s+der\s+besteuerung\s+ausgenommen|steuerfrei|shall\s+be\s+exempt|exempt\s+from\s+(?:tax|taxation))"
    r"|(?:von\s+der\s+besteuerung\s+ausgenommen|steuerfrei|shall\s+be\s+exempt|exempt\s+from\s+(?:tax|taxation)).{0,260}(?:lizenzgebühr|royalt)",
    flags=re.IGNORECASE | re.DOTALL,
)

RISK_PATTERNS = {
    "software": (r"software", r"computerprogramm", r"computer program"),
    "film_tv_radio": (r"kinematograph", r"film", r"fernseh", r"rundfunk", r"radio", r"television"),
    "equipment": (r"ausrüstung", r"ausruestung", r"equipment"),
    "financial_lease": (r"finanzierungsleasing", r"financial lease", r"finance lease"),
    "operating_lease": (r"operativ\w*\s+leasing", r"operating lease", r"betriebsleasing"),
    "technical_services": (r"technische dienstleistung", r"technical services", r"technical assistance", r"technische hilfe"),
    "ownership_condition": (r"kapital", r"capital", r"stimmrecht", r"voting power", r"beteiligung", r"holding"),
}

OWNERSHIP_BEFORE_RE = re.compile(
    r"(?:beteiligung|holding|holds?|owns?|anteil|kapital|capital|stimmrecht|voting\s+power|shares?)"
    r".{0,50}(?:von|of|mindestens|at\s+least|mehr\s+als|more\s+than|not\s+less\s+than)\s*$",
    flags=re.IGNORECASE | re.DOTALL,
)
OWNERSHIP_COMPARATIVE_BEFORE_RE = re.compile(
    r"(?:mehr\s+als|more\s+than|mindestens|at\s+least|not\s+less\s+than)\s*$",
    flags=re.IGNORECASE,
)
OWNERSHIP_AFTER_RE = re.compile(
    r"^\s*(?:(?:des|der|am)\s+|of\s+(?:the\s+)?|in\s+(?:the\s+)?)?"
    r"(?:(?:grund-?\s*(?:oder\s+)?stamm)?kapitals?|capital|stimmrechte?|voting\s+power|shares?|anteile?)\b",
    flags=re.IGNORECASE,
)
OWNERSHIP_CAPITAL_AFTER_RE = re.compile(
    r"^.{0,100}\b(?:grund\s*-?\s*(?:oder\s+)?stamm\s*-?\s*kapital|stamm\s*-?\s*kapital|kapital|capital|stimmrechte?|voting\s+power|shares?|anteile?)\b",
    flags=re.IGNORECASE | re.DOTALL,
)
CLAUSE_SPLIT_RE = re.compile(r"[;.!?]|\b(?:[a-z]|\d+)[.)]\s*", flags=re.IGNORECASE)


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
        before = text[max(0, start - 90):start]
        before_clause = re.split(r"[;.!?]", before)[-1]
        after = text[end:min(len(text), end + 120)]
        direct_context = OWNERSHIP_BEFORE_RE.search(before_clause) or OWNERSHIP_AFTER_RE.search(after)
        comparative_capital_context = (
            OWNERSHIP_COMPARATIVE_BEFORE_RE.search(before_clause)
            and OWNERSHIP_CAPITAL_AFTER_RE.search(after)
        )
        if direct_context or comparative_capital_context:
            values.add(value)
    return sorted(values)


def _technical_service_rate_tokens(text: str) -> list[float]:
    values: set[float] = set()
    for value, start, end in _percentage_mentions(text):
        before = text[max(0, start - 180):start]
        local_before = CLAUSE_SPLIT_RE.split(before)[-1]
        after = text[end:min(len(text), end + 100)]
        local_after = CLAUSE_SPLIT_RE.split(after)[0]
        local_context = f"{local_before} {local_after}"
        if TECHNICAL_SERVICE_RE.search(local_context) and not ROYALTY_TEXT_RE.search(local_context):
            values.add(value)
    return sorted(values)


def _rate_candidates(text: str) -> list[float]:
    raw = set(_percentage_tokens(text))
    ownership = set(_ownership_threshold_tokens(text))
    technical_services = set(_technical_service_rate_tokens(text))
    return sorted(raw - ownership - technical_services)


def _flags(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        name: any(re.search(pattern, lowered, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)
        for name, patterns in RISK_PATTERNS.items()
    }


def _royalty_semantic_candidate(text: str) -> bool:
    match = ROYALTY_TEXT_RE.search(text)
    return bool(match and match.start() < 180)


def _royalty_source_exemption_branch(text: str) -> bool:
    return bool(ROYALTY_SOURCE_EXEMPTION_RE.search(text))


def build_audit(candidate_inventory: dict[str, Any], *, artifact_root: Path) -> dict[str, Any]:
    if candidate_inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian article candidate inventory")
    if candidate_inventory.get("partner_count") != 89:
        raise ValueError(f"Expected 89 current AT treaty partners, got {candidate_inventory.get('partner_count')}")

    rows: list[dict[str, Any]] = []
    for partner in candidate_inventory.get("partners", []):
        label = str(partner.get("partner_label") or "")
        article_12_texts: list[str] = []
        fallback_texts: list[str] = []
        fallback_article_numbers: set[int] = set()
        rejected_count = 0
        semantic_rejected_article_12_count = 0

        for source in partner.get("sources", []):
            for candidate in source.get("article_candidates", []):
                number = candidate.get("article_number")
                semantic_income = candidate.get("semantic_income_candidate")
                if not isinstance(number, int) or number <= 0:
                    continue
                if number not in {10, 11, 12} and semantic_income != "royalty":
                    continue
                if candidate.get("substantive_article_candidate") is not True:
                    if number == 12:
                        rejected_count += 1
                    continue
                text = _artifact_text(Path(str(candidate["artifact_path"])), artifact_root)
                is_royalty_text = _royalty_semantic_candidate(text)
                if number == 12:
                    if is_royalty_text:
                        article_12_texts.append(text)
                    else:
                        semantic_rejected_article_12_count += 1
                elif is_royalty_text:
                    fallback_texts.append(text)
                    fallback_article_numbers.add(number)

        nonstandard_numbering = not article_12_texts and bool(fallback_texts)
        source_texts = article_12_texts if article_12_texts else fallback_texts
        royalty_article_numbers = [12] if article_12_texts else sorted(fallback_article_numbers)

        per_candidate_rates = [_rate_candidates(text) for text in source_texts]
        per_candidate_ownership = [_ownership_threshold_tokens(text) for text in source_texts]
        per_candidate_service_rates = [_technical_service_rate_tokens(text) for text in source_texts]
        per_candidate_exemption = [_royalty_source_exemption_branch(text) for text in source_texts]
        combined = "\n".join(source_texts)
        percentages = _percentage_tokens(combined)
        ownership_thresholds = sorted({value for values in per_candidate_ownership for value in values})
        technical_service_rates = sorted({value for values in per_candidate_service_rates for value in values})
        rates = sorted({value for values in per_candidate_rates for value in values})
        within_candidate_multi_rate = any(len(values) > 1 for values in per_candidate_rates)
        cross_instrument_rate_variance = len(rates) > 1 and not within_candidate_multi_rate
        source_exemption_branch = any(per_candidate_exemption)
        flags = _flags(combined)

        machine_risk_reasons: list[str] = []
        if not source_texts:
            machine_risk_reasons.append("no_substantive_article_12_candidate")
        if nonstandard_numbering:
            machine_risk_reasons.append("nonstandard_royalty_article_number_candidate")
        if within_candidate_multi_rate:
            machine_risk_reasons.append("multiple_rate_candidates_after_condition_filter")
        if cross_instrument_rate_variance:
            machine_risk_reasons.append("cross_instrument_rate_variance")
        if source_exemption_branch:
            machine_risk_reasons.append("royalty_source_exemption_branch_language")
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
            "semantic_rejected_article_12_count": semantic_rejected_article_12_count,
            "royalty_article_numbers_machine": royalty_article_numbers,
            "nonstandard_royalty_article_number_candidate": nonstandard_numbering,
            "percentage_tokens_raw": percentages,
            "ownership_threshold_tokens_machine": ownership_thresholds,
            "technical_service_rate_tokens_machine": technical_service_rates,
            "rate_candidates_machine": rates,
            "rate_candidates_by_text_machine": per_candidate_rates,
            "within_candidate_multi_rate_machine": within_candidate_multi_rate,
            "cross_instrument_rate_variance_machine": cross_instrument_rate_variance,
            "royalty_source_exemption_branch_machine": source_exemption_branch,
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
        "schema_version": 6,
        "source_country": "AT",
        "status": "royalty_category_machine_risk_queue_not_released",
        "base_user_facing_categories": list(BASE_CATEGORIES),
        "partner_count": len(rows),
        "risk_partner_count": len(risk_rows),
        "policy": {
            "seven_base_categories_are_not_assumed_to_be_legally_exhaustive": True,
            "treaty_specific_discriminators_may_be_required": True,
            "raw_percentage_tokens_are_not_rate_candidates": True,
            "legacy_v_h_percentage_notation_is_supported": True,
            "ownership_threshold_percentages_cannot_create_rate_branches": True,
            "technical_service_percentages_cannot_create_royalty_rate_branches": True,
            "source_exemption_language_is_a_branch_signal_not_a_synthetic_zero_rate": True,
            "machine_rate_candidates_do_not_establish_category_rates": True,
            "article_number_alone_does_not_establish_income_type": True,
            "royalty_semantics_required_for_article_candidate": True,
            "royalty_semantics_required_near_article_start_for_fallback_candidate": True,
            "nonstandard_royalty_article_number_requires_review": True,
            "cross_instrument_rate_variance_is_not_a_category_split": True,
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
