from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

INCOME_TYPES = ("dividend", "interest", "royalty")
EXPECTED_ARTICLE = {"dividend": 10, "interest": 11, "royalty": 12}

PERCENT_PATTERNS = (
    re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:%|prozent|percent|per\s+cent)", re.IGNORECASE),
    re.compile(r"(\d+(?:[.,]\d+)?)\s+vom\s+hundert", re.IGNORECASE),
    re.compile(r"(\d+(?:[.,]\d+)?)\s*v\.?\s*h\.?", re.IGNORECASE),
)
BENEFICIAL_OWNER_RE = re.compile(
    r"(?:beneficial\s+owner|beneficially\s+owned|nutzungsberechtigt|nutzungsberechtigte|wirtschaftlich\w*\s+eigentümer|wirtschaftlich\w*\s+eigentuemer)",
    re.IGNORECASE,
)
OWNERSHIP_BEFORE_RE = re.compile(
    r"(?:holds?|owns?|participation|capital|voting\s+power|shares?|beteiligung|kapital|stimmrecht|anteil).{0,70}$",
    re.IGNORECASE | re.DOTALL,
)
OWNERSHIP_AFTER_RE = re.compile(
    r"^.{0,90}(?:capital|voting\s+power|shares?|participation|kapital|stimmrecht|anteil|beteiligung)",
    re.IGNORECASE | re.DOTALL,
)
RATE_CONTEXT_AFTER_RE = re.compile(
    r"^.{0,100}(?:gross\s+amount|bruttobetrag|bruttobetrages|brutto(?:betrag|einnahmen)|of\s+the\s+gross)",
    re.IGNORECASE | re.DOTALL,
)
RATE_CONTEXT_BEFORE_RE = re.compile(
    r"(?:tax|steuer|rate|sazb|nicht\s+übersteigen|not\s+exceed).{0,100}$",
    re.IGNORECASE | re.DOTALL,
)
RESIDENCE_ONLY_RE = re.compile(
    r"(?:taxable\s+only\s+in|shall\s+be\s+taxable\s+only\s+in|nur\s+in\s+dem\s+anderen\s+(?:vertragstaat|vertragsstaat|staat)\s+besteuert|nur\s+im\s+anderen\s+(?:vertragstaat|vertragsstaat|staat)\s+besteuert|nur\s+in\s+diesem\s+staat\s+besteuert)",
    re.IGNORECASE,
)
PE_CARVEOUT_RE = re.compile(
    r"(?:permanent\s+establishment|fixed\s+base|betriebsstätte|betriebsstaette|feste\s+einrichtung)",
    re.IGNORECASE,
)
HOLDING_RE = re.compile(
    r"(?P<value>\d+)\s*(?P<unit>days?|months?|years?|tage?|monate?|jahre?)",
    re.IGNORECASE,
)
ROYALTY_CATEGORY_PATTERNS = {
    "copyright": re.compile(r"(?:copyright|urheberrecht)", re.IGNORECASE),
    "film_tv_radio": re.compile(r"(?:film|television|radio|fernseh|rundfunk|kinematograph)", re.IGNORECASE),
    "software": re.compile(r"(?:software|computerprogramm|computer\s+program)", re.IGNORECASE),
    "equipment": re.compile(r"(?:equipment|ausrüstung|ausruestung)", re.IGNORECASE),
    "industrial_ip_knowhow": re.compile(r"(?:patent|trademark|warenzeichen|marke|know-how|knowhow|secret\s+process|geheimverfahren)", re.IGNORECASE),
}
CLAUSE_BOUNDARY_RE = re.compile(r"(?m)(?=^\s*(?:\(?\d+\)|\d+[.)]|\(?[a-z]\)|[a-z][.)])\s+)")


def _artifact_text(path_value: str, artifact_root: Path) -> str:
    path = Path(path_value)
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    parts = path.parts
    if len(parts) >= 2 and parts[0] == "artifacts":
        candidate = artifact_root / Path(*parts[2:])
    else:
        candidate = artifact_root / path
    if not candidate.is_file():
        raise ValueError(f"Missing treaty article evidence: {candidate}")
    return candidate.read_text(encoding="utf-8", errors="replace")


def _clauses(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in CLAUSE_BOUNDARY_RE.split(text) if chunk.strip()]
    return chunks or [text.strip()]


def _percentage_mentions(text: str) -> list[tuple[float, int, int]]:
    mentions: list[tuple[float, int, int]] = []
    for pattern in PERCENT_PATTERNS:
        for match in pattern.finditer(text):
            mentions.append((float(match.group(1).replace(",", ".")), match.start(), match.end()))
    return sorted(mentions, key=lambda row: (row[1], row[2], row[0]))


def _is_ownership_percentage(text: str, start: int, end: int) -> bool:
    before = text[max(0, start - 100):start]
    after = text[end:min(len(text), end + 120)]
    if RATE_CONTEXT_AFTER_RE.search(after) or RATE_CONTEXT_BEFORE_RE.search(before):
        return False
    return bool(OWNERSHIP_BEFORE_RE.search(before) or OWNERSHIP_AFTER_RE.search(after))


def _ownership_thresholds(text: str) -> list[float]:
    return sorted({
        value
        for value, start, end in _percentage_mentions(text)
        if _is_ownership_percentage(text, start, end)
    })


def _holding_signal(text: str) -> tuple[int | None, str | None]:
    lower = text.lower()
    if not any(marker in lower for marker in ("period", "holding", "held", "zeitraum", "dauer", "ununterbrochen", "uninterrupted")):
        return None, None
    match = HOLDING_RE.search(text)
    if not match:
        return None, None
    value = int(match.group("value"))
    unit = match.group("unit").lower()
    if unit.startswith(("day", "tag")):
        return value, "days"
    if unit.startswith(("month", "monat")):
        return value, "months"
    return value, "years"


def _royalty_category(text: str) -> str | None:
    hits = [name for name, pattern in ROYALTY_CATEGORY_PATTERNS.items() if pattern.search(text)]
    if not hits:
        return None
    return "|".join(hits)


def _branch_rows(text: str, *, income_type: str, source_url: str) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    article_pe_carveout = bool(PE_CARVEOUT_RE.search(text))
    for clause in _clauses(text):
        ownership = _ownership_thresholds(clause)
        holding_value, holding_unit = _holding_signal(clause)
        beneficial_owner = bool(BENEFICIAL_OWNER_RE.search(clause))
        category = _royalty_category(clause) if income_type == "royalty" else None
        for value, start, end in _percentage_mentions(clause):
            if _is_ownership_percentage(clause, start, end):
                continue
            key = (value, clause, source_url)
            if key in seen:
                continue
            seen.add(key)
            branches.append({
                "rate_percent": value,
                "treatment_candidate": None,
                "condition_evidence_text": clause,
                "source_url": source_url,
                "beneficial_owner_required_machine": beneficial_owner,
                "ownership_threshold_percent_machine": min(ownership) if ownership else None,
                "holding_period_value_machine": holding_value,
                "holding_period_unit_machine": holding_unit,
                "category_discriminator_machine": category,
                "pe_carveout_machine": article_pe_carveout,
            })
        if RESIDENCE_ONLY_RE.search(clause):
            key = ("residence_only", clause, source_url)
            if key not in seen:
                seen.add(key)
                branches.append({
                    "rate_percent": None,
                    "treatment_candidate": "residence_only",
                    "condition_evidence_text": clause,
                    "source_url": source_url,
                    "beneficial_owner_required_machine": beneficial_owner,
                    "ownership_threshold_percent_machine": min(ownership) if ownership else None,
                    "holding_period_value_machine": holding_value,
                    "holding_period_unit_machine": holding_unit,
                    "category_discriminator_machine": category,
                    "pe_carveout_machine": article_pe_carveout,
                })
    return branches


def build_scope_machine_evidence(candidate_inventory: dict[str, Any], *, artifact_root: Path) -> dict[str, Any]:
    source_country = str(candidate_inventory.get("source_country") or "").strip().upper()
    if not source_country:
        raise ValueError("Candidate inventory is missing source_country")
    if candidate_inventory.get("status") != "article_text_candidates_not_reviewed":
        raise ValueError("Candidate inventory is not in machine-candidate state")

    scopes: list[dict[str, Any]] = []
    for partner in candidate_inventory.get("partners", []):
        partner_label = str(partner.get("partner_label") or "").strip()
        if not partner_label:
            raise ValueError("Candidate inventory contains partner without label")
        for income_type in INCOME_TYPES:
            expected = EXPECTED_ARTICLE[income_type]
            evidence_candidates: list[dict[str, Any]] = []
            for source in partner.get("sources", []) or []:
                source_url = str(source.get("final_url") or "")
                for candidate in source.get("article_candidates", []) or []:
                    if candidate.get("substantive_article_candidate") is not True:
                        continue
                    semantic = candidate.get("semantic_income_detected") or candidate.get("semantic_income_candidate")
                    number = candidate.get("article_number")
                    if semantic != income_type and not (semantic is None and number == expected):
                        continue
                    text = _artifact_text(str(candidate.get("artifact_path") or ""), artifact_root)
                    evidence_candidates.append({
                        "article_number": number,
                        "source_url": source_url,
                        "source_role": source.get("role_candidate"),
                        "text_sha256": candidate.get("text_sha256"),
                        "rate_branches_machine": _branch_rows(text, income_type=income_type, source_url=source_url),
                        "article_text": text,
                    })

            branches: list[dict[str, Any]] = []
            for evidence in evidence_candidates:
                branches.extend(evidence["rate_branches_machine"])
            unique_branches: list[dict[str, Any]] = []
            seen_branch: set[tuple[Any, ...]] = set()
            for branch in branches:
                key = (
                    branch.get("rate_percent"),
                    branch.get("treatment_candidate"),
                    branch.get("condition_evidence_text"),
                    branch.get("source_url"),
                )
                if key not in seen_branch:
                    seen_branch.add(key)
                    unique_branches.append(branch)

            blockers: list[str] = []
            if not evidence_candidates:
                blockers.append("no_substantive_semantic_article_candidate")
            if not unique_branches:
                blockers.append("no_rate_or_residence_only_branch_detected")
            if any(not str(branch.get("condition_evidence_text") or "").strip() for branch in unique_branches):
                blockers.append("condition_evidence_missing")
            if any(not str(branch.get("source_url") or "").startswith("https://") for branch in unique_branches):
                blockers.append("official_source_url_missing")

            scopes.append({
                "source_country": source_country,
                "partner_label": partner_label,
                "income_type": income_type,
                "actual_article_numbers_machine": sorted({
                    int(row["article_number"])
                    for row in evidence_candidates
                    if isinstance(row.get("article_number"), int)
                }),
                "evidence_candidate_count": len(evidence_candidates),
                "rate_branches_machine": unique_branches,
                "machine_evidence_complete": not blockers,
                "machine_evidence_blockers": blockers,
                "controlling_text_selected": False,
                "legal_review_completed": False,
                "promotable_to_canonical": False,
            })

    return {
        "schema_version": 1,
        "source_country": source_country,
        "status": "scope_machine_evidence_not_reviewed_not_released",
        "scope_count": len(scopes),
        "complete_scope_count": sum(row["machine_evidence_complete"] for row in scopes),
        "blocked_scope_count": sum(not row["machine_evidence_complete"] for row in scopes),
        "policy": {
            "article_number_alone_never_establishes_income_type": True,
            "ownership_percentages_are_not_rate_candidates": True,
            "residence_only_is_non_rate_treatment_not_synthetic_zero": True,
            "exact_condition_evidence_required_for_every_branch": True,
            "source_url_required_for_every_branch": True,
            "machine_evidence_is_not_legal_approval": True,
            "fail_closed": True
        },
        "scopes": scopes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inventory = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_scope_machine_evidence(inventory, artifact_root=args.artifact_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Treaty scope machine evidence:",
        result["source_country"],
        result["scope_count"],
        "scopes /",
        result["complete_scope_count"],
        "complete /",
        result["blocked_scope_count"],
        "blocked",
    )


if __name__ == "__main__":
    main()
