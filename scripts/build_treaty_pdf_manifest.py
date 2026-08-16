from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

from build_treaty_verbatim_registry import build_registry

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "treaty_verified_pdf_manifest.json"
BASE = "https://e-sbirka.gov.cz/sbr-externi"


def stale_path(source_url: str) -> str:
    path = urlparse(source_url).path
    if not path.startswith("/"):
        path = "/" + path
    return path


def resolve_document_id(session: requests.Session, source_url: str, timeout: int) -> int:
    stale = quote(stale_path(source_url), safe="")
    response = session.get(
        f"{BASE}/dokumenty-sbirky/{stale}/id",
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, int):
        return payload
    if isinstance(payload, str) and payload.isdigit():
        return int(payload)
    if isinstance(payload, dict):
        for key in ("dokumentId", "id"):
            value = payload.get(key)
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                return int(value)
    raise ValueError(f"Unexpected document-id payload for {source_url}: {payload!r}")


def build_manifest(timeout: int = 60) -> list[dict[str, object]]:
    registry = build_registry()
    source_to_keys: dict[str, list[str]] = {}
    for provision in registry["provisions"]:
        source_to_keys.setdefault(provision["source_url"], []).append(provision["key"])

    session = requests.Session()
    session.headers.update({"User-Agent": "TaxTreat legal-source verifier/1.0"})
    manifest: list[dict[str, object]] = []
    for source_url, provision_keys in sorted(source_to_keys.items()):
        document_id = resolve_document_id(session, source_url, timeout)
        manifest.append(
            {
                "source_url": source_url,
                "document_id": document_id,
                "provision_keys": sorted(provision_keys),
                "pdf_sha256": None,
                "pdf_path": None,
                "resolved": False,
            }
        )
    if len(manifest) != 101:
        raise AssertionError(f"Expected 101 official treaty instruments, got {len(manifest)}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(timeout=args.timeout)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Official treaty PDF manifest: {len(manifest)}/101 instruments resolved to document IDs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
