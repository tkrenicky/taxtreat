from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests


DEFAULT_INPUT = Path("artifacts/at/treaty_source_inventory_machine.json")
DEFAULT_OUTPUT = Path("artifacts/at/instrument_chain_pilot.json")
DEFAULT_RAW_DIR = Path("artifacts/at/instrument_chain_sources")
PILOT_PARTNERS = (
    "Deutschland / Germany",
    "Tschechische Republik / Czech Republic",
    "Slowakei (CSSR) / Slovakia (CSSR)",
    "Niederlande / Netherlands",
    "Schweiz / Switzerland",
)
ALLOWED_HOSTS = frozenset({
    "ris.bka.gv.at",
    "www.ris.bka.gv.at",
    "bmf.gv.at",
    "www.bmf.gv.at",
})
MAX_SOURCE_BYTES = 25 * 1024 * 1024


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
    if "geltendefassung.wxe" in lower:
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
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "TaxTreat Austrian treaty evidence acquisition/1.0"},
    )
    response.raise_for_status()
    final_url = str(response.url)
    _validate_official_url(final_url)
    content = response.content
    if not content:
        raise ValueError(f"Empty Austrian treaty source: {final_url}")
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError(f"Austrian treaty source exceeds size limit: {final_url}")
    return content, str(response.headers.get("content-type") or ""), final_url


def current_partner_labels(machine_inventory: dict[str, Any]) -> tuple[str, ...]:
    labels = tuple(
        str(row.get("partner_label"))
        for row in machine_inventory.get("records", [])
        if row.get("release_universe_candidate") is True and row.get("partner_label")
    )
    if not labels:
        raise ValueError("Austrian treaty inventory has no current release-universe candidates")
    return labels


def acquire_pilot(
    machine_inventory: dict[str, Any],
    *,
    raw_dir: Path,
    partners: tuple[str, ...] = PILOT_PARTNERS,
) -> dict[str, Any]:
    if machine_inventory.get("source_country") != "AT":
        raise ValueError("Expected Austrian treaty machine inventory")
    if machine_inventory.get("status") != "machine_source_inventory_not_reviewed":
        raise ValueError("Austrian treaty inventory is not in machine discovery state")

    records = {
        str(row.get("partner_label")): row
        for row in machine_inventory.get("records", [])
        if row.get("release_universe_candidate") is True
    }
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
        for index, url in enumerate(links, start=1):
            content, content_type, final_url = _fetch_official_source(str(url))
            digest = hashlib.sha256(content).hexdigest()
            suffix = _extension(content_type, final_url)
            filename = f"{_safe_slug(partner)}-{index:02d}-{digest[:12]}{suffix}"
            path = raw_dir / filename
            path.write_bytes(content)
            sources.append(
                {
                    "source_order": index,
                    "listed_url": str(url),
                    "final_url": final_url,
                    "role_candidate": classify_official_link(final_url),
                    "content_type": content_type,
                    "byte_size": len(content),
                    "sha256": digest,
                    "artifact_path": str(path),
                    "legal_review_completed": False,
                }
            )

        output_records.append(
            {
                "partner_label": partner,
                "machine_mli_flag": treaty.get("mli_flag") is True,
                "machine_status_instrument_flag": treaty.get("status_instrument_flag") is True,
                "source_count": len(sources),
                "sources": sources,
                "instrument_chain_resolved": False,
                "article_extraction_released": False,
            }
        )

    full_current = tuple(partners) == current_partner_labels(machine_inventory)
    return {
        "schema_version": 2,
        "source_country": "AT",
        "status": "instrument_chain_pilot_acquired_not_reviewed",
        "acquisition_scope": "all_current_partners" if full_current else "selected_partners",
        "pilot_partner_count": len(output_records),
        "source_count": sum(row["source_count"] for row in output_records),
        "partners": output_records,
        "release_constraints": [
            "Successful HTTP acquisition and hashing do not establish which instrument controls a treaty result.",
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
    if args.all_current:
        partners = current_partner_labels(inventory)
    else:
        partners = tuple(args.partners) if args.partners else PILOT_PARTNERS
    result = acquire_pilot(inventory, raw_dir=args.raw_dir, partners=partners)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"AT instrument-chain acquisition: {result['pilot_partner_count']} partners / "
        f"{result['source_count']} official sources acquired / {result['acquisition_scope']}"
    )


if __name__ == "__main__":
    main()
