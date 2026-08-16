from __future__ import annotations

import argparse
import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Any

import requests

BASE = "https://e-sbirka.gov.cz/sbr-externi"
FILE_BASE = "https://e-sbirka.gov.cz/souborove-sluzby"
USER_AGENT = "TaxTreat legal-source verifier/1.0"


def structured_url(document_id: int) -> str:
    return f"{BASE}/stahni/informativni-zneni/{document_id}/JSON"


def async_status_url(request_id: str) -> str:
    return f"{FILE_BASE}/verejne-pozadavky-dokumenty/pozadavky/{request_id}"


def async_file_url(file_id: str) -> str:
    return f"{FILE_BASE}/soubory/{file_id}"


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _resolve_response(
    session: requests.Session,
    response: requests.Response,
    timeout: int,
) -> requests.Response:
    try:
        payload = response.json()
    except ValueError:
        return response
    if not isinstance(payload, dict):
        return response

    status = str(payload.get("stavPozadavku") or payload.get("stav") or "").upper()
    request_id = payload.get("pozadavekId")
    file_id = payload.get("id")
    if status == "OK" and file_id:
        return session.get(async_file_url(str(file_id)), timeout=timeout, allow_redirects=True)
    if status != "PROBIHA" or not request_id:
        return response

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(0.5)
        poll = session.get(async_status_url(str(request_id)), timeout=timeout, allow_redirects=True)
        try:
            current = poll.json()
        except ValueError:
            return poll
        if not isinstance(current, dict):
            return poll
        status = str(current.get("stav") or current.get("stavPozadavku") or "").upper()
        if status == "CHYBA":
            return poll
        file_id = current.get("id")
        if status == "OK" and file_id:
            return session.get(async_file_url(str(file_id)), timeout=timeout, allow_redirects=True)
    return response


def _json_payloads(content: bytes) -> list[tuple[str, bytes]]:
    if content.startswith(b"PK"):
        with zipfile.ZipFile(BytesIO(content)) as archive:
            return [
                (name, archive.read(name))
                for name in archive.namelist()
                if name.lower().endswith(".json") and not name.endswith("/")
            ]
    stripped = content.lstrip()
    if stripped.startswith((b"{", b"[")):
        return [("payload.json", content)]
    return []


def fetch_one(document_id: int, output_dir: Path, timeout: int) -> dict[str, Any]:
    session = _session()
    try:
        initial = session.get(structured_url(document_id), timeout=timeout, allow_redirects=True)
        final = _resolve_response(session, initial, timeout)
    finally:
        session.close()

    result: dict[str, Any] = {
        "document_id": document_id,
        "initial_status": initial.status_code,
        "final_status": final.status_code,
        "content_type": final.headers.get("content-type"),
        "bytes": len(final.content),
        "json_files": [],
        "status": "unresolved",
    }
    if final.status_code != 200:
        return result

    payloads = _json_payloads(final.content)
    if not payloads:
        return result

    target = output_dir / str(document_id)
    target.mkdir(parents=True, exist_ok=True)
    saved = []
    for index, (name, raw) in enumerate(payloads, 1):
        try:
            parsed = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        out = target / f"{index:02d}.json"
        out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        saved.append({"archive_name": name, "path": str(out), "bytes": len(raw)})
    result["json_files"] = saved
    result["status"] = "structured_json_saved" if saved else "unresolved"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="reports/treaty_verified_pdf_manifest.json")
    parser.add_argument("--output-dir", default="artifacts/structured_sources")
    parser.add_argument("--report", default="reports/treaty_structured_source_manifest.json")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(fetch_one, int(item["document_id"]), output_dir, args.timeout): int(item["document_id"])
            for item in manifest
        }
        for future in as_completed(futures):
            document_id = futures[future]
            try:
                results.append(future.result())
            except requests.RequestException as exc:
                results.append({
                    "document_id": document_id,
                    "status": "request_error",
                    "error": type(exc).__name__,
                })

    results.sort(key=lambda item: int(item["document_id"]))
    resolved = sum(item.get("status") == "structured_json_saved" for item in results)
    report = {
        "counts": {"instruments": len(results), "structured_json_resolved": resolved, "unresolved": len(results) - resolved},
        "instruments": results,
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Structured e-Sbirka sources: {resolved}/{len(results)} resolved")
    return 0 if resolved == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
