from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class LegalSource:
    source_id: str
    title: str
    authority: str
    authority_class: str
    url: str
    retrieved_at: date
    effective_note: str | None = None


def load_legal_sources(path: str | Path) -> dict[str, LegalSource]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list):
        raise ValueError("Legal-source file must contain a 'sources' list.")

    sources: dict[str, LegalSource] = {}
    for raw in raw_sources:
        source = LegalSource(
            source_id=raw["source_id"],
            title=raw["title"],
            authority=raw["authority"],
            authority_class=raw["authority_class"],
            url=raw["url"],
            retrieved_at=date.fromisoformat(raw["retrieved_at"]),
            effective_note=raw.get("effective_note"),
        )
        if source.source_id in sources:
            raise ValueError(f"Duplicate legal-source id: {source.source_id}")
        if source.authority_class != "official":
            raise ValueError(
                f"Legal source {source.source_id} is not an official source."
            )
        if not source.url.startswith("https://"):
            raise ValueError(
                f"Legal source {source.source_id} must use HTTPS."
            )
        sources[source.source_id] = source
    return sources


def validate_evidence_references(
    evidence_source_ids: list[str | None],
    sources: dict[str, LegalSource],
) -> list[str]:
    return sorted(
        source_id
        for source_id in set(evidence_source_ids)
        if source_id is not None and source_id not in sources
    )
