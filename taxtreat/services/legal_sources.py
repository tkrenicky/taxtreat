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


@lru_cache(maxsize=1)
def load_verified_provisions() -> dict[str, dict[str, str]]:
    return json.loads(VERIFIED_PROVISIONS.read_text(encoding="utf-8"))


def build_legal_path(
    citations: list[dict[str, Any]],
    *,
    source_country: str,
    recipient_country: str,
    selected_rule_id: str | None,
) -> list[dict[str, Any]]:
    """Return the legal path in application order with verified display text."""

    selected = selected_rule_id or ""
    ordered = sorted(
        citations,
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
