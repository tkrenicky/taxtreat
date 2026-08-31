from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

EXTRACTION_PATH = SK_DIR / "treaty_article_machine_extraction.json"
OUTPUT_PATH = SK_DIR / "treaty_semantic_candidates.json"
SUMMARY_PATH = SK_DIR / "treaty_semantic_candidates_summary.json"

PERCENT_RE = re.compile(
    r"(?<!\d)(\d{1,3}(?:[.,]\d+)?)\s*(?:%|percent|procent)",
    re.IGNORECASE,
)
HOLDING_RE = re.compile(
    r"(?<!\d)(\d{1,4})\s*(dní|dni|dňov|mesiacov|měsíců|mesicu|months?)",
    re.IGNORECASE,
)

VALIDATED_EXTRACTION_STATUSES = {
    "article_extracted",
    "article_extracted_by_title_number_variance",
}
PRIMARY_SUMMARY_FALLBACK_STATUS = "article_evidence_primary_summary_fallback"

EXCLUSIVE_RESIDENCE_PATTERNS = (
    "môžu zdaniť iba v tomto druhom štáte",
    "môžu byť zdanené iba v tomto druhom štáte",
    "môžu sa zdaniť iba v tomto druhom štáte",
    "sa môžu zdaniť iba v tomto druhom štáte",
    "môžu zdaniť len v tomto druhom štáte",
    "môžu byť zdanené len v tomto druhom štáte",
    "podliehajú zdaneniu len v tomto druhom štáte",
    "mohou být zdaněny pouze v tomto druhém státě",
    "mohou být zdaněny jen v tomto druhém státě",
    "shall be taxable only in that other state",
)

BENEFICIAL_OWNER_TOKENS = (
    "skutočný vlastník",
    "skutočným vlastníkom",
    "skutečný vlastník",
    "skutečným vlastníkem",
    "skutočne právo na",
    "beneficial owner",
)

PE_TOKENS = (
    "stála prevádzkareň",
    "stálej prevádzkarne",
    "stálá provozovna",
    "stálé provozovny",
    "permanent establishment",
    "trvalé zariadenie",
    "trvalého zariadenia",
)

OWNERSHIP_TOKENS = (
    "kapitálu",
    "kapitalu",
    "hlasovac",
    "podiel",
    "podíl",
    "share capital",
    "voting",
)


# Percentages expressing an ownership / voting threshold are treaty conditions,
# not withholding-tax rates. They frequently occur in the same sentence as the
# reduced dividend rate (e.g. "5 % ... if ... owns at least 10 % of capital").
# The generic percentage extractor must therefore classify the matched
# percentage itself, rather than treating every percentage in Article 10/11/12
# as a candidate tax rate.
OWNERSHIP_PERCENT_AFTER_PATTERNS = (
    re.compile(r"^\s*(?:z|of)\s+(?:majetku|kapitálu|kapitalu|hlasovac\w*|podiel\w*|podíl\w*|share\w*|capital|voting\w*)", re.IGNORECASE),
    re.compile(r"^\s*(?:majetku|kapitálu|kapitalu|hlasovac\w*|podiel\w*|podíl\w*|share\w*|capital|voting\w*)", re.IGNORECASE),
)

RATE_PERCENT_AFTER_PATTERNS = (
    re.compile(r"^\s*(?:z|of)\s+(?:hrubej|hrubé|gross)\s+(?:sumy|amount)", re.IGNORECASE),
    re.compile(r"^\s*(?:hrubej|hrubé|gross)\s+(?:sumy|amount)", re.IGNORECASE),
)


def _percentage_is_ownership_threshold(text: str, match: re.Match[str]) -> bool:
    after = text[match.end():match.end() + 120]
    if any(pattern.search(after) for pattern in RATE_PERCENT_AFTER_PATTERNS):
        return False
    if any(pattern.search(after) for pattern in OWNERSHIP_PERCENT_AFTER_PATTERNS):
        return True

    before = text[max(0, match.start() - 120):match.start()].lower()
    ownership_leads = (
        "vlastní najmenej",
        "vlastní alespoň",
        "vlastní aspoň",
        "priamo vlastní",
        "přímo vlastní",
        "drží najmenej",
        "drží alespoň",
        "owns at least",
        "holds at least",
        "directly owns",
        "directly holds",
        "at least",
    )
    ownership_nouns = (
        "majetku",
        "kapitálu",
        "kapitalu",
        "hlasovac",
        "podiel",
        "podíl",
        "share",
        "capital",
        "voting",
    )
    return any(lead in before for lead in ownership_leads) and any(
        noun in after.lower() for noun in ownership_nouns
    )


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _compact(text: str) -> str:
    return " ".join(text.split())


def _context(text: str, start: int, end: int, radius: int = 240) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return _compact(text[left:right])


def _rate_candidates(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in PERCENT_RE.finditer(text):
        if _percentage_is_ownership_threshold(text, match):
            continue
        raw = match.group(1).replace(",", ".")
        value = float(raw)
        context = _context(text, match.start(), match.end())
        lowered = context.lower()
        rows.append({
            "rate_percent": value,
            "context": context,
            "context_sha256": hashlib.sha256(context.encode("utf-8")).hexdigest(),
            "ownership_context": any(token in lowered for token in OWNERSHIP_TOKENS),
            "beneficial_owner_context": any(
                token in lowered for token in BENEFICIAL_OWNER_TOKENS
            ),
        })
    return rows


def _holding_candidates(text: str) -> list[dict[str, Any]]:
    rows = []
    for match in HOLDING_RE.finditer(text):
        context = _context(text, match.start(), match.end())
        rows.append({
            "value": int(match.group(1)),
            "unit": match.group(2).lower(),
            "context": context,
            "context_sha256": hashlib.sha256(context.encode("utf-8")).hexdigest(),
        })
    return rows


def build_semantic_candidate(article_text: str) -> dict[str, Any]:
    text = _compact(article_text)
    lowered = text.lower()
    rates = _rate_candidates(text)
    holdings = _holding_candidates(text)

    return {
        "article_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "rate_candidates": rates,
        "exclusive_residence_taxation_candidate": any(
            pattern in lowered for pattern in EXCLUSIVE_RESIDENCE_PATTERNS
        ),
        "beneficial_owner_wording_present": any(
            token in lowered for token in BENEFICIAL_OWNER_TOKENS
        ),
        "pe_or_fixed_base_carveout_wording_present": any(
            token in lowered for token in PE_TOKENS
        ),
        "holding_period_candidates": holdings,
        "ownership_linked_rate_candidate_count": sum(
            row["ownership_context"] for row in rates
        ),
        "semantic_status": "machine_candidate_not_legal_conclusion",
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }


def _candidate_from_primary_summary(scope: dict[str, Any]) -> dict[str, Any]:
    evidence = scope["primary_summary_evidence"]
    rate_candidates = [
        {
            "rate_percent": float(value),
            "context": "primary_source_summary_fallback",
            "context_sha256": None,
            "ownership_context": False,
            "beneficial_owner_context": bool(
                evidence.get("beneficial_owner_wording_present")
            ),
        }
        for value in evidence.get("rate_candidates_percent", [])
    ]
    return {
        "article_text_sha256": None,
        "rate_candidates": rate_candidates,
        "exclusive_residence_taxation_candidate": bool(
            evidence.get("exclusive_residence_taxation_candidate")
        ),
        "beneficial_owner_wording_present": bool(
            evidence.get("beneficial_owner_wording_present")
        ),
        "pe_or_fixed_base_carveout_wording_present": bool(
            evidence.get("pe_or_fixed_base_carveout_wording_present")
        ),
        "holding_period_candidates": evidence.get("holding_period_candidates", []),
        "ownership_linked_rate_candidate_count": 0,
        "semantic_status": "machine_candidate_primary_summary_fallback_not_legal_conclusion",
        "evidence_quality": "official_primary_source_summary_fallback_not_byte_exact",
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }


def build_candidates() -> dict[str, Any]:
    extraction = _load(EXTRACTION_PATH)
    if extraction["scope_count"] != 225:
        raise ValueError("Treaty article extraction must cover 225 scopes.")

    rows: list[dict[str, Any]] = []
    for scope in extraction["scopes"]:
        article_text = scope.get("article_text")
        extraction_status = scope.get("machine_extraction_status")
        title_status = scope.get("title_validation_status")

        if (
            extraction_status == PRIMARY_SUMMARY_FALLBACK_STATUS
            and scope.get("primary_summary_evidence")
        ):
            candidate = _candidate_from_primary_summary(scope)
            candidate.update({
                "packet_id": scope["packet_id"],
                "source_country": "SK",
                "recipient_country": scope["recipient_country"],
                "income_type": scope["income_type"],
                "actual_article": scope.get("actual_article"),
                "article_resolution_status": scope.get("article_resolution_status"),
                "source_url": scope.get("source_url"),
                "source_sha256": None,
                "source_snapshot_path": scope.get("source_snapshot_path"),
            })
            rows.append(candidate)
            continue

        if (
            not article_text
            or extraction_status not in VALIDATED_EXTRACTION_STATUSES
            or title_status != "expected_income_title_matched"
        ):
            rows.append({
                "packet_id": scope["packet_id"],
                "source_country": "SK",
                "recipient_country": scope["recipient_country"],
                "income_type": scope["income_type"],
                "semantic_status": "blocked_missing_validated_article_text",
                "source_extraction_status": extraction_status,
                "source_title_validation_status": title_status,
                "human_review_status": "not_started",
                "approval_eligible": False,
                "runtime_status": "not_released",
            })
            continue

        candidate = build_semantic_candidate(article_text)
        candidate.update({
            "packet_id": scope["packet_id"],
            "source_country": "SK",
            "recipient_country": scope["recipient_country"],
            "income_type": scope["income_type"],
            "actual_article": scope.get("actual_article"),
            "article_resolution_status": scope.get("article_resolution_status"),
            "source_url": scope.get("source_url"),
            "source_sha256": scope.get("source_sha256"),
        })
        rows.append(candidate)

    if len(rows) != 225:
        raise ValueError("Expected 225 treaty semantic candidate rows.")
    if any(row["approval_eligible"] for row in rows):
        raise ValueError("Semantic candidates cannot be legal approvals.")
    if any(row["runtime_status"] != "not_released" for row in rows):
        raise ValueError("Semantic candidates must remain fail-closed.")

    return {
        "schema_version": 3,
        "dataset_release": "sk-treaty-semantic-candidates-2026-08-19.3",
        "source_country": "SK",
        "scope_count": 225,
        "policy": {
            "candidate_evidence_only": True,
            "validated_income_article_required": True,
            "primary_summary_fallback_must_be_explicit_and_never_byte_exact": True,
            "title_mismatch_never_enters_semantic_candidate_layer": True,
            "no_rate_is_released_from_regex_extraction": True,
            "exclusive_residence_phrase_is_candidate_not_final_zero_rate": True,
            "pe_carveout_must_be_preserved": True,
            "human_review_starts_only_after_all_machine_evidence_is_ready": True,
            "runtime_release": False,
        },
        "scopes": rows,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["scopes"]
    candidate_statuses = {
        "machine_candidate_not_legal_conclusion",
        "machine_candidate_primary_summary_fallback_not_legal_conclusion",
    }
    return {
        "schema_version": 3,
        "dataset_release": payload["dataset_release"],
        "scope_count": len(rows),
        "candidate_rows": sum(row["semantic_status"] in candidate_statuses for row in rows),
        "primary_summary_fallback_rows": sum(
            row["semantic_status"]
            == "machine_candidate_primary_summary_fallback_not_legal_conclusion"
            for row in rows
        ),
        "blocked_rows": sum(
            row["semantic_status"] == "blocked_missing_validated_article_text"
            for row in rows
        ),
        "scopes_with_rate_candidates": sum(bool(row.get("rate_candidates")) for row in rows),
        "exclusive_residence_candidates": sum(
            row.get("exclusive_residence_taxation_candidate") is True for row in rows
        ),
        "beneficial_owner_wording_scopes": sum(
            row.get("beneficial_owner_wording_present") is True for row in rows
        ),
        "pe_carveout_wording_scopes": sum(
            row.get("pe_or_fixed_base_carveout_wording_present") is True for row in rows
        ),
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_candidates()
    summary = build_summary(payload)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Semantic candidate scopes:", summary["candidate_rows"])
    print("Primary-summary fallback scopes:", summary["primary_summary_fallback_rows"])
    print("Blocked scopes:", summary["blocked_rows"])
    print("Scopes with rate candidates:", summary["scopes_with_rate_candidates"])
    print("Exclusive-residence candidates:", summary["exclusive_residence_candidates"])
    print("PE carve-out wording scopes:", summary["pe_carveout_wording_scopes"])


if __name__ == "__main__":
    main()
