from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import build_bulk_treaty_en_locale_candidates_v3_20260825 as core
import build_bulk_treaty_en_locale_candidates_v4_20260825 as v4
import build_bulk_treaty_en_locale_candidates_v5_20260825 as v5

ROOT = core.ROOT
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v6_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v6_20260825.json"
SOURCE_CACHE = ROOT / "reports" / "treaty_en_official_source_cache_v6_20260825.json"
MAX_WORKERS = v5.MAX_WORKERS

CZECH_MARKERS = (
    "czech republic",
    "czechia",
    "czechoslovak",
    "czech socialist republic",
    "ceska republika",
    "česká republika",
)


def _is_czech_pair_document(text: str, resolved_url: str) -> bool:
    haystack = (resolved_url + "\n" + text[:30000]).lower()
    return any(marker in haystack for marker in CZECH_MARKERS)


def _process_country(country: str, articles: dict[str, list[dict]], harvested: dict[str, list[dict]]) -> tuple[dict, dict | None]:
    sources = v5._source_urls_for_country(country, harvested)
    row = {
        "country": country,
        "status": "NO_LOCAL_OFFICIAL_SOURCE" if not sources else "NO_EN_TEXT",
        "sources_discovered": len(sources),
        "source_attempts": [],
        "articles": {
            article: {
                "expected_rates": core._expected_rates(article_rules),
                "status": "NO_EN_ARTICLE",
                "excerpt_length": 0,
                "missing_rates": core._expected_rates(article_rules),
            }
            for article, article_rules in articles.items()
        },
    }
    best_locales: dict[str, dict] = {}

    for source in sources:
        url = source["url"]
        attempt = {"url": url, "origin": source["origin"], "status": "SOURCE_RESOLUTION"}
        try:
            body, resolved = v4._discover_document_bounded(url)
            if not v5._official_or_governmentish(country, resolved):
                raise RuntimeError("resolved URL is outside official/government boundary")
            text = core._document_text(body, resolved)
            if not _is_czech_pair_document(text, resolved):
                attempt["status"] = "WRONG_TREATY_PAIR"
                attempt["resolved_url"] = resolved
                row["source_attempts"].append(attempt)
                continue
        except Exception as exc:
            attempt["status"] = "ERROR"
            attempt["error"] = f"{type(exc).__name__}: {exc}"
            row["source_attempts"].append(attempt)
            continue

        attempt["status"] = "PARSED"
        attempt["resolved_url"] = resolved
        attempt["text_length"] = len(text)
        attempt["articles"] = {}
        for article, article_rules in articles.items():
            candidate, excerpt = core._analyse_article(text, article, article_rules)
            attempt["articles"][article] = candidate["status"]
            current = row["articles"][article]
            if core.STATUS_RANK[candidate["status"]] > core.STATUS_RANK[current["status"]]:
                row["articles"][article] = candidate
                if excerpt:
                    best_locales[article] = {
                        "en": {
                            "language": "en",
                            "status": "candidate_official_treaty_text",
                            "authority": core._host(resolved),
                            "source_url": resolved,
                            "text": excerpt,
                        }
                    }
        row["source_attempts"].append(attempt)
        if all(value["status"] == "PASS" for value in row["articles"].values()):
            break

    pass_count = sum(1 for value in row["articles"].values() if value["status"] == "PASS")
    review_count = sum(1 for value in row["articles"].values() if value["status"] == "REVIEW")
    if pass_count == len(articles):
        row["status"] = "PASS"
    elif pass_count:
        row["status"] = "PARTIAL"
    elif review_count:
        row["status"] = "REVIEW"
    elif sources:
        row["status"] = "NO_EN_TEXT"

    candidate_payload = None
    if best_locales:
        candidate_payload = {
            "schema_version": 1,
            "source_country": "CZ",
            "recipient_country": country,
            "candidate_only": True,
            "articles": best_locales,
        }
    return row, candidate_payload


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUT_DIR.glob("*.json"):
        stale.unlink()

    rules = core._verified_treaty_rules()
    covered = core._covered_pairs()
    grouped: dict[tuple[str, str], list[dict]] = {}
    for rule in rules:
        country = str(rule.get("recipient_country") or "").upper()
        article = str(rule.get("article") or "").strip()
        if country and article and (country, article) not in covered:
            grouped.setdefault((country, article), []).append(rule)

    countries: dict[str, dict[str, list[dict]]] = {}
    for (country, article), article_rules in grouped.items():
        countries.setdefault(country, {})[article] = article_rules

    harvested, harvest_stats = v5._harvest_local_sources()
    eligible = sum(1 for country in countries if v5._source_urls_for_country(country, harvested))
    print(
        f"Bulk official EN treaty extraction v6: {len(countries)} countries, "
        f"local_json={harvest_stats['json_files_scanned']}, harvested_urls={harvest_stats['raw_links']}, "
        f"countries_with_local_sources={eligible}, workers={MAX_WORKERS}",
        flush=True,
    )

    SOURCE_CACHE.write_text(json.dumps({
        "schema_version": 1,
        "harvest_stats": harvest_stats,
        "countries": {
            country: v5._source_urls_for_country(country, harvested)
            for country in sorted(countries)
            if v5._source_urls_for_country(country, harvested)
        },
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    results: list[dict] = []
    total = len(countries)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_process_country, country, articles, harvested): country
            for country, articles in countries.items()
        }
        done = 0
        for future in as_completed(futures):
            country = futures[future]
            done += 1
            try:
                row, candidate = future.result()
            except Exception as exc:
                row = {"country": country, "status": "WORKER_ERROR", "error": f"{type(exc).__name__}: {exc}", "articles": {}}
                candidate = None
            results.append(row)
            if candidate:
                (OUT_DIR / f"{country}.json").write_text(
                    json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            print(f"[{done}/{total}] {country}: {row['status']} ({row.get('sources_discovered', 0)} sources)", flush=True)

    results.sort(key=lambda row: row["country"])
    counts: dict[str, int] = {}
    article_pass = 0
    article_review = 0
    wrong_pair = 0
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        article_pass += sum(1 for value in row.get("articles", {}).values() if value.get("status") == "PASS")
        article_review += sum(1 for value in row.get("articles", {}).values() if value.get("status") == "REVIEW")
        wrong_pair += sum(1 for attempt in row.get("source_attempts", []) if attempt.get("status") == "WRONG_TREATY_PAIR")

    summary = {
        "schema_version": 1,
        "missing_country_article_pairs_at_start": len(grouped),
        "countries_scanned": len(results),
        "harvest_stats": harvest_stats,
        "countries_with_local_sources": eligible,
        "wrong_treaty_pair_documents_rejected": wrong_pair,
        "country_status_counts": counts,
        "article_candidates_pass": article_pass,
        "article_candidates_review": article_review,
        "source_cache": str(SOURCE_CACHE.relative_to(ROOT)),
        "results": results,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Bulk official EN treaty locale candidate extraction v6", flush=True)
    print(f"Wrong treaty-pair documents rejected: {wrong_pair}", flush=True)
    print(f"Country status counts: {json.dumps(counts, sort_keys=True)}", flush=True)
    print(f"Article candidates PASS: {article_pass}", flush=True)
    print(f"Article candidates REVIEW: {article_review}", flush=True)
    print(f"Summary: {SUMMARY.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
