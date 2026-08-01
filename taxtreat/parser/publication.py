from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from taxtreat.validation.document_identity import (
    publication_reference,
    validate_treaty_identity,
    normalize_legal_text,
)

_NOTICE_MARKER = "sdeleni ministerstva zahranicnich veci"
_NOTICE_NUMBER_RE = re.compile(
    r"(?:^|\s)(?P<number>\d{1,3})\s+sdeleni\s+ministerstva\s+zahranicnich\s+veci(?:\s|$)"
)


@dataclass(frozen=True)
class PublicationSelection:
    pages: list[str]
    status: str
    method: str
    start_page: int
    end_page: int
    effective_title: str | None
    metadata_mismatch: bool
    candidate_count: int

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result.pop("pages")
        return result


def _notice_number(page: str) -> int | None:
    normalized = normalize_legal_text(page)
    match = _NOTICE_NUMBER_RE.search(normalized)
    return int(match.group("number")) if match else None


def _is_notice_page(page: str) -> bool:
    normalized = normalize_legal_text(page)
    return (
        _NOTICE_MARKER in normalized
        and "smlouva mezi" in normalized
        and ("podeps" in normalized or "sjednani smlouvy" in normalized)
    )


def _effective_title(number: int | None, source_title: str | None) -> str | None:
    if number is None:
        return source_title
    reference = publication_reference(source_title)
    if reference is None:
        return str(number)
    _, year = reference.split("/", 1)
    suffix = "Sb.m.s." if source_title and "m.s" in source_title.lower() else "Sb."
    return f"{number}/{year} {suffix}"


def select_treaty_pages(
    pages: list[str],
    *,
    expected_country: str,
    source_title: str | None,
) -> PublicationSelection:
    """Select one treaty from a publication containing one or more notices.

    Selection is based on the expected counterparty in a genuine Ministry of
    Foreign Affairs notice page. It does not rely on a country-specific map and
    never chooses a segment merely because an arbitrary publication number was
    found elsewhere in the document.
    """

    notice_indices = [index for index, page in enumerate(pages) if _is_notice_page(page)]
    candidates: list[tuple[int, int | None]] = []

    for index in notice_indices:
        identity = validate_treaty_identity(
            expected_country=expected_country,
            text=pages[index],
            source_title=None,
            minimum_text_length=40,
        )
        if identity.is_valid:
            candidates.append((index, _notice_number(pages[index])))

    if not candidates:
        return PublicationSelection(
            pages=pages,
            status="fallback",
            method="whole_document",
            start_page=1,
            end_page=len(pages),
            effective_title=source_title,
            metadata_mismatch=False,
            candidate_count=0,
        )

    expected_reference = publication_reference(source_title)
    expected_number = int(expected_reference.split("/", 1)[0]) if expected_reference else None

    selected_index, selected_number = candidates[0]
    if expected_number is not None:
        exact = [candidate for candidate in candidates if candidate[1] == expected_number]
        if exact:
            selected_index, selected_number = exact[0]

    next_notices = [index for index in notice_indices if index > selected_index]
    end_index = next_notices[0] if next_notices else len(pages)
    effective_title = _effective_title(selected_number, source_title)
    effective_reference = publication_reference(effective_title)

    return PublicationSelection(
        pages=pages[selected_index:end_index],
        status="resolved",
        method="notice_country_match",
        start_page=selected_index + 1,
        end_page=end_index,
        effective_title=effective_title,
        metadata_mismatch=(
            expected_reference is not None
            and effective_reference is not None
            and expected_reference != effective_reference
        ),
        candidate_count=len(candidates),
    )
