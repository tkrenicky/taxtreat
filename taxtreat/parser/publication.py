from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass

from taxtreat.validation.document_identity import (
    normalize_legal_text,
    publication_reference,
    validate_treaty_identity,
)

_NOTICE_MARKER_COMPACT = "sdeleniministerstvazahranicnichveci"
_NOTICE_MARKER_MOJIBAKE_RE = re.compile(
    r"sd[a-z]{0,4}leni[a-z]{0,3}ministerstvazahranic",
    re.IGNORECASE,
)
_FLEXIBLE_NOTICE_RE = re.compile(
    r"s.{0,3}d.{0,3}[eě].{0,3}l.{0,3}e.{0,3}n.{0,3}[ií]",
    re.IGNORECASE,
)
_NOTICE_NUMBER_RE = re.compile(
    r"(?<!\d)(?P<number>\d{1,3})\s+"
    r"s.{0,3}d.{0,3}[eě].{0,3}l.{0,3}e.{0,3}n.{0,3}[ií]",
    re.IGNORECASE,
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


def _compact(value: str) -> str:
    value = normalize_legal_text(value)
    value = value.translate(str.maketrans({"õ": "i", "Õ": "I"}))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _notice_number(page: str) -> int | None:
    # Work on the original page first so adjacent issue/page numbers remain
    # separated. The bounded gaps tolerate both spaced OCR and mojibake glyphs.
    matches = list(_NOTICE_NUMBER_RE.finditer(page))
    if matches:
        return int(matches[-1].group("number"))

    normalized = normalize_legal_text(page)
    matches = list(_NOTICE_NUMBER_RE.finditer(normalized))
    return int(matches[-1].group("number")) if matches else None


def _is_treaty_title_page(page: str) -> bool:
    compact = _compact(page)
    has_parties = "smlouvamezi" in compact or "conventionbetween" in compact
    has_tax_subject = any(
        marker in compact
        for marker in (
            "zamezenidvojimuzdaneni",
            "zamezenidvojihozdaneni",
            "avoidanceofdoubletaxation",
            "doubletaxation",
        )
    )
    return has_parties and has_tax_subject


def _is_notice_page(page: str) -> bool:
    compact = _compact(page)
    # Official notice summaries may omit the full tax-subject wording in OCR
    # or synthetic fixtures; the Ministry marker plus treaty-party phrase is
    # sufficient at this publication-boundary stage.
    has_notice_marker = (
        _NOTICE_MARKER_COMPACT in compact
        or _NOTICE_MARKER_MOJIBAKE_RE.search(compact) is not None
    )
    return has_notice_marker and (
        "smlouvamezi" in compact or "conventionbetween" in compact
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
    """Select the expected treaty from a single- or multi-act publication."""

    notice_indices = [index for index, page in enumerate(pages) if _is_notice_page(page)]
    if not notice_indices:
        notice_indices = [
            index for index, page in enumerate(pages) if _is_treaty_title_page(page)
        ]

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
