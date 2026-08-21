from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

STATUS_PATH = SK_DIR / "mli_relationship_status_inventory.json"
PROFILE_PATH = SK_DIR / "mli_wht_relevance_profile.json"
OUTPUT_PATH = SK_DIR / "mli_notice_machine_extraction.json"
SUMMARY_PATH = SK_DIR / "mli_notice_machine_extraction_summary.json"

MONTHS_SK = {
    "januára": 1,
    "februára": 2,
    "marca": 3,
    "apríla": 4,
    "mája": 5,
    "júna": 6,
    "júla": 7,
    "augusta": 8,
    "septembra": 9,
    "októbra": 10,
    "novembra": 11,
    "decembra": 12,
}

ARTICLE_RE = re.compile(
    r"článku\s+(\d{1,2})(?:\s+ods\.\s*[\d,\s až]+)?\s+dohovoru",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"(\d{1,2})\.\s*(januára|februára|marca|apríla|mája|júna|júla|"
    r"augusta|septembra|októbra|novembra|decembra)\s+(\d{4})",
    re.IGNORECASE,
)
WHT_TRIGGER = "v súvislosti s daňami vyberanými zrážkou pri zdroji"
SUPERSEDED_RE = re.compile(
    r"ruší\s+oznámenie\s+č\.\s*(\d+/\d{4})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FetchResult:
    url: str
    html: bytes


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _static_notice_url(notice: str) -> str:
    number, year = notice.split("/", 1)
    return (
        "https://static.slov-lex.sk/static/SK/ZZ/"
        f"{year}/{number}/vyhlasene_znenie.html"
    )


def _fetch(url: str, timeout: int = 30) -> FetchResult:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TaxTreat legal-source ingestion/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return FetchResult(url=url, html=response.read())


def _normalize_text(html: bytes | str) -> str:
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    return " ".join(soup.get_text(" ", strip=True).split())


def _parse_sk_date(day: str, month: str, year: str) -> str:
    month_number = MONTHS_SK[month.lower()]
    return date(int(year), month_number, int(day)).isoformat()


def _extract_articles(text: str) -> list[str]:
    return sorted(set(ARTICLE_RE.findall(text)), key=int)


def _extract_wht_dates(text: str) -> list[str]:
    lower = text.lower()
    cursor = 0
    dates: list[str] = []

    while True:
        position = lower.find(WHT_TRIGGER, cursor)
        if position < 0:
            break
        window = text[position : position + 650]
        match = DATE_RE.search(window)
        if match:
            parsed = _parse_sk_date(*match.groups())
            if parsed not in dates:
                dates.append(parsed)
        cursor = position + len(WHT_TRIGGER)

    return dates


def _extract_superseded_notices(text: str) -> list[str]:
    return sorted(set(SUPERSEDED_RE.findall(text)))


def _result_changing_articles(
    profile: dict[str, Any],
    applied_articles: list[str],
) -> list[str]:
    result = []
    for article in applied_articles:
        detail = profile["articles"].get(article)
        if detail and detail.get("can_change_result") is True:
            result.append(article)
    return result


def parse_notice(
    *,
    recipient_country: str,
    recipient_country_name: str,
    notice: str,
    html: bytes | str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    text = _normalize_text(html)
    applied_articles = _extract_articles(text)
    wht_dates = _extract_wht_dates(text)
    superseded = _extract_superseded_notices(text)

    source_bytes = html.encode("utf-8") if isinstance(html, str) else html
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    normalized_text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return {
        "recipient_country": recipient_country,
        "recipient_country_name": recipient_country_name,
        "slovak_notice": notice,
        "source_url": _static_notice_url(notice),
        "source_sha256": source_sha256,
        "normalized_text_sha256": normalized_text_sha256,
        "applied_mli_articles": applied_articles,
        "candidate_result_changing_articles": _result_changing_articles(
            profile,
            applied_articles,
        ),
        "wht_effective_dates": wht_dates,
        "wht_effective_date_status": (
            "machine_extracted_from_notice"
            if wht_dates
            else "not_found_requires_manual_resolution"
        ),
        "superseded_notices": superseded,
        "substantive_matching_status": (
            "machine_extracted_from_bilateral_notice"
            if applied_articles
            else "not_found_requires_manual_resolution"
        ),
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }


def build_extraction(*, fetch: bool = True) -> dict[str, Any]:
    status = _load(STATUS_PATH)
    profile = _load(PROFILE_PATH)

    if status["relationship_count"] != 46:
        raise ValueError("Expected 46 Slovak MLI relationships.")

    rows: list[dict[str, Any]] = []
    for relationship in status["relationships"]:
        notice = relationship["slovak_notice"]
        url = _static_notice_url(notice)
        if not fetch:
            rows.append({
                "recipient_country": relationship["recipient_country"],
                "recipient_country_name": relationship["recipient_country_name"],
                "slovak_notice": notice,
                "source_url": url,
                "machine_extraction_status": "not_fetched",
                "human_review_status": "not_started",
                "approval_eligible": False,
                "runtime_status": "not_released",
            })
            continue

        fetched = _fetch(url)
        parsed = parse_notice(
            recipient_country=relationship["recipient_country"],
            recipient_country_name=relationship["recipient_country_name"],
            notice=notice,
            html=fetched.html,
            profile=profile,
        )
        parsed["machine_extraction_status"] = "completed"
        rows.append(parsed)

    if len(rows) != 46:
        raise ValueError(f"Expected 46 extracted notices, found {len(rows)}.")
    if any(row["approval_eligible"] for row in rows):
        raise ValueError("Machine-extracted MLI notices cannot be legal approvals.")
    if any(row["runtime_status"] != "not_released" for row in rows):
        raise ValueError("MLI extraction must remain fail-closed.")

    return {
        "schema_version": 1,
        "dataset_release": "sk-mli-notice-machine-extraction-2026-08-19.1",
        "source_country": "SK",
        "relationship_count": 46,
        "policy": {
            "official_static_slov_lex_only": True,
            "bilateral_notice_is_machine_evidence_of_matched_effects": True,
            "machine_extraction_is_not_human_approval": True,
            "multiple_wht_effective_dates_are_preserved": True,
            "runtime_release": False,
        },
        "relationships": rows,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["relationships"]
    return {
        "schema_version": 1,
        "dataset_release": payload["dataset_release"],
        "relationship_count": len(rows),
        "machine_extraction_completed": sum(
            row.get("machine_extraction_status") == "completed"
            for row in rows
        ),
        "wht_date_extracted_relationships": sum(
            bool(row.get("wht_effective_dates")) for row in rows
        ),
        "substantive_articles_extracted_relationships": sum(
            bool(row.get("applied_mli_articles")) for row in rows
        ),
        "superseding_notice_relationships": sum(
            bool(row.get("superseded_notices")) for row in rows
        ),
        "human_reviewed_relationships": 0,
        "production_released_relationships": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_extraction(fetch=True)
    summary = build_summary(payload)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("MLI notices extracted:", summary["machine_extraction_completed"])
    print("WHT dates extracted:", summary["wht_date_extracted_relationships"])
    print(
        "Substantive article sets extracted:",
        summary["substantive_articles_extracted_relationships"],
    )
    print(
        "Superseding notices detected:",
        summary["superseding_notice_relationships"],
    )


if __name__ == "__main__":
    main()
