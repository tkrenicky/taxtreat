from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


_LOCALE_ROOT = Path(__file__).resolve().parents[2] / "app" / "web" / "treaty-excerpt-locales"

_STATUS_LABELS = {
    "official_treaty_text": "Official English treaty text",
    "official_synthesised_text": "Official synthesised English text",
    "official_protocol_text": "Official English protocol text",
    "official_translation_non_authentic": "Official English translation — non-authentic",
    "machine_translation_from_official_text": "Machine translation from official text",
    "verified_stage6_rule_summary": "Verified English rule summary — not treaty wording",
    "current_application_suspended": "Current application suspended",
}


def _read_locale(recipient_country: str) -> Mapping[str, Any] | None:
    code = str(recipient_country or "").strip().upper()
    if not code or not code.isalnum():
        return None
    path = _LOCALE_ROOT / f"{code}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def english_excerpt_for_citation(
    citation: Mapping[str, Any], recipient_country: str
) -> dict[str, Any] | None:
    """Return verified EN locale metadata for a treaty/protocol/MLI citation.

    Rule-specific entries take precedence over article-level entries. Missing or
    malformed locale data fails closed by returning None; the caller must not
    relabel the canonical excerpt as English in that case.
    """
    locale = _read_locale(recipient_country)
    if not locale:
        return None

    rule_id = str(citation.get("rule_id") or "")
    article = str(citation.get("article") or "")
    entry: Mapping[str, Any] | None = None

    rules = locale.get("rules")
    if rule_id and isinstance(rules, dict):
        candidate = rules.get(rule_id)
        if isinstance(candidate, dict):
            entry = candidate

    if entry is None and article:
        articles = locale.get("articles")
        if isinstance(articles, dict):
            candidate = articles.get(article)
            if isinstance(candidate, dict):
                entry = candidate

    if not entry:
        return None
    en = entry.get("en")
    if not isinstance(en, dict):
        return None
    text = str(en.get("text") or "").strip()
    status = str(en.get("status") or "").strip()
    if not text or not status:
        return None

    return {
        "excerpt": text,
        "excerpt_language": "en",
        "excerpt_status": status,
        "excerpt_status_label": _STATUS_LABELS.get(status, status.replace("_", " ").title()),
        "excerpt_authority": str(en.get("authority") or "").strip() or None,
        "excerpt_source_url": str(en.get("source_url") or "").strip() or None,
    }
