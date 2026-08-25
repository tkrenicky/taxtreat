from __future__ import annotations

import json
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import build_bulk_treaty_en_locale_candidates_v3_20260825 as core

ROOT = core.ROOT
REGISTRY = ROOT / "data" / "web" / "cz_treaty_en_official_sources_20260825.json"
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v9_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v9_20260825.json"
MAX_WORKERS = 8
STATUS_RANK = {"NO_EN_ARTICLE": 0, "REVIEW": 1, "PASS": 2}
PARTNER_MARKERS = {
    "PL": ("poland", "republic of poland"), "SI": ("slovenia",), "NO": ("norway",),
    "NL": ("netherlands",), "FI": ("finland",), "EE": ("estonia",), "LV": ("latvia",),
    "MT": ("malta",), "DK": ("denmark", "kingdom of denmark"), "ID": ("indonesia",),
    "TH": ("thailand", "kingdom of thailand"), "TW": ("taipei", "taiwan", "czech economic and cultural office"),
}
CZECH_MARKERS = ("czech republic", "czechia", "czechoslovak", "czech economic and cultural office")
SUBJECT = {"10": "dividend", "11": "interest", "12": "royalt"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rules() -> list[dict]:
    result = []
    for path in sorted(core.RULE_DIR.glob("*.json")):
        for rule in _load(path).get("rules", []):
            if rule.get("verification_status") == "verified" and rule.get("effect") == "rate" and rule.get("legal_layer") in {"treaty", "protocol", "mli"}:
                result.append(rule)
    return result


def _same_host_family(a: str, b: str) -> bool:
    ah = (urllib.parse.urlparse(a).hostname or "").lower().removeprefix("www.")
    bh = (urllib.parse.urlparse(b).hostname or "").lower().removeprefix("www.")
    return bool(ah and bh and (ah == bh or ah.endswith("." + bh) or bh.endswith("." + ah)))


def _pair_valid(country: str, text: str) -> bool:
    probe = " ".join(text[:30000].lower().split())
    return any(x in probe for x in CZECH_MARKERS) and any(x in probe for x in PARTNER_MARKERS.get(country, ()))


def _extract_flexible(text: str, article: str, rules: list[dict]) -> str | None:
    raw = text.replace("\r", "\n").replace("\u00a0", " ")
    start_re = re.compile(rf"(?im)^\s*article\s+(?:no\.?\s*)?{re.escape(article)}\b")
    matches = list(start_re.finditer(raw))
    if not matches:
        start_re = re.compile(rf"(?i)\barticle\s+(?:no\.?\s*)?{re.escape(article)}\b")
        matches = list(start_re.finditer(raw))
    if not matches:
        return None
    best: tuple[int, str] | None = None
    expected = core._expected_rates(rules)
    subject = SUBJECT.get(article, "")
    for match in matches:
        tail = raw[match.start():]
        offset = max(1, match.end() - match.start())
        next_match = re.search(r"(?im)^\s*article\s+(?:no\.?\s*)?(?:[0-9]{1,2}|[IVXLC]{1,8})\b", tail[offset:])
        end = len(tail) if not next_match else offset + next_match.start()
        excerpt = core._normalise(tail[:end])
        if len(excerpt) < 100:
            continue
        lowered = excerpt[:600].lower()
        score = (10 if subject and subject in lowered else 0) + (5 if core._english_likelihood(excerpt) else 0)
        score += sum(3 for rate in expected if core._rate_present(excerpt, rate))
        score += min(len(excerpt) // 1000, 4)
        if best is None or score > best[0]:
            best = (score, excerpt)
    return None if best is None else best[1]


def _analyse(text: str, article: str, rules: list[dict]) -> tuple[dict, str | None]:
    rates = core._expected_rates(rules)
    result = {"expected_rates": rates, "status": "NO_EN_ARTICLE", "excerpt_length": 0, "missing_rates": rates}
    excerpt = _extract_flexible(text, article, rules)
    if not excerpt or not core._english_likelihood(excerpt):
        return result, None
    missing = [rate for rate in rates if not core._rate_present(excerpt, rate)]
    result.update({"status": "PASS" if not missing else "REVIEW", "excerpt_length": len(excerpt), "missing_rates": missing})
    return result, excerpt


def _sources(entry: dict | None) -> list[dict]:
    if not entry:
        return []
    if isinstance(entry.get("sources"), list):
        return [x for x in entry["sources"] if isinstance(x, dict) and str(x.get("url") or "").startswith("http")]
    return [entry] if str(entry.get("url") or "").startswith("http") else []


def _process(country: str, articles: dict[str, list[dict]], entry: dict | None) -> tuple[dict, dict | None]:
    sources = _sources(entry)
    row = {"country": country, "status": "NO_REGISTERED_SOURCE" if not sources else "NO_EN_TEXT", "source_attempts": [], "articles": {a: {"expected_rates": core._expected_rates(r), "status": "NO_EN_ARTICLE", "excerpt_length": 0, "missing_rates": core._expected_rates(r)} for a, r in articles.items()}}
    best_locales: dict[str, dict] = {}
    any_pair_valid = any_source_ok = False
    for source in sources:
        url = str(source.get("url")); attempt = {"url": url, "authority": source.get("authority"), "status": "SOURCE_ERROR", "articles": {}}
        try:
            body, _, resolved = core._request(url, timeout=25)
            if not _same_host_family(url, resolved): raise RuntimeError(f"redirect outside registered authority: {resolved}")
            text = core._document_text(body, resolved); any_source_ok = True
            attempt.update({"status": "PARSED", "resolved_url": resolved, "text_length": len(text)})
        except Exception as exc:
            attempt["error"] = f"{type(exc).__name__}: {exc}"; row["source_attempts"].append(attempt); continue
        if not (bool(source.get("pair_verified")) or _pair_valid(country, text)):
            attempt["status"] = "WRONG_TREATY_PAIR"; row["source_attempts"].append(attempt); continue
        any_pair_valid = True
        allowed = {str(x) for x in source.get("articles", [])} if source.get("articles") else set(articles)
        for article, rules in articles.items():
            if article not in allowed: continue
            candidate, excerpt = _analyse(text, article, rules); attempt["articles"][article] = candidate["status"]
            if STATUS_RANK[candidate["status"]] > STATUS_RANK[row["articles"][article]["status"]]:
                row["articles"][article] = candidate
                if excerpt: best_locales[article] = {"en": {"language": "en", "status": "candidate_official_treaty_text", "authority": source.get("authority"), "source_url": resolved, "text": excerpt}}
        row["source_attempts"].append(attempt)
    pass_count = sum(1 for x in row["articles"].values() if x["status"] == "PASS"); review_count = sum(1 for x in row["articles"].values() if x["status"] == "REVIEW")
    if pass_count == len(articles): row["status"] = "PASS"
    elif pass_count: row["status"] = "PARTIAL"
    elif review_count: row["status"] = "REVIEW"
    elif sources and not any_source_ok: row["status"] = "SOURCE_ERROR"
    elif sources and not any_pair_valid: row["status"] = "WRONG_TREATY_PAIR"
    elif sources: row["status"] = "NO_EN_TEXT"
    candidate_payload = {"schema_version": 1, "source_country": "CZ", "recipient_country": country, "candidate_only": True, "articles": best_locales} if best_locales else None
    return row, candidate_payload


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True); registry = _load(REGISTRY).get("entries") or {}; covered = core._covered_pairs(); grouped = {}
    for rule in _rules():
        country, article = str(rule.get("recipient_country") or "").upper(), str(rule.get("article") or "").strip()
        if country and article and (country, article) not in covered: grouped.setdefault((country, article), []).append(rule)
    countries = {}
    for (country, article), rules in grouped.items(): countries.setdefault(country, {})[article] = rules
    eligible = [c for c in countries if c in registry]; print(f"Explicit official EN treaty extraction v9: missing={len(grouped)} pairs, registered_missing={len(eligible)} countries", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_process, c, a, registry.get(c)): c for c, a in sorted(countries.items())}
        done = 0
        for future in as_completed(futures):
            c = futures[future]; done += 1
            try: row, candidate = future.result()
            except Exception as exc: row, candidate = {"country": c, "status": "WORKER_ERROR", "error": f"{type(exc).__name__}: {exc}", "articles": {}}, None
            results.append(row)
            if candidate: (OUT_DIR / f"{c}.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if c in registry: print(f"[{done}/{len(countries)}] {c}: {row['status']}", flush=True)
    results.sort(key=lambda x: x["country"]); counts = {}; passes = reviews = 0
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1; passes += sum(1 for x in row.get("articles", {}).values() if x.get("status") == "PASS"); reviews += sum(1 for x in row.get("articles", {}).values() if x.get("status") == "REVIEW")
    SUMMARY.write_text(json.dumps({"schema_version": 1, "registered_missing_country_count": len(eligible), "missing_country_article_pairs_at_start": len(grouped), "country_status_counts": counts, "article_candidates_pass": passes, "article_candidates_review": reviews, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"v9 counts: {json.dumps(counts, sort_keys=True)}", flush=True); print(f"Article PASS={passes} REVIEW={reviews}", flush=True); return 0

if __name__ == "__main__": raise SystemExit(main())
