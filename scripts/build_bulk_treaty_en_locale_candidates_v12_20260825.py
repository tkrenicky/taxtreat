from __future__ import annotations

import re
import urllib.parse

import build_bulk_treaty_en_locale_candidates_v10_20260825 as v10
import build_bulk_treaty_en_locale_candidates_v11_20260825 as v11
import build_bulk_treaty_en_locale_candidates_v9_20260825 as v9


def _is_psp_print(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    return host == "psp.cz" and parsed.path.lower().endswith("/sqw/text/tiskt.sqw")


def _same_psp_family(url: str) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower().removeprefix("www.")
    return host in {"psp.cz", "public.psp.cz"}


def _looks_like_document_link(href: str, label: str) -> bool:
    probe = f"{href} {label}".lower()
    if any(x in probe for x in ("historie.sqw", "stenprot", "hlasovani", "schuze", "usneseni")):
        return False
    return bool(re.search(r"(?i)(\.pdf(?:$|[?#])|\.docx?(?:$|[?#])|/eknih/|orig\w*\.sqw|attachment|download|soubor|prilo|přílo)", probe))


def _english_treaty_text(body: bytes, resolved: str) -> str | None:
    try:
        text = v9.core._document_text(body, resolved)
    except Exception:
        return None
    probe = " ".join(text[:80000].lower().split())
    if "czech republic" not in probe:
        return None
    if "contracting state" not in probe:
        return None
    if "dividend" not in probe:
        return None
    if not re.search(r"(?i)\barticle\s+(?:no\.?\s*)?(?:10|x)\b", text):
        return None
    if len(text) < 1500:
        return None
    return text


def _resolve_psp_print(url: str, timeout: int) -> tuple[bytes, str, str]:
    page_body, page_type, page_resolved = v10._resilient_request(url, timeout=timeout)
    raw = page_body.decode("utf-8", errors="ignore")
    links = v11._absolute_links(page_resolved, raw)

    candidates: list[str] = []
    for href, label in links:
        if not _same_psp_family(href):
            continue
        if _looks_like_document_link(href, label):
            candidates.append(href)
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        raise RuntimeError("PSP treaty print contains no document attachment links")

    last_error: Exception | None = None
    for candidate in candidates[:40]:
        try:
            body, content_type, resolved = v10._resilient_request(candidate, timeout=max(timeout, 45))
            if not _same_psp_family(resolved):
                continue
            if _english_treaty_text(body, resolved):
                return body, content_type, resolved
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"PSP print has no machine-readable English treaty attachment: {last_error}")


def _request(url: str, timeout: int = 25) -> tuple[bytes, str, str]:
    if _is_psp_print(url):
        return _resolve_psp_print(url, timeout)
    return v11._request(url, timeout=timeout)


def main() -> int:
    # Acquisition-only extension. The v9 pair/article/rate analysis and PASS-only
    # promotion remain unchanged; v12 merely selects the correct official attachment.
    v9.core._request = _request
    return v9.main()


if __name__ == "__main__":
    raise SystemExit(main())
