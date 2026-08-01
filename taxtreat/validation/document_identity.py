from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass

_PUBLICATION_REFERENCE_RE = re.compile(
    r"(?<!\d)(?P<number>\d{1,4})\s*/\s*(?P<year>(?:19|20)\d{2})(?!\d)"
)
_PARENTHESES_RE = re.compile(r"\(([^()]*)\)")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_OCR_TRANSLATION = str.maketrans({"õ": "í", "Õ": "Í"})

_GENERIC_COUNTRY_WORDS = {
    "a",
    "the",
    "of",
    "stat",
    "staty",
    "state",
    "states",
    "republika",
    "republic",
    "kralovstvi",
    "kingdom",
    "federace",
    "federation",
    "spojene",
    "united",
    "lidova",
    "lidove",
    "people",
    "demokraticka",
    "democratic",
}


@dataclass(frozen=True)
class TreatyIdentityResult:
    expected_country: str
    status: str
    reason: str
    matched_alias: str | None = None
    matched_method: str | None = None
    publication_reference: str | None = None
    publication_reference_found: bool | None = None
    warnings: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.status == "validated"

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["warnings"] = list(self.warnings)
        return result


class TreatyIdentityError(RuntimeError):
    """Raised when a source document does not match its expected treaty partner."""

    def __init__(self, result: TreatyIdentityResult):
        self.result = result
        super().__init__(
            "Treaty identity rejected: "
            f"{result.reason} (expected {result.expected_country!r})"
        )


def normalize_legal_text(value: str) -> str:
    """Normalize text for deterministic identity matching.

    This intentionally does not attempt to repair the treaty content. It only
    removes formatting and common OCR differences so that source identity can
    be checked before legal rules are extracted.
    """

    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    value = value.translate(_OCR_TRANSLATION)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.casefold()
    return " ".join(_NON_ALNUM_RE.sub(" ", value).split())


def country_aliases(country: str) -> tuple[str, ...]:
    """Create aliases from the registry label without country-specific rules."""

    raw_aliases = [country]
    parenthetical = _PARENTHESES_RE.findall(country)
    raw_aliases.extend(parenthetical)

    without_parentheses = _PARENTHESES_RE.sub(" ", country).strip()
    if without_parentheses:
        raw_aliases.append(without_parentheses)

    expanded: list[str] = []
    for alias in raw_aliases:
        expanded.extend(part.strip() for part in re.split(r"[/;]", alias) if part.strip())

    normalized: list[str] = []
    seen: set[str] = set()
    for alias in expanded:
        clean = normalize_legal_text(alias)
        if clean and clean not in seen:
            seen.add(clean)
            normalized.append(clean)
    return tuple(normalized)


def publication_reference(title: str | None) -> str | None:
    if not title:
        return None
    match = _PUBLICATION_REFERENCE_RE.search(title)
    if not match:
        return None
    return f"{int(match.group('number'))}/{match.group('year')}"


def _distinctive_roots(alias: str) -> tuple[str, ...]:
    """Return generic lexical roots for common country-name variants.

    The rules are language-shape rules, not country-specific exceptions. They
    cover registry labels such as ``Moldávie`` vs. treaty wording
    ``Moldavská republika`` and ``Kyrgyzstán`` vs. ``Kyrgyzská republika``.
    """

    words = [word for word in alias.split() if word not in _GENERIC_COUNTRY_WORDS]
    if not words:
        return ()

    word = max(words, key=len)
    candidates: list[str] = [word]

    if len(word) >= 4 and word[-1] in "aeioy":
        candidates.append(word[:-1])

    for suffix in ("stan", "sko", "ie"):
        if word.endswith(suffix):
            candidates.append(word[: -len(suffix)])

    roots: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if len(candidate) >= 3 and candidate not in seen:
            seen.add(candidate)
            roots.append(candidate)
    return tuple(roots)


def _match_country(expected_country: str, normalized_text: str) -> tuple[str, str] | None:
    aliases = country_aliases(expected_country)

    for alias in aliases:
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized_text):
            return alias, "exact_alias"

    for alias in aliases:
        for root in _distinctive_roots(alias):
            if len(root) == 3:
                continuation = r"(?:an)?sk[a-z0-9]*"
            else:
                continuation = r"[a-z0-9]*"

            if re.search(
                rf"(?<![a-z0-9]){re.escape(root)}{continuation}",
                normalized_text,
            ):
                return alias, "country_root"

    return None


def validate_treaty_identity(
    *,
    expected_country: str,
    text: str,
    source_title: str | None = None,
    minimum_text_length: int = 100,
) -> TreatyIdentityResult:
    """Validate that an extracted document belongs to the expected treaty partner.

    The check is deterministic and generic. It derives aliases from the country
    label supplied by the official registry and never contains per-country
    exceptions. Publication references are recorded as an additional audit
    signal; a missing reference creates a warning but does not override a
    positive counterparty match.
    """

    normalized_text = normalize_legal_text(text)
    reference = publication_reference(source_title)

    if len(normalized_text) < minimum_text_length:
        return TreatyIdentityResult(
            expected_country=expected_country,
            status="rejected",
            reason="insufficient_text",
            publication_reference=reference,
        )

    match = _match_country(expected_country, normalized_text)
    if match is None:
        return TreatyIdentityResult(
            expected_country=expected_country,
            status="rejected",
            reason="counterparty_not_found",
            publication_reference=reference,
        )

    matched_alias, matched_method = match
    warnings: list[str] = []
    reference_found: bool | None = None
    if reference is not None:
        number, year = reference.split("/", 1)
        flexible_reference = re.compile(
            rf"(?<!\d)0*{re.escape(number)}\s*/\s*{re.escape(year)}(?!\d)"
        )
        reference_found = bool(flexible_reference.search(text))
        if not reference_found:
            warnings.append("publication_reference_not_found")

    return TreatyIdentityResult(
        expected_country=expected_country,
        status="validated",
        reason="counterparty_matched",
        matched_alias=matched_alias,
        matched_method=matched_method,
        publication_reference=reference,
        publication_reference_found=reference_found,
        warnings=tuple(warnings),
    )
