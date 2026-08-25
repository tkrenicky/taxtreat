from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import build_bulk_treaty_en_locale_candidates_v4_20260825 as v4

ROOT = v4.ROOT
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v5_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v5_20260825.json"
SOURCE_CACHE = ROOT / "reports" / "treaty_en_official_source_cache_v5_20260825.json"
MAX_WORKERS = 8
MAX_URLS_PER_COUNTRY = 40

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
COUNTRY_KEYS = {
    "country", "iso2", "recipient_country", "partner_country", "jurisdiction",
    "country_code", "partner", "recipient", "source_country",
}
URL_KEYS = {
    "url", "source_url", "official_source_url", "resolved_pdf_url", "resolved_url",
    "pdf_url", "document_url", "evidence_url", "href",
}


def _json_files() -> list[Path]:
    paths: list[Path] = []
    for base in (ROOT / "data", ROOT / "reports"):
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            if path in {SUMMARY, SOURCE_CACHE}:
                continue
            # Generated locale candidate outputs are not source evidence.
            if "treaty_en_locale_bulk_candidates" in str(path):
                continue
            paths.append(path)
    return sorted(set(paths))


def _country_values(node: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for key, value in node.items():
        if key.lower() not in COUNTRY_KEYS:
            continue
        if isinstance(value, str):
            token = value.strip().upper()
            if len(token) == 2 and token.isalpha() and token != "CZ":
                out.add(token)
    return out


def _urls_in_value(value: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(value, str):
        urls.extend(URL_RE.findall(value))
    elif isinstance(value, list):
        for item in value:
            urls.extend(_urls_in_value(item))
    elif isinstance(value, dict):
        for item in value.values():
            urls.extend(_urls_in_value(item))
    return urls


def _walk(node: Any, inherited: set[str], collected: dict[str, list[dict]], path: Path) -> None:
    if isinstance(node, dict):
        local = set(inherited)
        local.update(_country_values(node))

        direct_urls: list[str] = []
        for key, value in node.items():
            if key.lower() in URL_KEYS:
                direct_urls.extend(_urls_in_value(value))
        if local and direct_urls:
            for country in local:
                for url in direct_urls:
                    collected.setdefault(country, []).append({
                        "url": url.rstrip(".,);]"),
                        "origin": str(path.relative_to(ROOT)),
                    })

        for value in node.values():
            _walk(value, local, collected, path)
    elif isinstance(node, list):
        for item in node:
            _walk(item, inherited, collected, path)


def _harvest_local_sources() -> tuple[dict[str, list[dict]], dict[str, int]]:
    collected: dict[str, list[dict]] = {}
    stats = {"json_files_scanned": 0, "json_parse_errors": 0, "raw_links": 0}
    for path in _json_files():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            stats["json_parse_errors"] += 1
            continue
        stats["json_files_scanned"] += 1
        _walk(payload, set(), collected, path)

    cleaned: dict[str, list[dict]] = {}
    for country, entries in collected.items():
        seen: set[str] = set()
        for entry in entries:
            url = entry["url"]
            if url in seen or not url.startswith("http"):
                continue
            seen.add(url)
            cleaned.setdefault(country, []).append(entry)
            stats["raw_links"] += 1
    return cleaned, stats


def _official_or_governmentish(country: str, url: str) -> bool:
    if v4._is_official(country, url):
        return True
    host = v4._host(url)
    # Local evidence registries are allowed to introduce official domains not yet present
    # in the hard-coded hint map, but only if the hostname itself is government-like.
    return any(token in host for token in (
        ".gov.", ".gouv.", ".gob.", ".gv.", ".go.", ".admin.",
        "minfin", "finance", "financ", "tax", "revenue", "legis", "law",
    ))


def _source_urls_for_country(country: str, harvested: dict[str, list[dict]]) -> list[dict]:
    result: list[dict] = []
    seen: set[str] = set()
    for entry in harvested.get(country, []):
        url = entry["url"]
        if url in seen or not _official_or_governmentish(country, url):
            continue
        seen.add(url)
        result.append(entry)
        if len(result) >= MAX_URLS_PER_COUNTRY:
            break
    return result


def _process_country(country: str, articles: dict[str, list[dict]], harvested: dict[str, list[dict]]) -> tuple[dict, dict | None]:
    sources = _source_urls_for_country(country, harvested)
    row = {
        "country": country,
        "status": "NO_LOCAL_OFFICIAL_SOURCE" if not sources else "NO_EN_TEXT",
        "sources_discovered": len(sources),
        "source_attempts": [],
        "articles": {
            article: {
                "expected_rates": v4._expected_rates(article_rules),
                "status": "NO_EN_ARTICLE",
                "excerpt_length": 0,
                "missing_rates": v4._expected_rates(article_rules),
            }
            for article, article_rules in articles.items()
        },
    }
    best_locales: dict[str, dict] = {}

    for source in sources:
        url = source["url"]
        attempt = {"url": url, "origin": source["origin"], "status": "SOURCE_RESOLUTION"}
        try:
            body, resolved = v4._discover_document(url)
            if not _official_or_governmentish(country, resolved):
                raise RuntimeError("resolved URL is outside official/government boundary")
            text = v4._document_text(body, resolved)
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
            candidate, excerpt = v4._analyse_article(text, article, article_rules)
            attempt["articles"][article] = candidate["status"]
            current = row["articles"][article]
            if v4.STATUS_RANK[candidate["status"]] > v4.STATUS_RANK[current["status"]]:
                row["articles"][article] = candidate
                if excerpt:
                    best_locales[article] = {
                        "en": {
                            "language": "en",
                            "status": "candidate_official_treaty_text",
                            "authority": v4._host(resolved),
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
    rules = v4._verified_treaty_rules()
    covered = v4._covered_pairs()
    grouped: dict[tuple[str, str], list[dict]] = {}
    for rule in rules:
        country = str(rule.get("recipient_country") or "").upper()
        article = str(rule.get("article") or "").strip()
        if country and article and (country, article) not in covered:
            grouped.setdefault((country, article), []).append(rule)
    countries: dict[str, dict[str, list[dict]]] = {}
    for (country, article), article_rules in grouped.items():
        countries.setdefault(country, {})[article] = article_rules

    harvested, harvest_stats = _harvest_local_sources()
    eligible = sum(1 for country in countries if _source_urls_for_country(country, harvested))
    print(
        f"Bulk official EN treaty extraction v5: {len(countries)} countries, "
        f"local_json={harvest_stats['json_files_scanned']}, harvested_urls={harvest_stats['raw_links']}, "
        f"countries_with_local_sources={eligible}, workers={MAX_WORKERS}",
        flush=True,
    )

    cache_payload = {
        "schema_version": 1,
        "harvest_stats": harvest_stats,
        "countries": {
            country: _source_urls_for_country(country, harvested)
            for country in sorted(countries)
            if _source_urls_for_country(country, harvested)
        },
    }
    SOURCE_CACHE.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        article_pass += sum(1 for value in row.get("articles", {}).values() if value.get("status") == "PASS")
        article_review += sum(1 for value in row.get("articles", {}).values() if value.get("status") == "REVIEW")

    summary = {
        "schema_version": 1,
        "missing_country_article_pairs_at_start": len(grouped),
        "countries_scanned": len(results),
        "harvest_stats": harvest_stats,
        "countries_with_local_sources": eligible,
        "country_status_counts": counts,
        "article_candidates_pass": article_pass,
        "article_candidates_review": article_review,
        "source_cache": str(SOURCE_CACHE.relative_to(ROOT)),
        "results": results,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Bulk official EN treaty locale candidate extraction v5")
    print(f"Country status counts: {json.dumps(counts, sort_keys=True)}")
    print(f"Article candidates PASS: {article_pass}")
    print(f"Article candidates REVIEW: {article_review}")
    print(f"Summary: {SUMMARY.relative_to(ROOT)}")
    print(f"Candidates: {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
