from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

from taxtreat.engine.extractors import dividend_rule, interest_rule, royalty_rule
from taxtreat.engine.models import Rule
from taxtreat.engine.article_classifier import classify_article
from taxtreat.registry.legal_scope import load_partner_registry


ROOT = Path(__file__).resolve().parents[2]
PARSED_DIR = ROOT / "data" / "parsed"
DEFAULT_INVENTORY = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "remaining_294_base_candidates.json"
)
EXCLUDED_PILOT_CODES = {"AT", "CH"}
EXTRACTORS: dict[str, Callable[[str], Rule]] = {
    "dividend": dividend_rule,
    "interest": interest_rule,
    "royalty": royalty_rule,
}
SPECIAL_EXEMPTION_RE = re.compile(
    r"(?:vl[aá]d|centr[aá]ln|banka|bankou|veřejn|st[aá]t(?:u|em)|"
    r"government|central bank|public bod|financial institution)",
    re.IGNORECASE,
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source_id(country: str, source_title: str) -> str:
    token = f"CZ|{country}|{source_title}".encode("utf-8")
    return "SRC-" + hashlib.sha256(token).hexdigest()[:16].upper()


def _article_type(article: dict[str, Any]) -> str | None:
    result = classify_article(article.get("title") or "", article.get("text") or "")
    return result if result in EXTRACTORS else None


def _risk_flags(
    income_type: str,
    article_text: str,
    candidates: list[dict[str, Any]],
    discarded_candidates: list[dict[str, Any]],
) -> list[str]:
    flags: set[str] = set()
    if not candidates:
        flags.add("no_rate_candidate")
    if discarded_candidates:
        flags.add("non_dividend_ownership_percentage_requires_review")
    distinct_rates = {candidate["rate"] for candidate in candidates}
    if income_type == "royalty" and len(distinct_rates) > 1:
        flags.add("royalty_categories_not_fully_structured")
    if income_type == "dividend" and len(candidates) > 2:
        flags.add("dividend_special_cases_not_fully_structured")
    if 0.0 in distinct_rates and len(distinct_rates) > 1:
        flags.add("zero_rate_special_conditions_require_review")
    if SPECIAL_EXEMPTION_RE.search(article_text) and 0.0 in distinct_rates:
        flags.add("government_or_institution_exemption_requires_review")
    if any(candidate["rate"] > 15 for candidate in candidates):
        flags.add("treaty_rate_above_czech_domestic_rate")
    return sorted(flags)


def _rate_candidates(
    rule: Rule,
    *,
    income_type: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    discarded: list[dict[str, Any]] = []
    for candidate in rule.rates:
        source_text = candidate.source_text or ""
        row = {
            "rate": float(candidate.rate),
            "priority": candidate.priority,
            "legal_basis": candidate.legal_basis,
            "source_text": source_text,
            "source_text_sha256": _sha256(source_text),
            "conditions": [
                {
                    "condition_type": condition.condition_type.value,
                    "operator": condition.operator,
                    "value": condition.value,
                    "unit": condition.unit,
                }
                for condition in candidate.conditions
            ],
        }
        ownership_condition = any(
            condition["condition_type"] == "minimum_ownership"
            for condition in row["conditions"]
        )
        if income_type != "dividend" and ownership_condition:
            discarded.append(
                {
                    **row,
                    "discard_reason": (
                        "A non-dividend ownership percentage cannot be promoted "
                        "as a WHT rate without semantic review."
                    ),
                }
            )
        else:
            rows.append(row)
    return rows, discarded


def build_base_candidates(
    *,
    inventory_path: str | Path = DEFAULT_INVENTORY,
) -> dict[str, Any]:
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    inventory_by_code = {row["iso2"]: row for row in inventory["partners"]}
    scopes: list[dict[str, Any]] = []
    for partner in load_partner_registry():
        iso2 = partner["iso2"]
        if iso2 in EXCLUDED_PILOT_CODES:
            continue
        parsed_path = PARSED_DIR / partner["parsed_file"]
        parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
        article_by_type: dict[str, dict[str, Any]] = {}
        for article in parsed.get("articles", []):
            income_type = _article_type(article)
            if income_type is not None:
                article_by_type[income_type] = article
        if set(article_by_type) != set(EXTRACTORS):
            raise ValueError(
                f"{iso2} does not contain exactly the three supported articles."
            )

        inventory_row = inventory_by_code[iso2]
        base_urls = [
            source["url"] for source in inventory_row["base_instruments"]
        ]
        for income_type in ("dividend", "interest", "royalty"):
            article = article_by_type[income_type]
            article_text = article.get("text") or ""
            extracted = EXTRACTORS[income_type](article_text)
            candidates, discarded_candidates = _rate_candidates(
                extracted,
                income_type=income_type,
            )
            flags = _risk_flags(
                income_type,
                article_text,
                candidates,
                discarded_candidates,
            )
            blockers = ["independent_legal_review"]
            if inventory_row["protocol_listed"]:
                blockers.append("protocol_consolidation")
            if inventory_row["mli_listed"]:
                blockers.append(
                    "mli_effect_candidate_review"
                    if inventory_row["mli_notice_available"]
                    else "mli_matching_and_effective_date"
                )
            if income_type in {"interest", "royalty"}:
                blockers.append("domestic_and_eu_relief_consolidation")
            elif income_type == "dividend":
                blockers.append("domestic_and_parent_subsidiary_relief_consolidation")
            if flags:
                blockers.append("semantic_rate_review")
            scopes.append(
                {
                    "source_country": "CZ",
                    "recipient_country": iso2,
                    "recipient_country_name": partner["country"],
                    "income_type": income_type,
                    "parsed_path": str(parsed_path.relative_to(ROOT)),
                    "base_treaty_source_id": _source_id(
                        parsed["country"], parsed.get("source_title") or ""
                    ),
                    "base_treaty_publication": parsed.get("source_title"),
                    "official_source_urls": base_urls,
                    "article_number": article.get("number"),
                    "article_title": article.get("title"),
                    "article_text": article_text,
                    "article_text_sha256": _sha256(article_text),
                    "rate_candidates": candidates,
                    "discarded_rate_candidates": discarded_candidates,
                    "extractor_status": extracted.extraction_status,
                    "risk_flags": flags,
                    "consolidation_blockers": sorted(set(blockers)),
                    "candidate_status": (
                        "base_rate_candidate_extracted"
                        if candidates
                        else "manual_rate_extraction_required"
                    ),
                    "verification_status": "needs_review",
                }
            )

    if len(scopes) != 294:
        raise ValueError(f"Expected 294 remaining scopes, found {len(scopes)}.")
    return {
        "schema_version": 1,
        "dataset_release": "remaining-294-base-candidates-2026-08-03.1",
        "legal_data_cutoff": inventory["source_page"]["legal_data_cutoff"],
        "canonical_source": "data/parsed/*.json",
        "scope_exclusions": {
            "AT": "covered by the AT/CH pilot",
            "CH": "covered by the AT/CH pilot",
        },
        "scopes": sorted(
            scopes,
            key=lambda row: (
                row["recipient_country"],
                row["income_type"],
            ),
        ),
    }


def write_base_candidates(
    payload: dict[str, Any],
    path: str | Path = DEFAULT_OUTPUT,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
