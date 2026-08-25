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
LOCALE_REGISTRY = ROOT / "app" / "web" / "treaty-excerpt-locales-20260824.json"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_20260825.json"

USER_AGENT = "TaxTreat treaty-locale evidence preparation/2026-08-25"


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


def _request(url: str) -> tuple[bytes, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read(), response.headers.get_content_type(), response.geturl()


def _discover_pdf(url: str) -> tuple[bytes, str]:
    body, content_type, final_url = _request(url)
    if content_type == "application/pdf" or body[:4] == b"%PDF":
        return body, final_url

    text = body.decode("utf-8", errors="ignore")
    candidates = re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I)
    preferred: list[str] = []
    fallback: list[str] = []
    for href in candidates:
        absolute = urllib.parse.urljoin(final_url, href)
        lower = absolute.lower()
        if "viewfile.aspx" in lower or lower.endswith(".pdf") or ".pdf?" in lower:
            if any(token in lower for token in ("smlouv", "treat", "sbirka", "viewfile")):
                preferred.append(absolute)
            else:
                fallback.append(absolute)
    for candidate in preferred + fallback:
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
            subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
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
            r"\b(taxable only|taxed only|shall be exempt|exempt from tax|exempted from tax|may be taxed only)\b",
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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rules = _verified_treaty_rules()
    covered = _covered_pairs()
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
        source_urls = [
            str(rule.get("source_url") or "")
            for article_rules in articles.values()
            for rule in article_rules
            if str(rule.get("source_url") or "").startswith("http")
        ]
        source_url = source_urls[0] if source_urls else ""
        row = {
            "country": country,
            "source_url": source_url,
            "resolved_pdf_url": None,
            "status": "NO_SOURCE",
            "articles": {},
        }
        if not source_url:
            results.append(row)
            continue
        try:
            pdf, resolved_pdf_url = _discover_pdf(source_url)
            text = _pdf_text(pdf)
            row["resolved_pdf_url"] = resolved_pdf_url
            candidate_payload = {
                "schema_version": 1,
                "source_country": "CZ",
                "recipient_country": country,
                "candidate_only": True,
                "official_source_url": source_url,
                "resolved_pdf_url": resolved_pdf_url,
                "articles": {},
            }
            pass_count = 0
            for article, article_rules in sorted(articles.items(), key=lambda item: int(re.sub(r"\D", "", item[0]) or 0)):
                excerpt = _extract_article(text, article)
                rates = _expected_rates(article_rules)
                article_result = {
                    "expected_rates": rates,
                    "status": "NO_EN_ARTICLE",
                    "excerpt_length": 0,
                    "missing_rates": rates,
                }
                if excerpt and _english_likelihood(excerpt):
                    missing_rates = [rate for rate in rates if not _rate_present(excerpt, rate)]
                    article_result.update({
                        "status": "PASS" if not missing_rates else "REVIEW",
                        "excerpt_length": len(excerpt),
                        "missing_rates": missing_rates,
                    })
                    candidate_payload["articles"][article] = {
                        "en": {
                            "language": "en",
                            "status": "candidate_official_treaty_text",
                            "authority": "Official Czech treaty publication",
                            "source_url": resolved_pdf_url,
                            "text": excerpt,
                        }
                    }
                    if not missing_rates:
                        pass_count += 1
                row["articles"][article] = article_result
            row["status"] = "PASS" if pass_count == len(articles) else ("PARTIAL" if pass_count else "NO_EN_TEXT")
            if candidate_payload["articles"]:
                (OUT_DIR / f"{country}.json").write_text(
                    json.dumps(candidate_payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
        except Exception as exc:
            row["status"] = "ERROR"
            row["error"] = f"{type(exc).__name__}: {exc}"
        results.append(row)
        print(f"{country}: {row['status']}")

    counts: dict[str, int] = {}
    article_pass = 0
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        article_pass += sum(1 for value in row.get("articles", {}).values() if value.get("status") == "PASS")

    summary = {
        "schema_version": 1,
        "missing_country_article_pairs_at_start": len(grouped),
        "countries_scanned": len(results),
        "country_status_counts": counts,
        "article_candidates_pass": article_pass,
        "results": results,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nBulk EN treaty locale candidate extraction")
    print(f"Missing country/article pairs at start: {len(grouped)}")
    print(f"Countries scanned: {len(results)}")
    print(f"Article candidates PASS: {article_pass}")
    print(f"Summary: {SUMMARY.relative_to(ROOT)}")
    print(f"Candidates: {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
