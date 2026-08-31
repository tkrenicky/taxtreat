from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
LOCALE_REGISTRY = ROOT / "app" / "web" / "treaty-excerpt-locales-20260824.json"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"
OUT_DIR = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v3_20260825"
SUMMARY = ROOT / "reports" / "treaty_en_locale_bulk_candidates_v3_20260825.json"
SOURCE_CACHE = ROOT / "reports" / "treaty_en_official_source_cache_20260825.json"

USER_AGENT = "Mozilla/5.0 (compatible; TaxTreat official treaty evidence preparation/2026-08-25)"
STATUS_RANK = {"NO_EN_ARTICLE": 0, "REVIEW": 1, "PASS": 2}

# Discovery is intentionally broader than evidence acceptance. Search engines may locate a
# source, but only an official-domain document is eligible to become a locale candidate.
OFFICIAL_DOMAIN_HINTS = {
    "ad": ("govern.ad", "impostos.ad"),
    "ae": ("mof.gov.ae",),
    "al": ("financa.gov.al", "tatime.gov.al"),
    "am": ("minfin.am", "src.am"),
    "az": ("taxes.gov.az", "maliyye.gov.az"),
    "ba": ("fmf.gov.ba", "mft.gov.ba"),
    "bb": ("bra.gov.bb", "gov.bb"),
    "bd": ("nbr.gov.bd", "mof.gov.bd"),
    "be": ("finances.belgium.be",),
    "bg": ("minfin.bg", "nra.bg"),
    "bh": ("mofne.gov.bh", "bahrain.bh"),
    "br": ("gov.br", "receita.economia.gov.br"),
    "bw": ("burs.org.bw", "gov.bw"),
    "by": ("nalog.gov.by", "minfin.gov.by"),
    "ch": ("estv.admin.ch", "sif.admin.ch", "admin.ch"),
    "cl": ("sii.cl", "hacienda.cl"),
    "cm": ("impots.cm", "minfi.gov.cm"),
    "cn": ("chinatax.gov.cn", "mof.gov.cn"),
    "co": ("dian.gov.co", "minhacienda.gov.co"),
    "cy": ("mof.gov.cy",),
    "de": ("bundesfinanzministerium.de", "gesetze-im-internet.de"),
    "dk": ("skm.dk", "skat.dk"),
    "ee": ("fin.ee", "riigiteataja.ee"),
    "eg": ("eta.gov.eg", "mof.gov.eg"),
    "es": ("hacienda.gob.es", "boe.es"),
    "et": ("mofed.gov.et", "mor.gov.et"),
    "fi": ("finlex.fi", "vero.fi", "vm.fi"),
    "fr": ("impots.gouv.fr", "legifrance.gouv.fr", "economie.gouv.fr"),
    "ge": ("mof.ge", "rs.ge"),
    "gh": ("gra.gov.gh", "mofep.gov.gh"),
    "gr": ("aade.gr", "minfin.gov.gr"),
    "hr": ("porezna-uprava.hr", "mfin.gov.hr"),
    "hu": ("nav.gov.hu", "njt.hu", "kormany.hu"),
    "id": ("pajak.go.id", "kemenkeu.go.id"),
    "in": ("incometaxindia.gov.in", "dea.gov.in"),
    "ir": ("tax.gov.ir", "mefa.gov.ir"),
    "is": ("stjornarradid.is", "skatturinn.is"),
    "it": ("finanze.gov.it", "agenziaentrate.gov.it", "gazzettaufficiale.it"),
    "jo": ("istd.gov.jo", "mof.gov.jo"),
    "kg": ("sti.gov.kg", "minfin.kg"),
    "kp": ("mfa.gov.kp",),
    "kr": ("nts.go.kr", "moef.go.kr", "law.go.kr"),
    "kw": ("mof.gov.kw",),
    "kz": ("gov.kz", "kgd.gov.kz"),
    "lb": ("finance.gov.lb",),
    "li": ("llv.li",),
    "lk": ("ird.gov.lk", "treasury.gov.lk"),
    "lt": ("finmin.lrv.lt", "vmi.lt"),
    "lu": ("impotsdirects.public.lu", "legilux.public.lu"),
    "lv": ("fm.gov.lv", "vid.gov.lv", "likumi.lv"),
    "ma": ("tax.gov.ma", "finances.gov.ma"),
    "md": ("sfs.md", "mf.gov.md", "legis.md"),
    "me": ("gov.me",),
    "mk": ("finance.gov.mk", "ujp.gov.mk"),
    "mn": ("mta.gov.mn", "mof.gov.mn"),
    "mt": ("cfr.gov.mt", "finance.gov.mt", "legislation.mt"),
    "mx": ("sat.gob.mx", "dof.gob.mx", "gob.mx"),
    "ng": ("firs.gov.ng", "finance.gov.ng"),
    "nl": ("rijksoverheid.nl", "overheid.nl", "belastingdienst.nl"),
    "no": ("regjeringen.no", "lovdata.no", "skatteetaten.no"),
    "pa": ("dgi.mef.gob.pa", "mef.gob.pa"),
    "pk": ("fbr.gov.pk", "finance.gov.pk"),
    "pl": ("podatki.gov.pl", "gov.pl", "isap.sejm.gov.pl"),
    "pt": ("portaldasfinancas.gov.pt", "dre.pt"),
    "qa": ("gta.gov.qa", "mof.gov.qa"),
    "ro": ("mfinante.gov.ro", "anaf.ro"),
    "rs": ("mfin.gov.rs", "purs.gov.rs"),
    "ru": ("nalog.gov.ru", "minfin.gov.ru"),
    "rw": ("rra.gov.rw", "minecofin.gov.rw"),
    "se": ("regeringen.se", "skatteverket.se"),
    "si": ("gov.si", "fu.gov.si"),
    "sk": ("mfsr.sk", "financnasprava.sk", "slov-lex.sk"),
    "sm": ("gov.sm",),
    "sn": ("finances.gouv.sn", "impotsetdomaines.gouv.sn"),
    "sy": ("mof.gov.sy",),
    "th": ("rd.go.th", "mof.go.th"),
    "tj": ("andoz.tj", "moliya.tj"),
    "tm": ("tax.gov.tm", "minfin.gov.tm"),
    "tn": ("finances.gov.tn", "impots.finances.gov.tn"),
    "tr": ("gib.gov.tr", "hmb.gov.tr"),
    "tw": ("mof.gov.tw", "law.moj.gov.tw"),
    "ua": ("tax.gov.ua", "mof.gov.ua", "zakon.rada.gov.ua"),
    "uz": ("soliq.uz", "imv.uz", "lex.uz"),
    "ve": ("seniat.gob.ve", "mppre.gob.ve"),
    "vn": ("gdt.gov.vn", "mof.gov.vn"),
    "xk": ("atk-ks.org", "mf.rks-gov.net", "gzk.rks-gov.net"),
}

# These source countries have especially useful official treaty repositories and are tried
# as discovery mirrors for their Czech treaty. A successful mirror must still pass domain,
# English-article and Stage-6 rate checks below.
SEARCH_ENDPOINTS = (
    "https://www.google.com/search?q={query}",
    "https://www.bing.com/search?q={query}",
    "https://html.duckduckgo.com/html/?q={query}",
)


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


def _request(url: str, timeout: int = 35) -> tuple[bytes, str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), response.headers.get_content_type(), response.geturl()


def _host(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower().lstrip("www.")


def _is_official(country: str, url: str) -> bool:
    host = _host(url)
    hints = OFFICIAL_DOMAIN_HINTS.get(country.lower(), ())
    return any(host == hint or host.endswith("." + hint) for hint in hints)


def _unwrap_search_url(url: str) -> str:
    parsed = urllib.parse.urlparse(html.unescape(url))
    query = urllib.parse.parse_qs(parsed.query)
    if parsed.path == "/url" and query.get("q"):
        return query["q"][0]
    if "bing.com" in parsed.netloc and query.get("u"):
        value = query["u"][0]
        if value.startswith("a1"):
            value = value[2:]
        try:
            import base64
            padding = "=" * (-len(value) % 4)
            return base64.b64decode(value + padding).decode("utf-8", errors="ignore")
        except Exception:
            pass
    if "duckduckgo.com" in parsed.netloc and query.get("uddg"):
        return query["uddg"][0]
    return html.unescape(url)


def _links_from_html(body: bytes, base_url: str) -> list[str]:
    text = body.decode("utf-8", errors="ignore")
    links: list[str] = []
    seen: set[str] = set()
    for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
        href = _unwrap_search_url(urllib.parse.urljoin(base_url, href))
        if not href.startswith("http") or href in seen:
            continue
        seen.add(href)
        links.append(href)
    return links


def _discover_official_urls(country: str) -> list[str]:
    hints = OFFICIAL_DOMAIN_HINTS.get(country.lower(), ())
    if not hints:
        return []
    queries: list[str] = []
    for domain in hints:
        queries.extend([
            f'site:{domain} Czech Republic double taxation agreement English pdf',
            f'site:{domain} Czechia tax treaty English Article 10 dividends Article 11 interest Article 12 royalties',
            f'site:{domain} Czech Republic tax convention English',
        ])
    urls: list[str] = []
    seen: set[str] = set()
    for query in queries:
        encoded = urllib.parse.quote_plus(query)
        for template in SEARCH_ENDPOINTS:
            try:
                body, _, final_url = _request(template.format(query=encoded), timeout=20)
            except Exception:
                continue
            for url in _links_from_html(body, final_url):
                if url in seen or not _is_official(country, url):
                    continue
                seen.add(url)
                urls.append(url)
            if urls:
                break
        if len(urls) >= 20:
            break
    return urls[:20]


def _discover_document(url: str) -> tuple[bytes, str]:
    body, content_type, final_url = _request(url)
    if content_type == "application/pdf" or body[:4] == b"%PDF":
        return body, final_url

    links = _links_from_html(body, final_url)
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
    for _, candidate in sorted(scored, reverse=True):
        try:
            candidate_body, candidate_type, resolved = _request(candidate)
        except Exception:
            continue
        if candidate_type == "application/pdf" or candidate_body[:4] == b"%PDF":
            return candidate_body, resolved
        # Some official repositories expose the treaty directly as HTML.
        if candidate_type in {"text/html", "application/xhtml+xml", "text/plain"}:
            return candidate_body, resolved
    if content_type in {"text/html", "application/xhtml+xml", "text/plain"}:
        return body, final_url
    raise RuntimeError("official source did not resolve to usable treaty text")


def _document_text(body: bytes, source_url: str) -> str:
    if body[:4] != b"%PDF":
        text = body.decode("utf-8", errors="ignore")
        text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
        text = re.sub(r"(?s)<[^>]+>", "\n", text)
        return html.unescape(text)
    with tempfile.TemporaryDirectory(prefix="taxtreat-treaty-en-v3-") as tmp:
        pdf_path = Path(tmp) / "source.pdf"
        txt_path = Path(tmp) / "source.txt"
        pdf_path.write_bytes(body)
        if shutil.which("pdftotext"):
            completed = subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            if completed.returncode == 0:
                return txt_path.read_text(encoding="utf-8", errors="ignore")
            raise RuntimeError(f"pdftotext failed: {completed.stderr.strip()[:300]}")
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            from PyPDF2 import PdfReader  # type: ignore
        reader = PdfReader(str(pdf_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)


def _normalise(text: str) -> str:
    text = text.replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _article_heading_regex(article: str) -> re.Pattern[str]:
    number = re.escape(str(article))
    # Covers ARTICLE 10, Article X / ARTICLE X, Article 10., and common PDF line breaks.
    roman = {"10": "X", "11": "XI", "12": "XII"}.get(str(article), "")
    variants = [number]
    if roman:
        variants.append(roman)
    token = "(?:" + "|".join(variants) + ")"
    return re.compile(rf"(?im)^\s*article\s+(?:no\.?\s*)?{token}\s*[.:\-]?\s*(?:\n\s*)?(?:dividends|interest|royalt(?:y|ies))?\s*$", re.I | re.M)


def _extract_article(text: str, article: str) -> str | None:
    start_match = _article_heading_regex(article).search(text)
    if not start_match:
        return None
    after = text[start_match.start():]
    next_match = re.search(r"(?im)^\s*article\s+(?:no\.?\s*)?(?:[0-9]{1,2}|[IVXLC]{1,8})\s*[.:\-]?\s*(?:\n|$)", after[start_match.end() - start_match.start():], re.I | re.M)
    end = len(after)
    if next_match:
        end = start_match.end() - start_match.start() + next_match.start()
    excerpt = _normalise(after[:end])
    return excerpt if len(excerpt) >= 120 else None


def _english_likelihood(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "contracting state", "resident of", "beneficial owner", "shall be taxable",
        "may be taxed", "dividends", "interest", "royalties", "gross amount",
    )
    return sum(1 for marker in markers if marker in lowered) >= 3


def _expected_rates(rules: Iterable[dict]) -> list[float]:
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


def _analyse_article(text: str, article: str, rules: list[dict]) -> tuple[dict, str | None]:
    rates = _expected_rates(rules)
    result = {"expected_rates": rates, "status": "NO_EN_ARTICLE", "excerpt_length": 0, "missing_rates": rates}
    excerpt = _extract_article(text, article)
    if not excerpt or not _english_likelihood(excerpt):
        return result, None
    missing = [rate for rate in rates if not _rate_present(excerpt, rate)]
    result.update({
        "status": "PASS" if not missing else "REVIEW",
        "excerpt_length": len(excerpt),
        "missing_rates": missing,
    })
    return result, excerpt


def _load_cache() -> dict[str, list[str]]:
    if not SOURCE_CACHE.exists():
        return {}
    try:
        payload = _load_json(SOURCE_CACHE)
    except Exception:
        return {}
    return {str(k).upper(): list(v or []) for k, v in (payload.get("countries") or {}).items()}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rules = _verified_treaty_rules()
    covered = _covered_pairs()
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

    results: list[dict] = []
    updated_cache = dict(cache)
    for country, articles in sorted(countries.items()):
        discovered = list(cache.get(country, []))
        if not discovered:
            discovered = _discover_official_urls(country)
            if discovered:
                updated_cache[country] = discovered

        row = {
            "country": country,
            "status": "NO_OFFICIAL_EN_SOURCE" if not discovered else "NO_EN_TEXT",
            "sources_discovered": len(discovered),
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

        for source_url in discovered:
            if not _is_official(country, source_url):
                continue
            attempt = {"url": source_url, "status": "SOURCE_RESOLUTION"}
            try:
                body, resolved = _discover_document(source_url)
                if not _is_official(country, resolved):
                    raise RuntimeError("resolved document left official-domain boundary")
                text = _document_text(body, resolved)
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
                candidate, excerpt = _analyse_article(text, article, article_rules)
                attempt["articles"][article] = candidate["status"]
                current = row["articles"][article]
                if STATUS_RANK[candidate["status"]] > STATUS_RANK[current["status"]]:
                    row["articles"][article] = candidate
                    if excerpt:
                        best_locales[article] = {
                            "en": {
                                "language": "en",
                                "status": "candidate_official_treaty_text",
                                "authority": _host(resolved),
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
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        results.append(row)
        print(f"{country}: {row['status']}")

    SOURCE_CACHE.write_text(
        json.dumps({"schema_version": 1, "countries": updated_cache}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    counts: dict[str, int] = {}
    article_pass = 0
    article_review = 0
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        article_pass += sum(1 for value in row["articles"].values() if value["status"] == "PASS")
        article_review += sum(1 for value in row["articles"].values() if value["status"] == "REVIEW")

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
    print("\nBulk official EN treaty locale candidate extraction v3")
    print(f"Missing country/article pairs at start: {len(grouped)}")
    print(f"Countries scanned: {len(results)}")
    print(f"Country status counts: {json.dumps(counts, sort_keys=True)}")
    print(f"Article candidates PASS: {article_pass}")
    print(f"Article candidates REVIEW: {article_review}")
    print(f"Summary: {SUMMARY.relative_to(ROOT)}")
    print(f"Candidates: {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
