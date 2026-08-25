from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

DEFAULT_PILOT = Path("artifacts/at/instrument_chain_pilot.json")
DEFAULT_ARTICLES = Path("artifacts/at/article_candidate_inventory.json")
DEFAULT_OUTPUT = Path("artifacts/at/treaty_language_evidence.json")

LANGUAGE_MARKERS = {
    "de": ("deutsch", "deutscher", "german"),
    "en": ("englisch", "englischer", "english"),
}


def _artifact_path(path_value: str, artifact_root: Path) -> Path:
    path = Path(path_value)
    parts = path.parts
    if len(parts) >= 2 and parts[0] == "artifacts" and parts[1] == "at":
        path = Path(*parts[2:])
    return artifact_root / path


def _language_from_text(value: str) -> str | None:
    lowered = value.lower()
    for language, markers in LANGUAGE_MARKERS.items():
        if any(marker in lowered for marker in markers):
            return language
    return None


def _attachment_label(parent: dict[str, Any], child_url: str, *, artifact_root: Path) -> str:
    parent_path = _artifact_path(str(parent.get("artifact_path") or ""), artifact_root)
    content_type = str(parent.get("content_type") or "").lower()
    if not parent_path.is_file() or "html" not in content_type:
        return ""
    soup = BeautifulSoup(parent_path.read_bytes(), "lxml")
    base_url = str(parent.get("final_url") or "")
    for anchor in soup.find_all("a", href=True):
        candidate = urljoin(base_url, str(anchor["href"]))
        if candidate != child_url:
            continue
        image = anchor.find("img")
        return " ".join(
            " ".join(
                [
                    anchor.get_text(" ", strip=True),
                    str(anchor.get("title") or ""),
                    str(image.get("alt") or "") if image is not None else "",
                ]
            ).split()
        )
    return ""


def classify_source_language(
    source: dict[str, Any],
    *,
    sources_by_url: dict[str, dict[str, Any]],
    artifact_root: Path,
) -> tuple[str, str]:
    final_url = str(source.get("final_url") or "")
    discovered_from = str(source.get("discovered_from_url") or "")
    if discovered_from:
        parent = sources_by_url.get(discovered_from)
        if parent is not None:
            label = _attachment_label(parent, final_url, artifact_root=artifact_root)
            language = _language_from_text(label)
            if language:
                return language, "ris_attachment_label"

    language = _language_from_text(final_url)
    if language:
        return language, "url_language_marker"

    if source.get("role_candidate") == "current_consolidated_view":
        return "de", "official_austrian_consolidated_view"

    return "unknown", "not_determined"


def build_language_evidence(
    pilot: dict[str, Any],
    article_inventory: dict[str, Any],
    *,
    artifact_root: Path,
) -> dict[str, Any]:
    if pilot.get("source_country") != "AT" or article_inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian acquisition and article inventories")
    if pilot.get("pilot_partner_count") != 89 or article_inventory.get("partner_count") != 89:
        raise ValueError("AT language evidence requires the full 89-partner acquisition universe")

    article_partners = {str(row.get("partner_label")): row for row in article_inventory.get("partners", [])}
    rows: list[dict[str, Any]] = []
    for partner in pilot.get("partners", []):
        label = str(partner.get("partner_label") or "")
        article_partner = article_partners.get(label)
        if article_partner is None:
            raise ValueError(f"Missing AT article inventory partner: {label}")

        sources = list(partner.get("sources", []))
        sources_by_url = {str(row.get("final_url") or ""): row for row in sources}
        source_languages: dict[str, tuple[str, str]] = {}
        source_rows: list[dict[str, Any]] = []
        for source in sources:
            language, method = classify_source_language(
                source,
                sources_by_url=sources_by_url,
                artifact_root=artifact_root,
            )
            sha = str(source.get("sha256") or "")
            source_languages[sha] = (language, method)
            source_rows.append(
                {
                    "source_order": source.get("source_order"),
                    "final_url": source.get("final_url"),
                    "source_sha256": sha,
                    "role_candidate": source.get("role_candidate"),
                    "language_candidate": language,
                    "language_evidence_method": method,
                    "text_authority_candidate": "not_adjudicated",
                    "legal_review_completed": False,
                    "web_wording_released": False,
                }
            )

        article_rows: list[dict[str, Any]] = []
        for source in article_partner.get("sources", []):
            source_sha = str(source.get("source_sha256") or "")
            language, method = source_languages.get(source_sha, ("unknown", "not_determined"))
            for candidate in source.get("article_candidates", []):
                if candidate.get("substantive_article_candidate") is not True:
                    continue
                article_rows.append(
                    {
                        "article_number": candidate.get("article_number"),
                        "text_sha256": candidate.get("text_sha256"),
                        "artifact_path": candidate.get("artifact_path"),
                        "semantic_income_candidate": candidate.get("semantic_income_candidate"),
                        "source_sha256": source_sha,
                        "language_candidate": language,
                        "language_evidence_method": method,
                        "text_authority_candidate": "not_adjudicated",
                        "controlling_text_selected": False,
                        "web_wording_released": False,
                    }
                )

        languages = {row["language_candidate"] for row in source_rows}
        rows.append(
            {
                "partner_label": label,
                "source_language_evidence": source_rows,
                "article_language_evidence": article_rows,
                "language_evidence_coverage_machine": {
                    "german_official_source_candidate_available": "de" in languages,
                    "english_official_source_candidate_available": "en" in languages,
                    "unknown_language_source_count": sum(
                        row["language_candidate"] == "unknown" for row in source_rows
                    ),
                },
                "step4_web_wording_readiness": {
                    "de": False,
                    "en": False,
                    "reason": "controlling treaty instrument and language authority have not been legally adjudicated",
                },
                "translated_en_from_controlling_text": {
                    "status": "not_created",
                    "source_language": None,
                    "source_text_sha256": None,
                    "translation_text": None,
                },
                "legal_review_completed": False,
                "language_authority_review_completed": False,
                "web_wording_released": False,
            }
        )

    return {
        "schema_version": 1,
        "source_country": "AT",
        "status": "treaty_language_evidence_candidates_not_reviewed",
        "partner_count": len(rows),
        "partners": rows,
        "policy": {
            "official_source_presence_does_not_establish_controlling_text": True,
            "german_and_english_wording_are_tracked_separately": True,
            "language_candidate_does_not_establish_authenticity": True,
            "text_authority_requires_treaty_specific_review": True,
            "machine_translation_must_never_be_presented_as_authentic_treaty_text": True,
            "translated_english_may_be_created_only_from_selected_controlling_text": True,
            "step4_wording_requires_controlling_text_and_language_authority_review": True,
            "no_web_wording_is_released_by_this_inventory": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=Path, default=DEFAULT_PILOT)
    parser.add_argument("--articles", type=Path, default=DEFAULT_ARTICLES)
    parser.add_argument("--artifact-root", type=Path, default=Path("artifacts/at"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    pilot = json.loads(args.pilot.read_text(encoding="utf-8"))
    articles = json.loads(args.articles.read_text(encoding="utf-8"))
    result = build_language_evidence(pilot, articles, artifact_root=args.artifact_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    de_count = sum(
        row["language_evidence_coverage_machine"]["german_official_source_candidate_available"]
        for row in result["partners"]
    )
    en_count = sum(
        row["language_evidence_coverage_machine"]["english_official_source_candidate_available"]
        for row in result["partners"]
    )
    print(f"AT treaty language evidence: {result['partner_count']} partners / DE candidates {de_count} / EN candidates {en_count}")


if __name__ == "__main__":
    main()
