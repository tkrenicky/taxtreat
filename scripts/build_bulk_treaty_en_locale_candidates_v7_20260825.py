from __future__ import annotations

import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import build_bulk_treaty_en_locale_candidates_v3_20260825 as core

ROOT = core.ROOT
REGISTRY = ROOT / "data" / "web" / "cz_treaty_en_official_sources_20260825.json"
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v7_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v7_20260825.json"
MAX_WORKERS = 8

PARTNER_MARKERS = {
    "PL": ("republic of poland", "poland"),
    "SI": ("republic of slovenia", "slovenia"),
    "NO": ("kingdom of norway", "norway"),
    "NL": ("kingdom of the netherlands", "netherlands"),
    "FI": ("republic of finland", "finland"),
    "EE": ("republic of estonia", "estonia"),
    "LV": ("republic of latvia", "latvia"),
}
CZECH_MARKERS = ("czech republic", "czechia", "czechoslovak")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verified_rules() -> list[dict]:
    rules: list[dict] = []
    for path in sorted(core.RULE_DIR.glob("*.json")):
        payload = _load(path)
        for rule in payload.get("rules", []):
            if (
                rule.get("verification_status") == "verified"
                and rule.get("effect") == "rate"
                and rule.get("legal_layer") in {"treaty", "protocol", "mli"}
            ):
                rules.append(rule)
    return rules


def _pair_valid(country: str, text: str) -> bool:
    probe = " ".join(text[:14000].lower().split())
    return any(x in probe for x in CZECH_MARKERS) and any(
        x in probe for x in PARTNER_MARKERS.get(country, ())
    )


def _same_authority(original: str, resolved: str) -> bool:
    a = (urllib.parse.urlparse(original).hostname or "").lower().removeprefix("www.")
    b = (urllib.parse.urlparse(resolved).hostname or "").lower().removeprefix("www.")
    return bool(a and b and (a == b or a.endswith("." + b) or b.endswith("." + a)))


def _process(country: str, articles: dict[str, list[dict]], source: dict | None) -> tuple[dict, dict | None]:
    row = {
        "country": country,
        "status": "NO_REGISTERED_SOURCE" if not source else "NO_EN_TEXT",
        "source": source,
        "articles": {
            article: {
                "expected_rates": core._expected_rates(rules),
                "status": "NO_EN_ARTICLE",
                "excerpt_length": 0,
                "missing_rates": core._expected_rates(rules),
            }
            for article, rules in articles.items()
        },
    }
    if not source:
        return row, None

    url = str(source.get("url") or "")
    try:
        body, _, resolved = core._request(url, timeout=20)
        if not _same_authority(url, resolved):
            raise RuntimeError(f"registered source redirected outside authority boundary: {resolved}")
        text = core._document_text(body, resolved)
    except Exception as exc:
        row["status"] = "SOURCE_ERROR"
        row["error"] = f"{type(exc).__name__}: {exc}"
        return row, None

    row["resolved_url"] = resolved
    row["text_length"] = len(text)
    if not _pair_valid(country, text):
        row["status"] = "WRONG_TREATY_PAIR"
        return row, None

    best: dict[str, dict] = {}
    for article, rules in articles.items():
        result, excerpt = core._analyse_article(text, article, rules)
        row["articles"][article] = result
        if excerpt:
            best[article] = {
                "en": {
                    "language": "en",
                    "status": "candidate_official_treaty_text",
                    "authority": source.get("authority"),
                    "source_url": resolved,
                    "text": excerpt,
                }
            }

    pass_count = sum(1 for x in row["articles"].values() if x["status"] == "PASS")
    review_count = sum(1 for x in row["articles"].values() if x["status"] == "REVIEW")
    if pass_count == len(articles):
        row["status"] = "PASS"
    elif pass_count:
        row["status"] = "PARTIAL"
    elif review_count:
        row["status"] = "REVIEW"
    else:
        row["status"] = "NO_EN_TEXT"

    candidate = None
    if best:
        candidate = {
            "schema_version": 1,
            "source_country": "CZ",
            "recipient_country": country,
            "candidate_only": True,
            "articles": best,
        }
    return row, candidate


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registered = (_load(REGISTRY).get("entries") or {})
    covered = core._covered_pairs()
    grouped: dict[tuple[str, str], list[dict]] = {}
    for rule in _verified_rules():
        country = str(rule.get("recipient_country") or "").upper()
        article = str(rule.get("article") or "").strip()
        if country and article and (country, article) not in covered:
            grouped.setdefault((country, article), []).append(rule)
    countries: dict[str, dict[str, list[dict]]] = {}
    for (country, article), rules in grouped.items():
        countries.setdefault(country, {})[article] = rules

    print(f"Explicit official EN treaty extraction v7: missing={len(grouped)} pairs, registered={len(registered)} countries", flush=True)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(_process, country, articles, registered.get(country)): country
            for country, articles in sorted(countries.items())
        }
        done = 0
        for future in as_completed(futures):
            country = futures[future]
            done += 1
            try:
                row, candidate = future.result()
            except Exception as exc:
                row, candidate = {"country": country, "status": "WORKER_ERROR", "error": f"{type(exc).__name__}: {exc}", "articles": {}}, None
            results.append(row)
            if candidate:
                (OUT_DIR / f"{country}.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if country in registered:
                print(f"[{done}/{len(countries)}] {country}: {row['status']}", flush=True)

    results.sort(key=lambda x: x["country"])
    counts: dict[str, int] = {}
    passes = reviews = 0
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        passes += sum(1 for x in row.get("articles", {}).values() if x.get("status") == "PASS")
        reviews += sum(1 for x in row.get("articles", {}).values() if x.get("status") == "REVIEW")
    payload = {
        "schema_version": 1,
        "registered_source_count": len(registered),
        "missing_country_article_pairs_at_start": len(grouped),
        "countries_scanned": len(results),
        "country_status_counts": counts,
        "article_candidates_pass": passes,
        "article_candidates_review": reviews,
        "results": results,
    }
    SUMMARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"v7 counts: {json.dumps(counts, sort_keys=True)}", flush=True)
    print(f"Article PASS={passes} REVIEW={reviews}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
