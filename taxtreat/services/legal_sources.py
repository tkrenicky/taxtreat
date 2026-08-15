from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VERIFIED_PROVISIONS = (
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


def _domestic_starting_point(income_type: str) -> dict[str, Any]:
    """Return the mandatory Czech domestic starting point for the legal path.

    The date of a consolidated source package must not decide whether the
    domestic starting step is displayed.  Rule selection remains owned by the
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
        "excerpt": (
            "Výchozím vnitrostátním krokem je sazba 15 % podle § 36 "
            "zákona č. 586/1992 Sb., o daních z příjmů. Následně je "
            "zohledněna příslušná smlouva nebo vnitrostátní osvobození."
        ),
    }


@lru_cache(maxsize=1)
def load_verified_provisions() -> dict[str, dict[str, str]]:
    return json.loads(VERIFIED_PROVISIONS.read_text(encoding="utf-8"))


def build_legal_path(
    citations: list[dict[str, Any]],
    *,
    source_country: str,
    recipient_country: str,
    selected_rule_id: str | None,
    income_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return the legal path in application order with verified display text."""

    selected = selected_rule_id or ""
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
    provisions = load_verified_provisions()
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
        verified = provisions.get(
            f"{source_country}-{recipient_country}|{layer}|{article}"
        )
        if verified:
            item["official_text"] = verified["text"]
            item["official_title"] = verified["title"]
            item["source_url"] = verified["source_url"]
        result.append(item)
    return result
