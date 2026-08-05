from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from taxtreat.parser.official_source import official_download_urls


ROOT = Path(__file__).resolve().parents[2]

REGISTRY = ROOT / "data" / "registries" / "legal_evidence_sources.json"
ARCHIVE = ROOT / "data" / "raw" / "legal_evidence"
MANIFEST = ROOT / "data" / "manifests" / "legal_evidence_artifacts.json"

ALLOWED_DOMAINS = {
    "aplikace.mv.gov.cz",
    "mf.gov.cz",
    "mfcr.cz",
    "e-sbirka.gov.cz",
    "opendata.eselpoint.gov.cz",
    "eur-lex.europa.eu",
    "oecd.org",
    "www.oecd.org",
}

MAX_BYTES = 150 * 1024 * 1024


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _domain_allowed(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()

    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in ALLOWED_DOMAINS
    )


def _download(url: str) -> tuple[bytes, str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(compatible; TaxTreatLegalEvidenceArchiver/1.0)"
            ),
            "Accept": (
                "application/pdf,text/html,"
                "application/xhtml+xml,*/*;q=0.8"
            ),
        },
    )

    with urlopen(request, timeout=60) as response:
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "")
        content = response.read(MAX_BYTES + 1)

    if len(content) > MAX_BYTES:
        raise ValueError("Source artifact exceeds the 150 MB limit.")

    return content, content_type, final_url


def _classify(content: bytes, content_type: str) -> str:
    normalized_type = content_type.lower()
    beginning = content.lstrip()[:4096].lower()

    if content.startswith(b"%PDF-") or "application/pdf" in normalized_type:
        return "pdf"

    if (
        "text/html" in normalized_type
        or beginning.startswith(b"<!doctype html")
        or b"<html" in beginning
    ):
        return "html"

    return "other"



def _publication_label(source: dict[str, Any]) -> str | None:
    metadata = source.get("metadata") or {}

    for key in ("label", "source_title", "title"):
        value = metadata.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _linked_artifact_urls(
    content: bytes,
    *,
    base_url: str,
) -> tuple[str, ...]:
    soup = BeautifulSoup(content, "lxml")
    candidates: list[str] = []

    for element in soup.find_all(
        ["a", "iframe", "embed", "object", "source"]
    ):
        raw = (
            element.get("href")
            or element.get("src")
            or element.get("data")
            or element.get("data-src")
        )

        if not raw:
            continue

        url = urljoin(base_url, raw)

        if not _domain_allowed(url):
            continue

        probe = " ".join(
            [
                url,
                element.get_text(" ", strip=True),
                str(element.get("title", "")),
                str(element.get("type", "")),
            ]
        ).casefold()

        if any(
            token in probe
            for token in (
                ".pdf",
                "application/pdf",
                "stáhn",
                "stahn",
                "download",
                "soubor",
                "příloha",
                "priloha",
            )
        ):
            if url not in candidates:
                candidates.append(url)

    return tuple(candidates)


def _candidate_urls(source: dict[str, Any]) -> tuple[str, ...]:
    urls: list[str] = []

    label = _publication_label(source)

    if label:
        for url in official_download_urls(label):
            if url not in urls:
                urls.append(url)

    official_urls = source.get("official_urls", [])

    # Some evidence records contain only the interactive e-Sbírka URL and
    # do not carry a publication title. Derive the stable structured
    # download endpoints directly from the exact collection/year/number
    # encoded in that official URL.
    for official_url in official_urls:
        match = re.match(
            r"^https://e-sbirka\.gov\.cz/"
            r"(sb|sm)/(\d{4})/(\d+)(?:/[^?]*)?(?:\?.*)?$",
            official_url,
        )

        if match:
            collection, year, number = match.groups()
            base = (
                f"https://e-sbirka.gov.cz/"
                f"{collection}/{year}/{number}/0000-00-00"
            )

            for extension in (
                "PDF",
                "XML",
                "JSON",
                "pdf",
                "xml",
                "json",
            ):
                candidate = f"{base}.{extension}"

                if candidate not in urls:
                    urls.append(candidate)

    for url in official_urls:
        if url not in urls:
            urls.append(url)

    return tuple(urls)


def _html_can_be_archived(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()

    # e-Sbírka interactive pages can be a common JavaScript shell and are
    # therefore not accepted as evidence unless a structured artifact exists.
    if hostname == "e-sbirka.gov.cz" or hostname.endswith(
        ".e-sbirka.gov.cz"
    ):
        return False

    return hostname in {
        "mf.gov.cz",
        "eur-lex.europa.eu",
        "opendata.eselpoint.gov.cz",
    }

def archive_legal_evidence(
    *,
    sleep_seconds: float = 0.05,
) -> dict[str, Any]:
    registry = _read_json(REGISTRY)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    content_cache: dict[str, dict[str, Any]] = {}

    for index, source in enumerate(registry["sources"], start=1):
        source_id = source["source_id"]

        # Již ověřené hlavní smlouvy nepřepisujeme.
        if source["artifact_status"] == "verified":
            records.append(
                {
                    "source_id": source_id,
                    "status": "existing_verified_artifact",
                    "artifact_uri": source["artifact_uri"],
                    "sha256": source["artifact_sha256"],
                    "official_url": (
                        source["official_urls"][0]
                        if source["official_urls"]
                        else None
                    ),
                    "final_url": None,
                    "content_type": "application/pdf",
                    "size_bytes": None,
                }
            )
            continue

        attempts: list[dict[str, Any]] = []
        archived_record: dict[str, Any] | None = None
        html_found = False

        for url in _candidate_urls(source):
            if not _domain_allowed(url):
                attempts.append(
                    {
                        "url": url,
                        "status": "rejected_domain",
                    }
                )
                continue

            if url in content_cache:
                cached = content_cache[url]
                content = cached["content"]
                content_type = cached["content_type"]
                final_url = cached["final_url"]
            else:
                try:
                    content, content_type, final_url = _download(url)
                    content_cache[url] = {
                        "content": content,
                        "content_type": content_type,
                        "final_url": final_url,
                    }
                except Exception as exc:
                    attempts.append(
                        {
                            "url": url,
                            "status": "download_failed",
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue

            kind = _classify(content, content_type)

            attempts.append(
                {
                    "url": url,
                    "status": f"downloaded_{kind}",
                    "final_url": final_url,
                    "content_type": content_type,
                    "size_bytes": len(content),
                }
            )

            if kind == "html":
                html_found = True

                linked_urls = _linked_artifact_urls(
                    content,
                    base_url=final_url,
                )

                for linked_url in linked_urls:
                    try:
                        linked_content, linked_type, linked_final_url = (
                            _download(linked_url)
                        )
                    except Exception as exc:
                        attempts.append(
                            {
                                "url": linked_url,
                                "status": "linked_download_failed",
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        continue

                    linked_kind = _classify(
                        linked_content,
                        linked_type,
                    )

                    attempts.append(
                        {
                            "url": linked_url,
                            "status": f"linked_downloaded_{linked_kind}",
                            "final_url": linked_final_url,
                            "content_type": linked_type,
                            "size_bytes": len(linked_content),
                        }
                    )

                    if linked_kind == "pdf":
                        content = linked_content
                        content_type = linked_type
                        final_url = linked_final_url
                        url = linked_url
                        kind = "pdf"
                        break

                if kind == "html":
                    if not _html_can_be_archived(final_url):
                        continue

                    digest = hashlib.sha256(content).hexdigest()
                    destination = ARCHIVE / f"{digest}.html"

                    if not destination.exists():
                        destination.write_bytes(content)

                    archived_record = {
                        "source_id": source_id,
                        "status": "verified_html",
                        "artifact_uri": str(
                            destination.relative_to(ROOT)
                        ),
                        "sha256": digest,
                        "official_url": url,
                        "final_url": final_url,
                        "content_type": content_type,
                        "size_bytes": len(content),
                        "attempts": attempts,
                    }
                    break

            if kind != "pdf":
                continue

            digest = hashlib.sha256(content).hexdigest()
            destination = ARCHIVE / f"{digest}.pdf"

            if destination.exists():
                existing_digest = hashlib.sha256(
                    destination.read_bytes()
                ).hexdigest()

                if existing_digest != digest:
                    raise ValueError(
                        f"Existing artifact hash mismatch: {destination}"
                    )
            else:
                destination.write_bytes(content)

            archived_record = {
                "source_id": source_id,
                "status": "verified_pdf",
                "artifact_uri": str(destination.relative_to(ROOT)),
                "sha256": digest,
                "official_url": url,
                "final_url": final_url,
                "content_type": content_type,
                "size_bytes": len(content),
                "attempts": attempts,
            }
            break

        if archived_record is None:
            archived_record = {
                "source_id": source_id,
                "status": (
                    "html_only_unresolved"
                    if html_found
                    else "artifact_unresolved"
                ),
                "artifact_uri": None,
                "sha256": None,
                "official_url": None,
                "final_url": None,
                "content_type": None,
                "size_bytes": None,
                "attempts": attempts,
            }

        records.append(archived_record)

        if index % 25 == 0:
            print(f"Processed: {index}/{len(registry['sources'])}")

        if sleep_seconds:
            time.sleep(sleep_seconds)

    status_counts = Counter(record["status"] for record in records)

    unique_pdf_hashes = {
        record["sha256"]
        for record in records
        if record["status"] == "verified_pdf"
    }

    payload = {
        "schema_version": 1,
        "dataset_release": "legal-evidence-artifacts-2026-08-05.1",
        "source_registry_release": registry["dataset_release"],
        "summary": {
            "total_sources": len(records),
            "existing_verified_artifacts": status_counts[
                "existing_verified_artifact"
            ],
            "newly_verified_pdf_sources": status_counts["verified_pdf"],
            "newly_verified_html_sources": status_counts["verified_html"],
            "unique_new_pdf_artifacts": len(unique_pdf_hashes),
            "html_only_unresolved_sources": status_counts[
                "html_only_unresolved"
            ],
            "other_unresolved_sources": status_counts[
                "artifact_unresolved"
            ],
        },
        "artifacts": sorted(
            records,
            key=lambda record: record["source_id"],
        ),
    }

    _write_json(MANIFEST, payload)
    return payload


def main() -> None:
    payload = archive_legal_evidence()

    print("\nLegal evidence archive completed.")
    for key, value in payload["summary"].items():
        print(f"{key}: {value}")

    print("Manifest:", MANIFEST.relative_to(ROOT))
    print("Local archive:", ARCHIVE.relative_to(ROOT))


if __name__ == "__main__":
    main()
