from __future__ import annotations

import html
import re
import urllib.parse

import build_bulk_treaty_en_locale_candidates_v10_20260825 as v10
import build_bulk_treaty_en_locale_candidates_v9_20260825 as v9


_INDEX_RESOLVERS = {
    "www.nbr.gov.bh/FTR/bahrain_tax_treaties_network": {
        "country_markers": ("جمهورية التشيك", "czech republic"),
        "language_markers": ("الإنجليزية", "english"),
    },
}


def _absolute_links(base_url: str, raw: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for match in re.finditer(r"(?is)<a\b[^>]*?href\s*=\s*(['\"])(.*?)\1[^>]*>(.*?)</a>", raw):
        href = html.unescape(match.group(2).strip())
        label = re.sub(r"(?is)<[^>]+>", " ", match.group(3))
        label = " ".join(html.unescape(label).split())
        if href and not href.lower().startswith(("javascript:", "mailto:")):
            links.append((urllib.parse.urljoin(base_url, href), label))
    return links


def _resolve_index(url: str, timeout: int) -> tuple[bytes, str, str] | None:
    parsed = urllib.parse.urlparse(url)
    key = f"{parsed.netloc}{parsed.path}"
    config = _INDEX_RESOLVERS.get(key)
    if not config:
        return None

    body, content_type, resolved = v10._resilient_request(url, timeout=timeout)
    raw = body.decode("utf-8", errors="ignore")
    lower = html.unescape(raw).lower()

    marker_positions = [lower.find(marker.lower()) for marker in config["country_markers"]]
    marker_positions = [pos for pos in marker_positions if pos >= 0]
    if not marker_positions:
        raise RuntimeError("official index page does not contain Czech Republic section")
    start = min(marker_positions)

    # Stay inside the Czech treaty block. The NBR page repeats the same structural
    # heading for every treaty; 20k chars is deliberately bounded to avoid choosing
    # an English PDF belonging to a neighbouring country.
    segment = raw[start:start + 20000]
    links = _absolute_links(resolved, segment)
    candidates: list[str] = []
    for href, label in links:
        probe = f"{label} {href}".lower()
        if any(marker.lower() in probe for marker in config["language_markers"]):
            candidates.append(href)
    if not candidates:
        # Some government templates render the language label outside the anchor.
        # Accept only PDF/download links from the bounded Czech block, never a link
        # from another treaty section.
        candidates = [href for href, _ in links if re.search(r"(?i)(\.pdf(?:$|[?#])|download|attachment)", href)]
    if not candidates:
        raise RuntimeError("no English treaty document link found in Czech Republic section")

    last_error: Exception | None = None
    for candidate in candidates[:6]:
        try:
            doc_body, doc_type, doc_resolved = v10._resilient_request(candidate, timeout=timeout)
            if doc_body.startswith(b"%PDF") or len(doc_body) >= 2000:
                return doc_body, doc_type, doc_resolved
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Czech Republic index links did not yield a treaty document: {last_error}")


def _request(url: str, timeout: int = 25) -> tuple[bytes, str, str]:
    resolved = _resolve_index(url, timeout)
    if resolved is not None:
        return resolved
    return v10._resilient_request(url, timeout=timeout)


def main() -> int:
    # Acquisition-only extension. Pair validation, article extraction, expected-rate
    # reconciliation and PASS-only promotion stay in v9 unchanged.
    v9.core._request = _request
    return v9.main()


if __name__ == "__main__":
    raise SystemExit(main())
