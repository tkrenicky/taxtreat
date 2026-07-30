from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import csv
import hashlib
import json
import time

DATASET = Path("data/cz_master_dataset.csv")
ARCHIVE = Path("data/source_archive")
MANIFEST = Path("data/source_manifest.json")

ALLOWED_DOMAINS = {
    "financnisprava.gov.cz",
    "financnisprava.cz",
    "mfcr.cz",
    "zakonyprolidi.cz",
    "e-sbirka.cz",
    "eur-lex.europa.eu",
    "oecd.org",
    "bundesfinanzministerium.de",
}

SOURCE_COLUMNS = (
    "official_treaty_source",
    "official_domestic_source",
)


def domain_allowed(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in ALLOWED_DOMAINS
    )


def download(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "TaxTreat/1.0 official-source-archiver",
            "Accept": "text/html,application/pdf,text/plain,*/*",
        },
    )

    with urlopen(request, timeout=30) as response:
        return response.read()


def main() -> None:
    if not DATASET.exists():
        raise SystemExit(f"Dataset not found: {DATASET}")

    ARCHIVE.mkdir(parents=True, exist_ok=True)

    urls: set[str] = set()

    with DATASET.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            for column in SOURCE_COLUMNS:
                url = (row.get(column) or "").strip()

                if url:
                    urls.add(url)

    manifest: list[dict[str, object]] = []
    failed = 0

    for index, url in enumerate(sorted(urls), start=1):
        record: dict[str, object] = {
            "url": url,
            "status": "pending",
        }

        if not domain_allowed(url):
            record["status"] = "rejected"
            record["error"] = "Domain is not included in the official-source allowlist."
            manifest.append(record)
            failed += 1
            continue

        try:
            content = download(url)
            digest = hashlib.sha256(content).hexdigest()
            suffix = Path(urlparse(url).path).suffix.lower() or ".bin"
            destination = ARCHIVE / f"{digest}{suffix}"
            destination.write_bytes(content)

            record.update({
                "status": "downloaded",
                "sha256": digest,
                "file": str(destination),
                "size_bytes": len(content),
            })

        except Exception as exc:
            record["status"] = "failed"
            record["error"] = str(exc)
            failed += 1

        manifest.append(record)

        if index < len(urls):
            time.sleep(1)

    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Official URLs found: {len(urls)}")
    print(f"Successfully archived: {sum(r['status'] == 'downloaded' for r in manifest)}")
    print(f"Rejected or failed: {failed}")
    print(f"Manifest: {MANIFEST}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
