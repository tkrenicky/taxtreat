from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
MF_INVENTORY = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
LOCALE_REGISTRY = ROOT / "app" / "web" / "treaty-excerpt-locales-20260824.json"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_20260825.json"

USER_AGENT = "Mozilla/5.0 (compatible; TaxTreat treaty-locale evidence preparation/2026-08-25)"
STATUS_RANK = {"NO_EN_ARTICLE": 0, "REVIEW": 1, "PASS": 2}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verified_treaty_rules() -> list[dict]:
    rules: list[dict] = []
    for path in sorted(RULE_DIR.glob("*.json")):
        payload = _load_json(path)
        for rule in payload.get("rules", []):
            if (
                rule.get("verification_status") == "verified"
                and rule.get("effect") == "rate"
                and rule.get("legal_layer") in {"treaty", "protocol", "mli"}
            ):
                rules.append(rule)
    return rules


def _covered_pairs() -> set[tuple[str, str]]:
    covered: set[tuple[str, str]] = set()
    base = _load_json(LOCALE_REGISTRY)
    for country, articles in (base.get("entries") or {}).items():
        for article, payload in (articles or {}).items():
            if str((payload or {}).get("en", {}).get("text") or "").strip():
                covered.add((str(country).upper(), str(article)))
    if LOCALE_DIR.is_dir():
        for path in LOCALE_DIR.glob("*.json"):
            payload = _load_json(path)
            country = str(payload.get("recipient_country") or path.stem).upper()
            for article, entry in (payload.get("articles") or {}).items():
                if str((entry or {}).get("en", {}).get("text") or "").strip():
                    covered.add((country, str(article)))
    return covered


def _mf_sources() -> dict[str, list[dict]]:
    if not MF_INVENTORY.exists():
        return {}
    payload = _load_json(MF_INVENTORY)
    result: dict[str, list[dict]] = {}
    for partner in payload.get("partners", []):
        country = str(partner.get("iso2") or "").upper()
        if not country:
            continue
        ordered_groups = (
            ("base_instrument", partner.get("base_instruments") or []),
            ("financial_reporter", partner.get("financial_reporter_sources") or []),
            ("related_instrument", partner.get("related_instruments") or []),
        )
        for source_kind, items in ordered_groups:
            for item in items:
                url = str(item.get("url") or "")
                if not url.startswith("http"):
                    continue
                result.setdefault(country, []).append({
                    "url": url,
                    "authority": str(item.get("authority") or "Czech Ministry of Finance / official publication"),
                    "label": str(item.get("label") or ""),
                    "source_id": str(item.get("source_id") or ""),
                    "source_kind": source_kind,
                    "origin": "mf_inventory",
                })
    return result


def _source_candidates(country: str, articles: dict[str, list[dict]], mf_sources: dict[str, list[dict]]) -> list[dict]:
    candidates = list(mf_sources.get(country, []))
    for article_rules in articles.values():
        for rule in article_rules:
            url = str(rule.get("source_url") or "")
            if url.startswith("http"):
                candidates.append({
                    "url": url,
                    "authority": "Stage 6 approved official source",
                    "label": str(rule.get("source_id") or ""),
                    "source_id": str(rule.get("source_id") or ""),
                    "source_kind": "stage6_rule_source",
                    "origin": "stage6",
                })
    deduped: list[dict] = []
    seen: set[str] = set()
    for candidate in candidates:
        url = candidate["url"]
        if url in seen:
            continue
        seen.add(url)
        deduped.append(candidate)
    return deduped


def _request(url: str) -> tuple[bytes, str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read(), response.headers.get_content_type(), response.geturl()


def _discover_pdf(url: str) -> tuple[bytes, str]:
    body, content_type, final_url = _request(url)
    if content_type == "application/pdf" or body[:4] == b"%PDF":
        return body, final_url

    text = body.decode("utf-8", errors="ignore")
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I)
    preferred: list[str] = []
    fallback: list[str] = []
    for href in hrefs:
        absolute = urllib.parse.urljoin(final_url, href)
        lower = absolute.lower()
        is_download = any(token in lower for token in (
            "viewfile.aspx",
            "/stahni/",
            "overena-zneni",
            ".pdf",
            "download",
        ))
        if not is_download:
            continue
        if any(token in lower for token in ("smlouv", "treat", "sbirka", "viewfile", "overena-zneni")):
            preferred.append(absolute)
        else:
            fallback.append(absolute)

    seen: set[str] = set()
    for candidate in preferred + fallback:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            pdf, pdf_type, resolved = _request(candidate)
        except Exception:
            continue
        if pdf_type == "application/pdf" or pdf[:4] == b"%PDF":
            return pdf, resolved
    raise RuntimeError("official source did not resolve to a PDF")


def _pdf_text(pdf: bytes) -> str:
    with tempfile.TemporaryDirectory(prefix="taxtreat-treaty-en-") as tmp:
        pdf_path = Path(tmp) / "source.pdf"
        txt_path = Path(tmp) / "source.txt"
        pdf_path.write_bytes(pdf)
        if shutil.which("pdftotext"):
            completed = subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(f"pdftotext failed: {completed.stderr.strip()[:300]}")
            return txt_path.read_text(encoding="utf-8", errors="ignore")
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # type: ignore
            except ImportError as exc:
                raise RuntimeError("pdftotext, pypdf or PyPDF2 is required") from exc
        reader = PdfReader(str(pdf_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)


def _normalise(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_article(text: str, article: str) -> str | None:
    article_re = re.escape(str(article))
    start_patterns = [
        rf"(?im)^\s*ARTICLE\s+{article_re}\b.*$",
        rf"(?im)^\s*Article\s+{article_re}\b.*$",
    ]
    start = None
    for pattern in start_patterns:
        match = re.search(pattern, text)
        if match:
            start = match.start()
            break
    if start is None:
        return None
    after = text[start:]
    next_match = re.search(r"(?im)^\s*(?:ARTICLE|Article)\s+([0-9]+[A-Za-z]?)\b", after[1:])
    end = len(after) if not next_match else 1 + next_match.start()
    excerpt = _normalise(after[:end])
    return excerpt if len(excerpt) >= 80 else None


def _expected_rates(rules: list[dict]) -> list[float]:
    values: set[float] = set()
    for rule in rules:
        try:
            values.add(float(rule.get("rate")))
        except (TypeError, ValueError):
            pass
    return sorted(values)


def _rate_present(text: str, rate: float) -> bool:
    if rate == 0:
        return bool(re.search(
            r"\b(taxable only|taxed only|shall be exempt|exempt from tax|exempted from tax|may be taxed only|shall not be taxed)\b",
            text,
            re.I,
        ))
    canonical = str(int(rate)) if float(rate).is_integer() else str(rate)
    escaped = re.escape(canonical).replace(r"\.", r"[.,]")
    return bool(re.search(rf"(?:^|[^0-9]){escaped}(?:[.,]0+)?\s*(?:%|percent|per cent)\b", text, re.I))


def _english_likelihood(text: str) -> bool:
    tokens = re.findall(r"[A-Za-z]+", text.lower())
    if not tokens:
        return False
    markers = {"contracting", "state", "resident", "dividends", "interest", "royalties", "tax"}
    return len(markers.intersection(tokens)) >= 3


def _analyse_article(text: str, article: str, article_rules: list[dict]) -> tuple[dict, str | None]:
    excerpt = _extract_article(text, article)
    rates = _expected_rates(article_rules)
    result = {
        "expected_rates": rates,
        "status": "NO_EN_ARTICLE",
        "excerpt_length": 0,
        "missing_rates": rates,
    }
    if not excerpt or not _english_likelihood(excerpt):
        return result, None
    missing_rates = [rate for rate in rates if not _rate_present(excerpt, rate)]
    result.update({
        "status": "PASS" if not missing_rates else "REVIEW",
        "excerpt_length": len(excerpt),
        "missing_rates": missing_rates,
    })
    return result, excerpt


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rules = _verified_treaty_rules()
    covered = _covered_pairs()
    mf_sources = _mf_sources()

    grouped: dict[tuple[str, str], list[dict]] = {}
    for rule in rules:
        country = str(rule.get("recipient_country") or "").upper()
        article = str(rule.get("article") or "").strip()
        if not country or not article or (country, article) in covered:
            continue
        grouped.setdefault((country, article), []).append(rule)

    countries: dict[str, dict[str, list[dict]]] = {}
    for (country, article), article_rules in grouped.items():
        countries.setdefault(country, {})[article] = article_rules

    results: list[dict] = []
    for country, articles in sorted(countries.items()):
        sources = _source_candidates(country, articles, mf_sources)
        row = {
            "country": country,
            "status": "NO_SOURCE" if not sources else "NO_EN_TEXT",
            "source_attempts": [],
            "articles": {
                article: {
                    "expected_rates": _expected_rates(article_rules),
                    "status": "NO_EN_ARTICLE",
                    "excerpt_length": 0,
                    "missing_rates": _expected_rates(article_rules),
                }
                for article, article_rules in articles.items()
            },
        }
        best_locales: dict[str, dict] = {}

        for source in sources:
            attempt = {
                "url": source["url"],
                "origin": source["origin"],
                "source_kind": source["source_kind"],
                "source_id": source["source_id"],
                "label": source["label"],
                "status": "SOURCE_RESOLUTION",
            }
            try:
                pdf, resolved_pdf_url = _discover_pdf(source["url"])
                attempt["resolved_pdf_url"] = resolved_pdf_url
            except Exception as exc:
                attempt["status"] = "DOWNLOAD_ERROR"
                attempt["error"] = f"{type(exc).__name__}: {exc}"
                row["source_attempts"].append(attempt)
                continue

            try:
                text = _pdf_text(pdf)
            except Exception as exc:
                attempt["status"] = "PDF_TEXT_ERROR"
                attempt["error"] = f"{type(exc).__name__}: {exc}"
                row["source_attempts"].append(attempt)
                continue

            attempt["status"] = "PARSED"
            attempt["text_length"] = len(text)
            article_attempts: dict[str, str] = {}
            for article, article_rules in articles.items():
                candidate_result, excerpt = _analyse_article(text, article, article_rules)
                article_attempts[article] = candidate_result["status"]
                current = row["articles"][article]
                if STATUS_RANK[candidate_result["status"]] > STATUS_RANK[current["status"]]:
                    row["articles"][article] = candidate_result
                    if excerpt:
                        best_locales[article] = {
                            "en": {
                                "language": "en",
                                "status": "candidate_official_treaty_text",
                                "authority": source["authority"],
                                "source_url": resolved_pdf_url,
                                "text": excerpt,
                            }
                        }
            attempt["articles"] = article_attempts
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
        elif sources and all(attempt["status"] == "DOWNLOAD_ERROR" for attempt in row["source_attempts"]):
            row["status"] = "DOWNLOAD_ERROR"
        elif sources and any(attempt["status"] == "PDF_TEXT_ERROR" for attempt in row["source_attempts"]):
            row["status"] = "PDF_TEXT_ERROR"
        elif sources:
            row["status"] = "NO_EN_TEXT"

        if best_locales:
            candidate_payload = {
                "schema_version": 1,
                "source_country": "CZ",
                "recipient_country": country,
                "candidate_only": True,
                "articles": best_locales,
            }
            (OUT_DIR / f"{country}.json").write_text(
                json.dumps(candidate_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        results.append(row)
        print(f"{country}: {row['status']}")

    counts: dict[str, int] = {}
    attempt_counts: dict[str, int] = {}
    article_pass = 0
    article_review = 0
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        for attempt in row.get("source_attempts", []):
            attempt_counts[attempt["status"]] = attempt_counts.get(attempt["status"], 0) + 1
        article_pass += sum(1 for value in row.get("articles", {}).values() if value.get("status") == "PASS")
        article_review += sum(1 for value in row.get("articles", {}).values() if value.get("status") == "REVIEW")

    summary = {
        "schema_version": 2,
        "missing_country_article_pairs_at_start": len(grouped),
        "countries_scanned": len(results),
        "country_status_counts": counts,
        "source_attempt_status_counts": attempt_counts,
        "article_candidates_pass": article_pass,
        "article_candidates_review": article_review,
        "results": results,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nBulk EN treaty locale candidate extraction")
    print(f"Missing country/article pairs at start: {len(grouped)}")
    print(f"Countries scanned: {len(results)}")
    print(f"Country status counts: {json.dumps(counts, sort_keys=True)}")
    print(f"Source attempt status counts: {json.dumps(attempt_counts, sort_keys=True)}")
    print(f"Article candidates PASS: {article_pass}")
    print(f"Article candidates REVIEW: {article_review}")
    print(f"Summary: {SUMMARY.relative_to(ROOT)}")
    print(f"Candidates: {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
