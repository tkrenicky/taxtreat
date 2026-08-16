#!/usr/bin/env python3
"""Recover authoritative e-Sbírka treaty PDFs referenced by a manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

BASE = "https://e-sbirka.gov.cz/sbr-externi"
FILE_BASE = "https://e-sbirka.gov.cz/souborove-sluzby"
USER_AGENT = "TaxTreat legal-source verifier/1.0"


def legacy_verified_url(document_id: int) -> str:
    return f"{BASE}/stahni/overena-zneni/{document_id}"


def legally_binding_complete_url(document_id: int) -> str:
    return f"{BASE}/stahni/pravne-zavazne-zneni-vcetne-uplnych/{document_id}"


def async_status_url(request_id: str) -> str:
    return f"{FILE_BASE}/verejne-pozadavky-dokumenty/pozadavky/{request_id}"


def async_file_url(file_id: str) -> str:
    return f"{FILE_BASE}/soubory/{file_id}"


def is_pdf_response(response: requests.Response) -> bool:
    return response.status_code == 200 and response.content.startswith(b"%PDF-")


def _new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _resolve_async_download(
    session: requests.Session,
    response: requests.Response,
    timeout: int,
    poll_interval: float = 0.5,
) -> requests.Response:
    """Resolve the asynchronous e-Sbírka download response to the final PDF response."""
    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError):
        return response

    status = str(payload.get("stavPozadavku") or "").upper()
    request_id = payload.get("pozadavekId")
    file_id = payload.get("id")

    if status == "OK" and file_id:
        return session.get(async_file_url(str(file_id)), timeout=timeout, allow_redirects=True)

    if status != "PROBIHA" or not request_id:
        return response

    deadline = time.monotonic() + timeout
    current = payload
    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        status_response = session.get(
            async_status_url(str(request_id)), timeout=timeout, allow_redirects=True
        )
        try:
            current = status_response.json()
        except (ValueError, json.JSONDecodeError):
            return status_response
        status = str(current.get("stav") or current.get("stavPozadavku") or "").upper()
        if status == "CHYBA":
            return status_response
        file_id = current.get("id")
        if status == "OK" and file_id:
            return session.get(async_file_url(str(file_id)), timeout=timeout, allow_redirects=True)

    return response


def download_pdf(
    session: requests.Session, document_id: int, timeout: int = 90
) -> tuple[requests.Response, str]:
    attempts = [
        (legally_binding_complete_url(document_id), "pravne_zavazne_zneni_vcetne_uplnych"),
        (legacy_verified_url(document_id), "overena_zneni"),
    ]
    last: requests.Response | None = None
    for url, mode in attempts:
        response = session.get(
            url,
            params={"stahniOpravnouSadu": "false"},
            timeout=timeout,
            allow_redirects=True,
        )
        if mode == "pravne_zavazne_zneni_vcetne_uplnych" and not is_pdf_response(response):
            response = _resolve_async_download(session, response, timeout)
        last = response
        if is_pdf_response(response):
            return response, mode
    assert last is not None
    return last, "unresolved"


def _recover_one(
    item: dict[str, Any],
    pdf_dir: Path,
    timeout: int,
) -> tuple[int, dict[str, Any]]:
    document_id = int(item["document_id"])
    session = _new_session()
    try:
        response, mode = download_pdf(session, document_id, timeout=timeout)
    finally:
        session.close()

    update: dict[str, Any]
    if not is_pdf_response(response):
        update = {
            "download_status": "unresolved_legal_pdf",
            "resolved": False,
            "last_http_status": response.status_code,
            "last_content_type": response.headers.get("content-type"),
        }
        return document_id, update

    path = pdf_dir / f"{document_id}.pdf"
    path.write_bytes(response.content)
    update = {
        "pdf_path": str(path),
        "pdf_sha256": hashlib.sha256(response.content).hexdigest(),
        "pdf_bytes": len(response.content),
        "download_status": "downloaded",
        "download_mode": mode,
        "resolved": True,
        "official_download_url": str(response.url),
    }
    return document_id, update


def recover_manifest(
    manifest_path: Path,
    pdf_dir: Path,
    timeout: int = 90,
    workers: int = 12,
) -> dict[str, int]:
    manifest: list[dict[str, Any]] = json.loads(manifest_path.read_text(encoding="utf-8"))
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pending = [item for item in manifest if not item.get("pdf_sha256")]
    updates: dict[int, dict[str, Any]] = {}

    if workers <= 1:
        for item in pending:
            document_id, update = _recover_one(item, pdf_dir, timeout)
            updates[document_id] = update
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_recover_one, item, pdf_dir, timeout): int(item["document_id"])
                for item in pending
            }
            for future in as_completed(futures):
                document_id = futures[future]
                try:
                    resolved_document_id, update = future.result()
                except requests.RequestException as exc:
                    updates[document_id] = {
                        "download_status": "request_error",
                        "resolved": False,
                        "last_error": type(exc).__name__,
                    }
                    continue
                updates[resolved_document_id] = update

    recovered = 0
    failed = 0
    for item in manifest:
        update = updates.get(int(item["document_id"]))
        if update is None:
            continue
        item.update(update)
        if update.get("pdf_sha256"):
            recovered += 1
        else:
            failed += 1

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    valid = sum(bool(item.get("pdf_sha256")) for item in manifest)
    return {"total": len(manifest), "valid": valid, "recovered": recovered, "failed": failed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="reports/treaty_verified_pdf_manifest.json")
    parser.add_argument("--pdf-dir", default="data/legal_texts/verified_source_pdfs")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    result = recover_manifest(
        Path(args.manifest),
        Path(args.pdf_dir),
        timeout=args.timeout,
        workers=max(1, args.workers),
    )
    print(f"Official instruments: {result['total']}")
    print(f"Valid official PDFs: {result['valid']}")
    print(f"Recovered this run: {result['recovered']}")
    print(f"Still unresolved: {result['total'] - result['valid']}")
    return 0 if result["valid"] == result["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
