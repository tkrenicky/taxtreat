from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Sequence

from taxtreat.validation.document_identity import (
    TreatyIdentityResult,
    normalize_legal_text,
    publication_reference,
    validate_treaty_identity,
)

_NOTICE_NUMBER_RE = re.compile(r"^0*(?P<number>\d{1,4})$")
_REFERENCE_RE = re.compile(
    r"(?<!\d)(?P<number>\d{1,4})\s*/\s*(?P<year>(?:19|20)\d{2})(?!\d)"
)


@dataclass(frozen=True)
class PublicationSegment:
    start_index: int
    end_index: int
    notice_number: int


@dataclass(frozen=True)
class SourceResolution:
    status: str
    method: str
    requested_title: str
    effective_title: str
    start_page: int
    end_page: int
    notice_number: int | None = None
    metadata_mismatch: bool = False
    candidate_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _notice_number_from_page(page: str) -> int | None:
    """Detect a ministry notice body, excluding collection contents pages.

    Czech collection issues can contain several treaty notices. A real notice
    body normally contains the ministry wording twice (heading + operative
    sentence) and a standalone notice number near the beginning. Contents pages
    mention the wording only once and are therefore excluded.
    """

    normalized = normalize_legal_text(page)
    tokens = normalized.split()
    has_operational_verb = any(
        token.startswith("sde") and token.endswith("luje") for token in tokens
    )
    if normalized.count("ministerstv") < 2 or not has_operational_verb:
        return None

    for index, token in enumerate(tokens[:35]):
        match = _NOTICE_NUMBER_RE.fullmatch(token)
        if not match:
            continue

        following = tokens[index + 1 : index + 10]
        if any(item.startswith("sde") for item in following) and any(
            item.startswith("ministerstv") for item in following
        ):
            return int(match.group("number"))

    return None


def publication_segments(pages: Sequence[str]) -> list[PublicationSegment]:
    starts: list[tuple[int, int]] = []

    for index, page in enumerate(pages):
        notice_number = _notice_number_from_page(page)
        if notice_number is not None:
            starts.append((index, notice_number))

    return [
        PublicationSegment(
            start_index=start_index,
            end_index=(
                starts[position + 1][0]
                if position + 1 < len(starts)
                else len(pages)
            ),
            notice_number=notice_number,
        )
        for position, (start_index, notice_number) in enumerate(starts)
    ]


def _replace_reference_number(title: str, number: int) -> str:
    match = _REFERENCE_RE.search(title)
    if not match:
        return title

    return title[: match.start("number")] + str(number) + title[match.end("number") :]


def _validate_segment(country: str, pages: Sequence[str]) -> TreatyIdentityResult:
    return validate_treaty_identity(
        expected_country=country,
        source_title=None,
        text="\n\n".join(pages),
    )


def resolve_treaty_source(
    pages: Sequence[str],
    *,
    country: str,
    source_title: str,
) -> tuple[list[str], SourceResolution]:
    """Resolve the country-specific treaty from a collection publication.

    If reliable notice boundaries are present, the country match selects one
    notice segment. The observed notice number becomes the effective source
    metadata and any mismatch with the registry title remains auditable. If the
    publication cannot be segmented reliably, the function preserves the whole
    document so the existing parser path remains available without regression.
    """

    segments = publication_segments(pages)
    requested_reference = publication_reference(source_title)
    requested_number = (
        int(requested_reference.split("/", 1)[0])
        if requested_reference is not None
        else None
    )

    matching: list[tuple[PublicationSegment, TreatyIdentityResult]] = []
    for segment in segments:
        result = _validate_segment(
            country,
            pages[segment.start_index : segment.end_index],
        )
        if result.is_valid:
            matching.append((segment, result))

    if matching:
        # Prefer the registry number when it points to the same country. If the
        # registry association is wrong, a unique country match still resolves
        # the correct notice and records the metadata discrepancy.
        preferred = [
            candidate
            for candidate in matching
            if candidate[0].notice_number == requested_number
        ]
        candidates = preferred or matching

        if len(candidates) == 1:
            segment, _ = candidates[0]
            effective_title = _replace_reference_number(
                source_title,
                segment.notice_number,
            )
            return (
                list(pages[segment.start_index : segment.end_index]),
                SourceResolution(
                    status="resolved",
                    method="publication_notice_country_match",
                    requested_title=source_title,
                    effective_title=effective_title,
                    start_page=segment.start_index + 1,
                    end_page=segment.end_index,
                    notice_number=segment.notice_number,
                    metadata_mismatch=(
                        requested_number is not None
                        and segment.notice_number != requested_number
                    ),
                    candidate_count=len(matching),
                ),
            )

    return (
        list(pages),
        SourceResolution(
            status="fallback",
            method="whole_document",
            requested_title=source_title,
            effective_title=source_title,
            start_page=1,
            end_page=len(pages),
            notice_number=None,
            metadata_mismatch=False,
            candidate_count=len(matching),
        ),
    )
