from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

DEFAULT_INPUT = Path("artifacts/at/treaty_source_inventory_machine.json")
DEFAULT_OUTPUT = Path("artifacts/at/instrument_chain_pilot.json")
DEFAULT_RAW_DIR = Path("artifacts/at/instrument_chain_sources")
PILOT_PARTNERS = ("Deutschland / Germany", "Tschechische Republik / Czech Republic", "Slowakei (CSSR) / Slovakia (CSSR)", "Niederlande / Netherlands", "Schweiz / Switzerland")
ALLOWED_HOSTS = frozenset({"ris.bka.gv.at", "www.ris.bka.gv.at", "bmf.gv.at", "www.bmf.gv.at"})
MAX_SOURCE_BYTES = 25 * 1024 * 1024
FETCH_ATTEMPTS = 3
RIS_TREATY_TEXT_LABELS = ("deutscher vertragstext", "englischer vertragstext", "deutscher text", "englischer text", "german treaty text", "english treaty text")
RIS_TREATY_LANGUAGE_MARKERS = ("deutsch", "englisch", "german", "english")
RIS_TREATY_DOCUMENT_MARKERS = ("vertrag", "abkommen", "protokoll", "treaty", "agreement", "protocol", "sprachfassung", "sprache")


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "source"


def _validate_official_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ValueError(f"Non-official Austrian treaty source URL: {url}")


def classify_official_link(url: str) -> str:
    lower = url.lower()
    if "bmf.gv.at/dam/" in lower and ("synth" in lower or "mli" in lower):
        return "synthesized_mli_text"
    if "geltendefassung.wxe" in lower or "/geltendefassung/bundesnormen/" in lower:
        return "current_consolidated_view"
    if "/eli/" in lower or "bgbl" in lower:
        return "published_instrument_or_protocol"
    return "official_text_attachment"


def _extension(content_type: str, url: str) -> str:
    lower_type = content_type.lower()
    path = urlsplit(url).path.lower()
    if "pdf" in lower_type or path.endswith(".pdf"):
        return ".pdf"
    if "html" in lower_type or path.endswith(".html") or path.endswith(".htm"):
        return ".html"
    return ".bin"


def _fetch_official_source(url: str, *, timeout: int = 30) -> tuple[bytes, str, str]:
    _validate_official_url(url)
    response = None
    last_error: Exception | None = None
    for _ in range(FETCH_ATTEMPTS):
        try:
            response = requests.get(url, timeout=timeout, headers={"User-Agent": "TaxTreat Austrian treaty evidence acquisition/1.0"})
            break
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc
    if response is None:
        raise ValueError(f"Austrian treaty source unavailable after {FETCH_ATTEMPTS} attempts: {url}") from last_error
    response.raise_for_status()
    final_url = str(response.url)
    _validate_official_url(final_url)
    content = response.content
    if not content:
        raise ValueError(f"Empty Austrian treaty source: {final_url}")
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError(f"Austrian treaty source exceeds size limit: {final_url}")
    return content, str(response.headers.get("content-type") or ""), final_url


def _is_relevant_ris_pdf(label: str, candidate_path: str) -> bool:
    if "/geltendefassung/bundesnormen/" in candidate_path:
        return True
    basename = candidate_path.rsplit("/", 1)[-1]
    if "/dokumente/bgblauth/" in candidate_path and basename.startswith("bgbla_"):
        return True
    if any(marker in label for marker in RIS_TREATY_TEXT_LABELS):
        return True
    return any(marker in label for marker in RIS_TREATY_LANGUAGE_MARKERS) and any(marker in label for marker in RIS_TREATY_DOCUMENT_MARKERS)


def _discover_ris_treaty_text_attachments(content: bytes, content_type: str, final_url: str) -> tuple[str, ...]:
    parsed = urlsplit(final_url)
    if (parsed.hostname or "").lower() not in {"ris.bka.gv.at", "www.ris.bka.gv.at"}:
        return ()
    if "html" not in content_type.lower() and not parsed.path.lower().endswith((".html", ".htm")):
        return ()
    soup = BeautifulSoup(content, "lxml")
    discovered: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        candidate = urljoin(final_url, str(anchor["href"]))
        candidate_path = urlsplit(candidate).path.lower()
        if not candidate_path.endswith(".pdf"):
            continue
        image = anchor.find("img")
        label = " ".join(" ".join([anchor.get_text(" ", strip=True), str(anchor.get("title") or ""), str(image.get("alt") or "") if image is not None else ""]).lower().split())
        if not _is_relevant_ris_pdf(label, candidate_path):
            continue
        _validate_official_url(candidate)
        if candidate not in seen:
            seen.add(candidate)
            discovered.append(candidate)
    return tuple(discovered)


def current_partner_labels(machine_inventory: dict[str, Any]) -> tuple[str, ...]:
    labels = tuple(str(row.get("partner_label")) for row in machine_inventory.get("records", []) if row.get("release_universe_candidate") is True and row.get("partner_label"))
    if not labels:
        raise ValueError("Austrian treaty inventory has no current release-universe candidates")
    return labels


def acquire_pilot(machine_inventory: dict[str, Any], *, raw_dir: Path, partners: tuple[str, ...] = PILOT_PARTNERS) -> dict[str, Any]:
    if machine_inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian treaty machine inventory")
    if machine_inventory.get("status") != "machine_source_inventory_not_reviewed":
        raise ValueError("Austrian treaty inventory is not in machine discovery state")
    records = {str(row.get("partner_label")): row for row in machine_inventory.get("records", []) if row.get("release_universe_candidate") is True}
    missing = [partner for partner in partners if partner not in records]
    if missing:
        raise ValueError(f"Requested partners missing from current Austrian treaty universe: {missing}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_records: list[dict[str, Any]] = []
    for partner in partners:
        treaty = records[partner]
        links = treaty.get("treaty_links") or []
        if not links:
            raise ValueError(f"Current Austrian treaty partner has no treaty-text links: {partner}")
        sources: list[dict[str, Any]] = []
        attachment_failures: list[dict[str, Any]] = []
        seen_final_urls: set[str] = set()

        def archive_source(listed_url: str, *, discovered_from_url: str | None = None) -> tuple[bytes, str, str] | None:
            try:
                content, content_type, final_url = _fetch_official_source(listed_url)
            except (ValueError, requests.RequestException) as exc:
                if discovered_from_url is None:
                    raise
                attachment_failures.append({
                    "listed_url": listed_url,
                    "discovered_from_url": discovered_from_url,
                    "discovery_method": "ris_treaty_text_attachment",
                    "status": "discovered_attachment_not_acquired",
                    "error_type": type(exc).__name__,
                    "legal_review_completed": False,
                })
                return None
            if final_url in seen_final_urls:
                return None
            seen_final_urls.add(final_url)
            digest = hashlib.sha256(content).hexdigest()
            suffix = _extension(content_type, final_url)
            source_order = len(sources) + 1
            path = raw_dir / f"{_safe_slug(partner)}-{source_order:02d}-{digest[:12]}{suffix}"
            path.write_bytes(content)
            row = {"source_order": source_order, "listed_url": listed_url, "final_url": final_url, "role_candidate": classify_official_link(final_url), "content_type": content_type, "byte_size": len(content), "sha256": digest, "artifact_path": str(path), "legal_review_completed": False}
            if discovered_from_url is not None:
                row["discovered_from_url"] = discovered_from_url
                row["discovery_method"] = "ris_treaty_text_attachment"
            sources.append(row)
            return content, content_type, final_url

        for url in links:
            archived = archive_source(str(url))
            if archived is None:
                continue
            content, content_type, final_url = archived
            for attachment_url in _discover_ris_treaty_text_attachments(content, content_type, final_url):
                archive_source(attachment_url, discovered_from_url=final_url)
        output_records.append({
            "partner_label": partner,
            "machine_mli_flag": treaty.get("mli_flag") is True,
            "machine_status_instrument_flag": treaty.get("status_instrument_flag") is True,
            "source_count": len(sources),
            "sources": sources,
            "attachment_acquisition_failure_count": len(attachment_failures),
            "attachment_acquisition_failures": attachment_failures,
            "attachment_acquisition_complete": not attachment_failures,
            "instrument_chain_resolved": False,
            "article_extraction_released": False,
        })

    full_current = tuple(partners) == current_partner_labels(machine_inventory)
    attachment_failure_count = sum(row["attachment_acquisition_failure_count"] for row in output_records)
    return {
        "schema_version": 3,
        "source_country": "AT",
        "status": "instrument_chain_pilot_acquired_not_reviewed",
        "acquisition_scope": "all_current_partners" if full_current else "selected_partners",
        "pilot_partner_count": len(output_records),
        "source_count": sum(row["source_count"] for row in output_records),
        "attachment_acquisition_failure_count": attachment_failure_count,
        "partners": output_records,
        "release_constraints": [
            "Successful HTTP acquisition and hashing do not establish which instrument controls a treaty result.",
            "Failure to acquire a discovered RIS attachment is retained as partner-specific unresolved evidence and never makes that partner release-eligible.",
            "A failure to acquire a listed primary source remains fatal to the acquisition run.",
            "RIS landing and consolidated-view pages may expose separate official publication, treaty-text or consolidated PDF attachments; discovered attachments remain machine evidence candidates only.",
            "Link-role classification is a machine candidate only and must be reconciled against the legal instrument chain.",
            "No Article 10, 11 or 12 rate may be released from this acquisition output without primary-text extraction and review.",
            "MLI and status-instrument flags remain discovery signals only."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--partner", action="append", dest="partners")
    parser.add_argument("--all-current", action="store_true")
    args = parser.parse_args()
    if args.partners and args.all_current:
        raise SystemExit("Use either --partner or --all-current, not both")
    inventory = json.loads(args.input.read_text(encoding="utf-8"))
    partners = current_partner_labels(inventory) if args.all_current else (tuple(args.partners) if args.partners else PILOT_PARTNERS)
    result = acquire_pilot(inventory, raw_dir=args.raw_dir, partners=partners)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AT instrument-chain acquisition: {result['pilot_partner_count']} partners / {result['source_count']} official sources acquired / {result['attachment_acquisition_failure_count']} unresolved discovered attachments / {result['acquisition_scope']}")


if __name__ == "__main__":
    main()
