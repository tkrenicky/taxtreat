from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LegalFact:
    fact_id: str
    country: str
    name: str
    value: Any
    effective_from: date
    effective_to: date | None
    verification_status: str
    source_id: str | None
    source_url: str | None
    source_excerpt_hash: str | None
    source_text: str | None
    evidence_source_ids: tuple[str, ...]
    reviewer_id: str | None
    reviewed_at: date | None
    approved_by: str | None
    approved_at: date | None
    dataset_release: str | None

    @property
    def is_verified(self) -> bool:
        required = (
            self.source_id,
            self.source_url,
            self.source_excerpt_hash,
            self.reviewer_id,
            self.reviewed_at,
            self.approved_by,
            self.approved_at,
            self.dataset_release,
        )
        return self.verification_status == "verified" and all(required)

    @property
    def is_review_ready(self) -> bool:
        required = (
            self.source_id,
            self.source_url,
            self.source_excerpt_hash,
            self.source_text,
            self.dataset_release,
            self.evidence_source_ids,
        )
        if not all(required):
            return False
        return hashlib.sha256(
            self.source_text.encode("utf-8")
        ).hexdigest() == self.source_excerpt_hash.lower()

    def is_effective(self, as_of: date) -> bool:
        return self.effective_from <= as_of and (
            self.effective_to is None or as_of <= self.effective_to
        )


def _parse_date(value: str | None, *, required: bool = False) -> date | None:
    if value in (None, ""):
        if required:
            raise ValueError("effective_from is required for every legal fact")
        return None
    return date.fromisoformat(value)


def load_legal_facts(path: str | Path) -> list[LegalFact]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_facts = payload.get("facts")
    if not isinstance(raw_facts, list):
        raise ValueError("Legal-fact file must contain a 'facts' list.")

    facts: list[LegalFact] = []
    seen_ids: set[str] = set()
    for raw in raw_facts:
        fact_id = raw["fact_id"]
        if fact_id in seen_ids:
            raise ValueError(f"Duplicate legal-fact id: {fact_id}")
        seen_ids.add(fact_id)
        fact = LegalFact(
            fact_id=fact_id,
            country=raw["country"],
            name=raw["name"],
            value=raw.get("value"),
            effective_from=_parse_date(
                raw.get("effective_from"),
                required=True,
            ),
            effective_to=_parse_date(raw.get("effective_to")),
            verification_status=raw.get(
                "verification_status",
                "needs_review",
            ),
            source_id=raw.get("source_id"),
            source_url=raw.get("source_url"),
            source_excerpt_hash=raw.get("source_excerpt_hash"),
            source_text=raw.get("source_text"),
            evidence_source_ids=tuple(raw.get("evidence_source_ids", [])),
            reviewer_id=raw.get("reviewer_id"),
            reviewed_at=_parse_date(raw.get("reviewed_at")),
            approved_by=raw.get("approved_by"),
            approved_at=_parse_date(raw.get("approved_at")),
            dataset_release=raw.get("dataset_release"),
        )
        if fact.effective_to and fact.effective_to < fact.effective_from:
            raise ValueError(
                f"Legal fact {fact.fact_id} has an invalid date interval."
            )
        facts.append(fact)
    return facts


def resolve_legal_facts(
    facts: list[LegalFact],
    *,
    country: str,
    as_of: date,
) -> tuple[dict[str, Any], list[str]]:
    effective = [
        fact
        for fact in facts
        if fact.country == country and fact.is_effective(as_of)
    ]
    resolved: dict[str, Any] = {}
    unresolved: list[str] = []
    by_name: dict[str, list[LegalFact]] = {}
    for fact in effective:
        by_name.setdefault(fact.name, []).append(fact)

    for name, candidates in by_name.items():
        verified = [fact for fact in candidates if fact.is_verified]
        values = {json.dumps(fact.value, sort_keys=True) for fact in verified}
        if len(verified) == 1 and len(values) == 1:
            resolved[name] = verified[0].value
        else:
            unresolved.append(name)
    return resolved, sorted(unresolved)


def resolve_legal_fact_candidates(
    facts: list[LegalFact],
    *,
    country: str,
    as_of: date,
) -> tuple[dict[str, Any], list[str]]:
    """Return unambiguous review-ready values and names not yet verified.

    Candidate values may drive a visible candidate calculation, but callers
    must keep the result in REVIEW_REQUIRED until ``unverified`` is empty.
    """

    effective = [
        fact
        for fact in facts
        if fact.country == country and fact.is_effective(as_of)
    ]
    values: dict[str, Any] = {}
    unverified: list[str] = []
    by_name: dict[str, list[LegalFact]] = {}
    for fact in effective:
        by_name.setdefault(fact.name, []).append(fact)

    for name, candidates in by_name.items():
        review_ready = [fact for fact in candidates if fact.is_review_ready]
        serialized = {
            json.dumps(fact.value, sort_keys=True) for fact in review_ready
        }
        if len(serialized) == 1:
            values[name] = review_ready[0].value
            if not any(fact.is_verified for fact in review_ready):
                unverified.append(name)
        else:
            unverified.append(name)
    return values, sorted(unverified)
