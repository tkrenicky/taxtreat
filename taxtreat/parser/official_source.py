from __future__ import annotations

import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from taxtreat.validation.document_identity import publication_reference


@dataclass(frozen=True)
class OfficialSourceDocument:
    pages: list[str]
    url: str


class OfficialSourceError(RuntimeError):
    pass


def official_source_urls(source_title: str | None) -> tuple[str, ...]:
    """Build deterministic public e-Sbírka URLs from a publication reference."""

    reference = publication_reference(source_title)
    if reference is None:
        return ()

    number, year = reference.split("/", 1)
    normalized_title = re.sub(r"\s+", "", (source_title or "").casefold())
    primary_collection = "sm" if "sb.m.s" in normalized_title else "sb"
    collections = (primary_collection, "sb" if primary_collection == "sm" else "sm")

    urls: list[str] = []
    for collection in collections:
        base = f"https://e-sbirka.gov.cz/{collection}/{year}/{number}"
        for suffix in (
            "/0000-00-00",
            "/0000-00-00?zalozka=text",
            "?zalozka=text",
            "",
        ):
            url = base + suffix
            if url not in urls:
                urls.append(url)
    return tuple(urls)




def official_download_urls(source_title: str | None) -> tuple[str, ...]:
    """Build public stable download URLs for structured e-Sbírka formats."""

    reference = publication_reference(source_title)
    if reference is None:
        return ()

    number, year = reference.split("/", 1)
    normalized_title = re.sub(r"\s+", "", (source_title or "").casefold())
    primary_collection = "sm" if "sb.m.s" in normalized_title else "sb"
    collections = (primary_collection, "sb" if primary_collection == "sm" else "sm")

    urls: list[str] = []
    for collection in collections:
        base = f"https://e-sbirka.gov.cz/{collection}/{year}/{number}/0000-00-00"
        for extension in ("XML", "JSON", "PDF", "xml", "json", "pdf"):
            url = f"{base}.{extension}"
            if url not in urls:
                urls.append(url)
    return tuple(urls)


def verified_mirror_urls(source_title: str | None) -> tuple[str, ...]:
    """Return deterministic read-only mirrors for an exact publication reference.

    The print endpoint is intentionally tried before the interactive page because
    it is server-rendered and does not depend on the JavaScript challenge used by
    the normal document view. Krajta is an additional transport fallback for the
    domestic ``Sb.`` collection only. Every response still has to pass publication,
    counterparty and semantic treaty validation before it can be accepted.
    """

    reference = publication_reference(source_title)
    if reference is None:
        return ()

    number, year = reference.split("/", 1)
    normalized_title = re.sub(r"\s+", "", (source_title or "").casefold())
    collection = "ms" if "sb.m.s" in normalized_title else "cs"
    document = f"{year}-{int(number)}"
    urls = [
        f"https://www.zakonyprolidi.cz/print/{collection}/{document}/?sil=1",
        f"https://www.zakonyprolidi.cz/{collection}/{document}",
    ]
    if collection == "cs":
        urls.append(f"https://krajta.slv.cz/{year}/{int(number)}")
    return tuple(urls)


def _request(url: str) -> Request:
    return Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; TaxTreat/1.0; +https://github.com/tkrenicky/taxtreat)",
            "Accept": "application/xml,application/json,application/pdf,text/html;q=0.9,*/*;q=0.1",
            "Accept-Language": "cs,en;q=0.8",
        },
    )


def _content_type(response: object) -> str:
    headers = getattr(response, "headers", None)
    if headers is None:
        return ""
    getter = getattr(headers, "get_content_type", None)
    if callable(getter):
        return str(getter()).casefold()
    raw = headers.get("Content-Type", "") if hasattr(headers, "get") else ""
    return str(raw).split(";", 1)[0].strip().casefold()


def _html_to_text(payload: bytes) -> str:
    soup = BeautifulSoup(payload, "lxml")
    for element in soup(
        ["script", "style", "noscript", "svg", "form", "button", "nav", "header", "footer", "aside"]
    ):
        element.decompose()

    # Some legal mirrors prepend a short anti-bot ``<main>`` before the actual
    # server-rendered document. Selecting the first main element therefore drops
    # the treaty. Prefer the text-richest plausible document container instead.
    candidates = list(soup.find_all("main"))
    candidates.extend(soup.find_all(attrs={"role": "main"}))
    candidates.extend(soup.find_all("article"))
    if soup.body is not None:
        candidates.append(soup.body)
    root = max(
        candidates,
        key=lambda element: len(element.get_text(" ", strip=True)),
        default=soup,
    )
    text = root.get_text("\n")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)




def _clean_text_lines(values: list[str]) -> str:
    lines: list[str] = []
    previous = None
    for value in values:
        line = " ".join(str(value).split())
        if not line or line == previous:
            continue
        lines.append(line)
        previous = line
    return "\n".join(lines)


def _xml_to_text(payload: bytes) -> str:
    root = ET.fromstring(payload)
    return _clean_text_lines([value for value in root.itertext()])


def _json_to_text(payload: bytes) -> str:
    data = json.loads(payload.decode("utf-8-sig"))
    values: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(data)
    return _clean_text_lines(values)


def _structured_to_text(payload: bytes, *, url: str, content_type: str) -> str | None:
    probe = payload.lstrip()[:64]
    lowered_url = url.casefold()
    try:
        if (
            content_type in {"application/xml", "text/xml"}
            or (probe.startswith(b"<") and b"<html" not in probe.lower())
        ):
            return _xml_to_text(payload)
        if (
            content_type in {"application/json", "application/ld+json"}
            or probe.startswith((b"{", b"["))
        ):
            return _json_to_text(payload)
        if lowered_url.endswith(".xml"):
            return _xml_to_text(payload)
        if lowered_url.endswith(".json"):
            return _json_to_text(payload)
    except (ET.ParseError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return None
    return None


def _allowed_official_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and (
            parsed.hostname == "e-sbirka.gov.cz"
            or parsed.hostname.endswith(".e-sbirka.gov.cz")
        )
    )


def _linked_document_urls(payload: bytes, base_url: str) -> tuple[str, ...]:
    soup = BeautifulSoup(payload, "lxml")
    candidates: list[tuple[int, str]] = []

    for element in soup.find_all(["a", "iframe", "embed", "object", "source"]):
        raw = (
            element.get("href")
            or element.get("src")
            or element.get("data")
            or element.get("data-src")
        )
        if not raw:
            continue
        url = urljoin(base_url, raw)
        if not _allowed_official_url(url):
            continue

        probe = " ".join(
            [
                url,
                element.get_text(" ", strip=True),
                str(element.get("title", "")),
                str(element.get("aria-label", "")),
                str(element.get("type", "")),
            ]
        ).casefold()
        score = 0
        if ".pdf" in probe or "application/pdf" in probe:
            score += 10
        if any(marker in probe for marker in ("pdf", "stáhn", "stahn", "úplné znění", "uplne zneni", "dokument")):
            score += 5
        if any(marker in probe for marker in ("priloha", "příloha", "download", "soubor", "content")):
            score += 2
        if score:
            candidates.append((score, url))

    # Some client-rendered pages keep document URLs in JSON/script attributes.
    decoded = payload.decode("utf-8", errors="ignore")
    for raw in re.findall(r'https:\\/\\/(?:[a-z0-9-]+\.)*e-sbirka\.gov\.cz[^"\s<]+|https://(?:[a-z0-9-]+\.)*e-sbirka\.gov\.cz[^"\s<]+', decoded):
        url = raw.replace("\\/", "/").replace("\\u0026", "&")
        if _allowed_official_url(url) and any(marker in url.casefold() for marker in ("pdf", "download", "soubor")):
            candidates.append((4, url))

    ordered: list[str] = []
    for _, url in sorted(candidates, key=lambda item: item[0], reverse=True):
        if url not in ordered:
            ordered.append(url)
    return tuple(ordered[:12])


def _complete_treaty_pages(
    pages: list[str],
    *,
    expected_country: str | None,
    source_title: str | None,
) -> bool:
    """Validate that one page set contains a complete semantic DTT sequence."""

    from taxtreat.parser.article_parser import parse_articles
    from taxtreat.parser.article_selection import select_best_article_sequence
    from taxtreat.parser.detector import extract_treaty
    from taxtreat.parser.normalize import normalize_pages
    from taxtreat.parser.publication import select_treaty_pages

    normalized = normalize_pages(pages)
    if expected_country:
        selection = select_treaty_pages(
            normalized,
            expected_country=expected_country,
            source_title=source_title,
        )
        normalized = selection.pages
    try:
        treaty_text, _ = extract_treaty(normalized)
        articles = parse_articles(treaty_text)
    except RuntimeError:
        return False
    return select_best_article_sequence(articles).is_complete


def _extract_linked_pdf(
    payload: bytes,
    *,
    url: str,
    timeout: float,
    expected_country: str | None,
    source_title: str | None,
    errors: list[str],
) -> OfficialSourceDocument | None:
    from taxtreat.parser.extractor import extract_document

    for document_url in _linked_document_urls(payload, url):
        try:
            with urlopen(_request(document_url), timeout=timeout) as response:
                document = response.read()
                content_type = _content_type(response)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{document_url}: {type(exc).__name__}: {exc}")
            continue

        if not document.startswith(b"%PDF") and content_type != "application/pdf":
            continue

        try:
            with tempfile.TemporaryDirectory(prefix="taxtreat_official_") as directory:
                path = Path(directory) / "official.pdf"
                path.write_bytes(document)
                extraction = extract_document(
                    path,
                    expected_country=expected_country,
                    source_title=source_title,
                )
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"{document_url}: {type(exc).__name__}: {exc}")
            continue

        if _complete_treaty_pages(
            extraction.pages,
            expected_country=expected_country,
            source_title=source_title,
        ):
            return OfficialSourceDocument(pages=extraction.pages, url=document_url)
        errors.append(f"{document_url}: PDF did not contain a complete treaty sequence")
    return None




def _mirror_url_has_reference(url: str, reference: str) -> bool:
    """Confirm that a deterministic mirror URL encodes the exact publication."""

    number, year = reference.split("/", 1)
    number = str(int(number))
    path = urlparse(url).path.rstrip("/")
    return bool(
        re.search(rf"/(?:cs|ms)/(?:{re.escape(year)}-{re.escape(number)})(?:/|$)", path)
        or re.search(rf"/{re.escape(year)}/{re.escape(number)}(?:/|$)", path)
    )

def _fetch_verified_mirror(
    source_title: str | None,
    *,
    expected_country: str | None,
    timeout: float,
    errors: list[str],
) -> OfficialSourceDocument | None:
    """Fetch a mirror only after official transports failed.

    The mirror is accepted only when the exact publication reference appears in
    the page and the normal country/semantic treaty validation succeeds.
    """

    reference = publication_reference(source_title)
    if reference is None:
        return None

    for url in verified_mirror_urls(source_title):
        try:
            with urlopen(_request(url), timeout=timeout) as response:
                payload = response.read()
                content_type = _content_type(response)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue

        if content_type and content_type not in {"text/html", "application/xhtml+xml"}:
            errors.append(f"{url}: unsupported mirror content type {content_type}")
            continue

        text = _html_to_text(payload)
        compact = re.sub(r"\s+", "", text.casefold())
        number, year = reference.split("/", 1)
        publication_markers = (
            f"{int(number)}/{year}sb.",
            f"{int(number)}/{year}sb.m.s.",
            f"{int(number)}/{year}sb.m.s",
        )
        marker_in_text = any(
            marker.replace(" ", "") in compact for marker in publication_markers
        )
        if not marker_in_text and not _mirror_url_has_reference(url, reference):
            errors.append(f"{url}: exact publication reference {reference} not found")
            continue

        if _complete_treaty_pages(
            [text],
            expected_country=expected_country,
            source_title=source_title,
        ):
            return OfficialSourceDocument(pages=[text], url=url)
        errors.append(f"{url}: mirror text did not contain a complete validated treaty")

    return None


def fetch_official_document(
    source_title: str | None,
    *,
    expected_country: str | None = None,
    timeout: float | None = None,
) -> OfficialSourceDocument:
    """Fetch structured text or a linked official PDF from public e-Sbírka."""

    if os.getenv("TAXTREAT_OFFICIAL_SOURCE", "auto").strip().lower() in {
        "0", "false", "off", "no"
    }:
        raise OfficialSourceError("Official-source fallback is disabled")

    urls = official_download_urls(source_title) + official_source_urls(source_title)
    if not urls:
        raise OfficialSourceError(f"No publication reference in title {source_title!r}")

    request_timeout = timeout or float(os.getenv("TAXTREAT_OFFICIAL_SOURCE_TIMEOUT", "45"))
    errors: list[str] = []

    for url in urls:
        try:
            with urlopen(_request(url), timeout=request_timeout) as response:
                payload = response.read()
                content_type = _content_type(response)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue

        structured_text = _structured_to_text(
            payload,
            url=url,
            content_type=content_type,
        )
        if structured_text is not None:
            if _complete_treaty_pages(
                [structured_text],
                expected_country=expected_country,
                source_title=source_title,
            ):
                return OfficialSourceDocument(pages=[structured_text], url=url)
            errors.append(f"{url}: structured document did not contain a complete treaty")
            continue

        if payload.startswith(b"%PDF") or content_type == "application/pdf":
            try:
                from taxtreat.parser.extractor import extract_document

                with tempfile.TemporaryDirectory(prefix="taxtreat_official_") as directory:
                    path = Path(directory) / "official.pdf"
                    path.write_bytes(payload)
                    extraction = extract_document(
                        path,
                        expected_country=expected_country,
                        source_title=source_title,
                    )
                if _complete_treaty_pages(
                    extraction.pages,
                    expected_country=expected_country,
                    source_title=source_title,
                ):
                    return OfficialSourceDocument(pages=extraction.pages, url=url)
            except (OSError, RuntimeError, ValueError) as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue

        if content_type and content_type not in {"text/html", "application/xhtml+xml"}:
            errors.append(f"{url}: unsupported content type {content_type}")
            continue

        text = _html_to_text(payload)
        if len(text) >= 500 and _complete_treaty_pages(
            [text],
            expected_country=expected_country,
            source_title=source_title,
        ):
            return OfficialSourceDocument(pages=[text], url=url)

        linked = _extract_linked_pdf(
            payload,
            url=url,
            timeout=request_timeout,
            expected_country=expected_country,
            source_title=source_title,
            errors=errors,
        )
        if linked is not None:
            return linked

        errors.append(f"{url}: official page did not expose complete treaty text or PDF")

    mirror = _fetch_verified_mirror(
        source_title,
        expected_country=expected_country,
        timeout=request_timeout,
        errors=errors,
    )
    if mirror is not None:
        return mirror

    raise OfficialSourceError("; ".join(errors) or "Official source could not be fetched")
