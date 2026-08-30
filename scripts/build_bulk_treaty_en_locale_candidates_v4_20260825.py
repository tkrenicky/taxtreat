from __future__ import annotations

import concurrent.futures
import json
import os
import urllib.parse
from pathlib import Path

import build_bulk_treaty_en_locale_candidates_v3_20260825 as core


ROOT = core.ROOT
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v4_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v4_20260825.json"
SOURCE_CACHE = ROOT / "reports" / "treaty_en_official_source_cache_v4_20260825.json"
MAX_COUNTRY_WORKERS = max(2, min(int(os.environ.get("TAXTREAT_EN_WORKERS", "8")), 12))
SEARCH_TIMEOUT = int(os.environ.get("TAXTREAT_EN_SEARCH_TIMEOUT", "7"))
DOC_TIMEOUT = int(os.environ.get("TAXTREAT_EN_DOC_TIMEOUT", "10"))
MAX_DISCOVERED_URLS = 8

# Search endpoints are discovery-only. Evidence acceptance remains restricted to the
# country-specific official-domain allowlist in the v3 core.
SEARCH_ENDPOINTS = (
    "https://www.bing.com/search?q={query}",
    "https://html.duckduckgo.com/html/?q={query}",
)


def _load_cache() -> dict[str, list[str]]:
    if not SOURCE_CACHE.exists():
        return {}
    try:
        payload = core._load_json(SOURCE_CACHE)
    except Exception:
        return {}
    return {str(k).upper(): list(v or []) for k, v in (payload.get("countries") or {}).items()}


def _search_one(country: str, domain: str, template: str) -> list[str]:
    query = urllib.parse.quote_plus(
        f'site:{domain} "Czech Republic" tax treaty convention English pdf'
    )
    try:
        body, _, final_url = core._request(template.format(query=query), timeout=SEARCH_TIMEOUT)
    except Exception:
        return []
    result: list[str] = []
    for url in core._links_from_html(body, final_url):
        if core._is_official(country, url):
            result.append(url)
    return result


def _discover_fast(country: str) -> list[str]:
    hints = core.OFFICIAL_DOMAIN_HINTS.get(country.lower(), ())
    if not hints:
        return []
    jobs = [(domain, endpoint) for domain in hints[:3] for endpoint in SEARCH_ENDPOINTS]
    urls: list[str] = []
    seen: set[str] = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(jobs) or 1)) as pool:
        futures = [pool.submit(_search_one, country, domain, endpoint) for domain, endpoint in jobs]
        for future in concurrent.futures.as_completed(futures):
            try:
                found = future.result()
            except Exception:
                found = []
            for url in found:
                if url not in seen:
                    seen.add(url)
                    urls.append(url)
                    if len(urls) >= MAX_DISCOVERED_URLS:
                        return urls
    return urls


def _discover_document_bounded(url: str) -> tuple[bytes, str]:
    body, content_type, final_url = core._request(url, timeout=DOC_TIMEOUT)
    if content_type == "application/pdf" or body[:4] == b"%PDF":
        return body, final_url

    links = core._links_from_html(body, final_url)
    scored: list[tuple[int, str]] = []
    for link in links:
        lower = link.lower()
        score = 0
        if ".pdf" in lower or "download" in lower or "viewfile" in lower:
            score += 5
        if any(token in lower for token in ("treat", "convention", "double", "tax", "czech", "cesk")):
            score += 3
        if any(token in lower for token in ("english", "engl", "en_", "/en/", "lang=en")):
            score += 2
        if score:
            scored.append((score, link))

    for _, candidate in sorted(scored, reverse=True)[:6]:
        try:
            candidate_body, candidate_type, resolved = core._request(candidate, timeout=DOC_TIMEOUT)
        except Exception:
            continue
        if candidate_type == "application/pdf" or candidate_body[:4] == b"%PDF":
            return candidate_body, resolved
        if candidate_type in {"text/html", "application/xhtml+xml", "text/plain"}:
            return candidate_body, resolved

    if content_type in {"text/html", "application/xhtml+xml", "text/plain"}:
        return body, final_url
    raise RuntimeError("official source did not resolve to usable treaty text")


def _process_country(country: str, articles: dict[str, list[dict]], cached: list[str]) -> tuple[dict, list[str]]:
    discovered = list(cached)
    if not discovered:
        discovered = _discover_fast(country)

    row = {
        "country": country,
        "status": "NO_OFFICIAL_EN_SOURCE" if not discovered else "NO_EN_TEXT",
        "sources_discovered": len(discovered),
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

    for source_url in discovered[:MAX_DISCOVERED_URLS]:
        if not core._is_official(country, source_url):
            continue
        attempt = {"url": source_url, "status": "SOURCE_RESOLUTION"}
        try:
            body, resolved = _discover_document_bounded(source_url)
            if not core._is_official(country, resolved):
                raise RuntimeError("resolved document left official-domain boundary")
            text = core._document_text(body, resolved)
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
    elif discovered:
        row["status"] = "NO_EN_TEXT"

    if best_locales:
        payload = {
            "schema_version": 1,
            "source_country": "CZ",
            "recipient_country": country,
            "candidate_only": True,
            "articles": best_locales,
        }
        (OUT_DIR / f"{country}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return row, discovered


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rules = core._verified_treaty_rules()
    covered = core._covered_pairs()
    cache = _load_cache()

    grouped: dict[tuple[str, str], list[dict]] = {}
    for rule in rules:
        country = str(rule.get("recipient_country") or "").upper()
        article = str(rule.get("article") or "").strip()
        if country and article and (country, article) not in covered:
            grouped.setdefault((country, article), []).append(rule)

    countries: dict[str, dict[str, list[dict]]] = {}
    for (country, article), article_rules in grouped.items():
        countries.setdefault(country, {})[article] = article_rules

    total = len(countries)
    print(
        f"Bulk official EN treaty extraction v4: {total} countries, "
        f"workers={MAX_COUNTRY_WORKERS}, search_timeout={SEARCH_TIMEOUT}s, doc_timeout={DOC_TIMEOUT}s",
        flush=True,
    )

    results: list[dict] = []
    updated_cache = dict(cache)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_COUNTRY_WORKERS) as pool:
        futures = {
            pool.submit(_process_country, country, articles, cache.get(country, [])): country
            for country, articles in sorted(countries.items())
        }
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            country = futures[future]
            completed += 1
            try:
                row, discovered = future.result()
            except Exception as exc:
                row = {
                    "country": country,
                    "status": "WORKER_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                    "articles": {},
                }
                discovered = []
            if discovered:
                updated_cache[country] = discovered
            results.append(row)
            print(f"[{completed}/{total}] {country}: {row['status']}", flush=True)

    results.sort(key=lambda row: row["country"])
    SOURCE_CACHE.write_text(
        json.dumps({"schema_version": 1, "countries": updated_cache}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

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
        "country_status_counts": counts,
        "article_candidates_pass": article_pass,
        "article_candidates_review": article_review,
        "source_cache": str(SOURCE_CACHE.relative_to(ROOT)),
        "results": results,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nBulk official EN treaty locale candidate extraction v4", flush=True)
    print(f"Country status counts: {json.dumps(counts, sort_keys=True)}", flush=True)
    print(f"Article candidates PASS: {article_pass}", flush=True)
    print(f"Article candidates REVIEW: {article_review}", flush=True)
    print(f"Summary: {SUMMARY.relative_to(ROOT)}", flush=True)
    print(f"Candidates: {OUT_DIR.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
