from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
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
    """Build deterministic e-Sbírka stable URLs from a publication reference."""

    reference = publication_reference(source_title)
    if reference is None:
        return ()

    number, year = reference.split("/", 1)
    normalized_title = re.sub(r"\s+", "", (source_title or "").casefold())
    primary_collection = "sm" if "sb.m.s" in normalized_title else "sb"
    collections = (primary_collection, "sb" if primary_collection == "sm" else "sm")

    urls: list[str] = []
    for collection in collections:
        for suffix in ("/0000-00-00", ""):
            url = f"https://e-sbirka.gov.cz/{collection}/{year}/{number}{suffix}"
            if url not in urls:
                urls.append(url)
    return tuple(urls)


def _html_to_text(payload: bytes) -> str:
    soup = BeautifulSoup(payload, "lxml")
    for element in soup(
        ["script", "style", "noscript", "svg", "form", "button", "nav", "header", "footer", "aside"]
    ):
        element.decompose()

    root = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup
    text = root.get_text("\n")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def fetch_official_document(
    source_title: str | None,
    *,
    timeout: float | None = None,
) -> OfficialSourceDocument:
    """Fetch the public HTML representation of an act from official e-Sbírka."""

    if os.getenv("TAXTREAT_OFFICIAL_SOURCE", "auto").strip().lower() in {
        "0", "false", "off", "no"
    }:
        raise OfficialSourceError("Official-source fallback is disabled")

    urls = official_source_urls(source_title)
    if not urls:
        raise OfficialSourceError(f"No publication reference in title {source_title!r}")

    request_timeout = timeout or float(os.getenv("TAXTREAT_OFFICIAL_SOURCE_TIMEOUT", "45"))
    errors: list[str] = []

    for url in urls:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TaxTreat/1.0; +https://github.com/tkrenicky/taxtreat)",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
                "Accept-Language": "cs,en;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=request_timeout) as response:
                payload = response.read()
                content_type = response.headers.get_content_type()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue

        if content_type not in {"text/html", "application/xhtml+xml"}:
            errors.append(f"{url}: unsupported content type {content_type}")
            continue

        text = _html_to_text(payload)
        normalized = text.casefold()
        if len(text) < 500 or not any(marker in normalized for marker in ("článek 1", "clanek 1", "article 1")):
            errors.append(f"{url}: official HTML did not contain treaty articles")
            continue

        return OfficialSourceDocument(pages=[text], url=url)

    raise OfficialSourceError("; ".join(errors) or "Official source could not be fetched")
