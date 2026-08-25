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
        "scope": "bounded_section",
    },
    "istd.gov.jo/EN/ListDetails/Agreements_signed_with_the_Jordanian_government__Double_taxation_avoidance_agreements/1102/1": {
        "country_markers": ("czechre", "czech republic", "czech"),
        "language_markers": ("english",),
        "scope": "table_row",
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


def _scoped_segment(raw: str, start: int, scope: str) -> str:
    if scope == "table_row":
        before = raw.rfind("<tr", 0, start)
        after = raw.lower().find("</tr>", start)
        if before < 0 or after < 0:
            raise RuntimeError("Czech Republic marker is not contained in a complete treaty table row")
        segment = raw[before:after + len("</tr>")]
        if len(segment) > 15000:
            raise RuntimeError("Czech Republic treaty row is unexpectedly large")
        return segment
    if scope == "bounded_section":
        return raw[start:start + 20000]
    raise RuntimeError(f"unsupported official index scope: {scope}")


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
    segment = _scoped_segment(raw, start, str(config.get("scope") or "bounded_section"))
    segment_lower = html.unescape(segment).lower()
    if not any(marker.lower() in segment_lower for marker in config["country_markers"]):
        raise RuntimeError("scoped treaty block no longer contains Czech Republic marker")

    links = _absolute_links(resolved, segment)
    candidates: list[str] = []
    for href, label in links:
        probe = f"{label} {href}".lower()
        if any(marker.lower() in probe for marker in config["language_markers"]):
            candidates.append(href)
    if not candidates:
        # Row/section is already strictly scoped to Czech Republic. Accept only
        # document-like links from that exact scope and let pair/rate validation
        # downstream reject anything that is not the intended treaty.
        candidates = [href for href, _ in links if re.search(r"(?i)(\.pdf(?:$|[?#])|download|attachment|root_storage)", href)]
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        raise RuntimeError("no treaty document link found inside Czech Republic scope")

    last_error: Exception | None = None
    for candidate in candidates[:8]:
        try:
            doc_body, doc_type, doc_resolved = v10._resilient_request(candidate, timeout=timeout)
            if doc_body.startswith(b"%PDF") or len(doc_body) >= 2000:
                return doc_body, doc_type, doc_resolved
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Czech Republic scoped links did not yield a treaty document: {last_error}")


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
