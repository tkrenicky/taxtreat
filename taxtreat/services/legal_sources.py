from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PROVISIONS = (
    ROOT / "data" / "legal_texts" / "canonical_provisions.json"
)
LEGACY_VERIFIED_PROVISIONS = (
    ROOT / "data" / "legal_texts" / "verified_provisions.json"
)
_LAYER_ORDER = {
    "domestic": 0,
    "treaty": 1,
    "protocol": 2,
    "mli": 3,
    "eu_relief": 4,
}
_CZ_OUTBOUND_INCOME_TYPES = {"dividend", "interest", "royalty"}
_CZ_DOMESTIC_SOURCE_URL = "https://e-sbirka.gov.cz/sb/1992/586"
_DISPLAYABLE_TREATY_TEXT_STATUSES = {
    "official_esbirka_structured_text_pdf_anchored",
}


def _domestic_starting_point(income_type: str) -> dict[str, Any]:
    """Return the mandatory Czech domestic starting point for the legal path.

    The date of a consolidated source package must not decide whether the
    domestic starting step is displayed. Rule selection remains owned by the
    legal engine; this item makes the audit path complete when an applicable
    treaty rule is returned without its preceding domestic citation.
    """

    return {
        "rule_id": f"CZ-{income_type.upper()}-DOMESTIC-STARTING-15",
        "legal_instrument": "domestic_law",
        "legal_layer": "domestic",
        "article": "36",
        "paragraph": "1",
        "rate": 15.0,
        "tax_treatment": "taxable_at_rate",
        "source_id": "CZ-ZDP-CANONICAL",
        "source_url": _CZ_DOMESTIC_SOURCE_URL,
        "path_role": "domestic_starting_point",
    }


def _format_domestic_paragraph(value: Any) -> Any:
    """Render internal domestic locators in conventional Czech legal style."""

    if value in (None, ""):
        return value
    text = str(value).strip()
    match = re.fullmatch(r"(\d+)\(([a-z])\)\((\d+)\)", text)
    if match:
        paragraph, letter, point = match.groups()
        return f"odst. {paragraph} písm. {letter}) bod {point}"
    if re.fullmatch(r"\d+", text):
        return f"odst. {text}"
    return value


@lru_cache(maxsize=1)
def load_verified_provisions() -> dict[str, dict[str, Any]]:
    """Load canonical display text while retaining the historic public helper.

    Treaty display text is sourced from the official structured e-Sbírka text
    and is bound to the SHA-256 of the corresponding authoritative PDF. The
    legacy single-provision file remains a fallback for older checkouts only.
    """

    path = (
        CANONICAL_PROVISIONS
        if CANONICAL_PROVISIONS.is_file()
        else LEGACY_VERIFIED_PROVISIONS
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Canonical legal-text registry must contain an object.")
    return payload


def _attach_canonical_text(
    item: dict[str, Any],
    provision: dict[str, Any],
) -> None:
    text = str(provision.get("text") or "").strip()
    if not text:
        return

    text_source_status = str(provision.get("text_source_status") or "")
    legacy = not CANONICAL_PROVISIONS.is_file()
    if not legacy and text_source_status not in _DISPLAYABLE_TREATY_TEXT_STATUSES:
        return

    text_hash = provision.get("verified_text_sha256")
    item["official_text"] = text
    item["official_title"] = provision.get("title")
    item["source_url"] = provision.get("source_url") or item.get("source_url")
    item["official_text_sha256"] = text_hash
    item["official_pdf_sha256"] = provision.get("official_pdf_sha256")
    item["official_pdf_document_id"] = provision.get("official_pdf_document_id")
    item["text_source_status"] = provision.get("text_source_status")
    item["text_verification_status"] = provision.get("verification_status")
    item["text_verification_method"] = provision.get("verification_method")
    item["excerpt"] = text
    item["excerpt_sha256"] = text_hash
    if provision.get("official_pdf_pages"):
        item["official_pdf_pages"] = provision["official_pdf_pages"]


def _enrich_citations_in_place(
    citations: list[dict[str, Any]],
    *,
    source_country: str,
    recipient_country: str,
    provisions: dict[str, dict[str, Any]],
) -> None:
    """Make canonical treaty text available to consumers sharing citations."""

    for citation in citations:
        layer = str(citation.get("legal_layer") or "")
        article = str(citation.get("article") or "")
        provision = provisions.get(
            f"{source_country}-{recipient_country}|{layer}|{article}"
        )
        if provision:
            _attach_canonical_text(citation, provision)


def build_legal_path(
    citations: list[dict[str, Any]],
    *,
    source_country: str,
    recipient_country: str,
    selected_rule_id: str | None,
    income_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return one canonical legal path shared by UI and professional report.

    The caller's citation list is replaced with the same deduplicated path.
    This prevents exported reports from reintroducing duplicate treaty article
    cards or internal Stage 6 excerpts after the UI has already resolved the
    canonical legal path.
    """

    selected = selected_rule_id or ""
    provisions = load_verified_provisions()
    _enrich_citations_in_place(
        citations,
        source_country=source_country,
        recipient_country=recipient_country,
        provisions=provisions,
    )
    supplied = [dict(citation) for citation in citations]
    normalized_income_type = str(income_type or "").lower()
    has_domestic_start = any(
        str(citation.get("legal_layer") or "") == "domestic"
        for citation in supplied
    )
    if (
        source_country.upper() == "CZ"
        and normalized_income_type in _CZ_OUTBOUND_INCOME_TYPES
        and not has_domestic_start
    ):
        supplied.append(_domestic_starting_point(normalized_income_type))

    ordered = sorted(
        supplied,
        key=lambda citation: (
            _LAYER_ORDER.get(str(citation.get("legal_layer")), 99),
            str(citation.get("rule_id")) != selected,
            str(citation.get("rule_id")),
        ),
    )
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for citation in ordered:
        layer = str(citation.get("legal_layer") or "")
        article = str(citation.get("article") or "")
        identity = (layer, str(citation.get("source_url") or ""), article)
        if identity in seen:
            continue
        seen.add(identity)
        item = dict(citation)
        provision = provisions.get(
            f"{source_country}-{recipient_country}|{layer}|{article}"
        )
        if provision:
            _attach_canonical_text(item, provision)
        if layer == "domestic":
            item["paragraph"] = _format_domestic_paragraph(item.get("paragraph"))
            # Stage 6 domestic excerpts are internal summaries, not verbatim
            # statutory text. Keep the official source link and rule metadata,
            # but never present the internal summary as legal wording.
            item.pop("excerpt", None)
            item.pop("excerpt_sha256", None)
            item.pop("official_text", None)
            item.pop("official_text_sha256", None)
        result.append(item)

    citations[:] = [dict(item) for item in result]
    return result
