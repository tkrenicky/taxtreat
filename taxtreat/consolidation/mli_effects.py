from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
DEFAULT_OUTPUT = ROOT / "data" / "legal_consolidation" / "mli_wht_effects.json"
EXPECTED_CZECH_WHT_YEAR = {
    "AL": 2025, "AM": 2024, "AU": 2021, "AZ": 2025, "BA": 2025,
    "BB": 2025, "BE": 2021, "BG": 2023, "BH": 2025, "CA": 2021,
    "CH": 2022, "CL": 2022, "CN": 2023, "CY": 2021, "DE": 2026,
    "DK": 2021, "EG": 2021, "ES": 2023, "FI": 2021, "FR": 2021,
    "GB": 2021, "GE": 2021, "GR": 2022, "HK": 2024, "HR": 2022,
    "HU": 2022, "ID": 2027, "IE": 2021, "IL": 2021, "IN": 2021,
    "IS": 2021, "JP": 2021, "JO": 2025, "KZ": 2025, "LI": 2021,
    "LT": 2021, "LU": 2021, "LV": 2021, "MN": 2025, "MT": 2021,
    "MX": 2024,
    "MY": 2025, "NL": 2021, "NO": 2021, "NZ": 2021, "PA": 2025,
    "PK": 2022, "PL": 2021, "PT": 2021, "RO": 2024, "RS": 2021,
    "RU": 2021, "SA": 2025, "SG": 2021, "SI": 2021, "SK": 2021,
    "TH": 2025, "TN": 2025, "UA": 2025, "VN": 2025, "ZA": 2023,
    "AT": 2021,
}


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(html.unescape(href))


def _download(url: str) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": "TaxTreat-official-source-refresh/1.0"},
    )
    with urlopen(request, timeout=60) as response:
        return response.read()


def _pdf_url(page_url: str, page_html: bytes) -> str:
    parser = _LinkParser()
    parser.feed(page_html.decode("utf-8"))
    candidates = [
        urljoin(page_url, link)
        for link in parser.links
        if link.casefold().endswith(".pdf")
        or "/assets/attachments/" in link.casefold()
        or "/assets/cs/media/" in link.casefold()
    ]
    if not candidates:
        raise ValueError(f"No official PDF was found on {page_url}.")
    return candidates[0]


def _pdf_text(pdf_bytes: bytes) -> str:
    completed = subprocess.run(
        ["pdftotext", "-layout", "-", "-"],
        input=pdf_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.decode("utf-8", "replace")


def _compact(value: str) -> str:
    return " ".join(value.replace("\x0c", " ").split())


def _wht_excerpt(text: str, year: int) -> str:
    pattern = re.compile(
        r"(.{0,120}dan[eě].{0,180}?sr[aá][zž]k.{0,520}?"
        rf"1\.\s*ledn[au]\s+{year}.{{0,100}})",
        re.IGNORECASE | re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        raise ValueError(f"Czech WHT effective date 1 January {year} not found.")
    return _compact(matches[0].group(1))


def build_mli_effects(
    inventory: dict[str, Any],
    *,
    documents: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    effects: list[dict[str, Any]] = []
    for partner in inventory["partners"]:
        notices = [
            source
            for source in partner["related_instruments"]
            if source["source_type"] == "mli_synthesised_notice"
        ]
        if not notices:
            continue
        if len(notices) != 1:
            raise ValueError(
                f"{partner['iso2']} must have exactly one MLI notice source."
            )
        notice = notices[0]
        expected_year = EXPECTED_CZECH_WHT_YEAR.get(partner["iso2"])
        if expected_year is None:
            raise ValueError(
                f"No independently checked MLI WHT year for {partner['iso2']}."
            )
        pdf_url, text = documents[notice["url"]]
        excerpt = _wht_excerpt(text, expected_year)
        effects.append(
            {
                "effect_id": f"CZ-{partner['iso2']}-MLI-WHT-PPT",
                "source_country": "CZ",
                "recipient_country": partner["iso2"],
                "recipient_country_name": partner["country"],
                "applies_to_income_types": [
                    "dividend",
                    "interest",
                    "royalty",
                ],
                "mli_article": "Article 7(1) PPT",
                "effective_from": f"{expected_year}-01-01",
                "source_page_id": notice["source_id"],
                "source_page_url": notice["url"],
                "source_pdf_url": pdf_url,
                "source_excerpt": excerpt,
                "source_excerpt_sha256": hashlib.sha256(
                    excerpt.encode("utf-8")
                ).hexdigest(),
                "verification_status": "needs_review",
            }
        )
    if len(effects) != 62:
        raise ValueError(f"Expected 62 official MLI notices, found {len(effects)}.")
    return {
        "schema_version": 1,
        "dataset_release": "cz-mli-wht-effects-2026-08-03-candidate.1",
        "legal_data_cutoff": inventory["source_page"]["legal_data_cutoff"],
        "effects": sorted(effects, key=lambda row: row["recipient_country"]),
    }


def fetch_mli_documents(
    inventory: dict[str, Any],
) -> dict[str, tuple[str, str]]:
    page_urls = sorted(
        {
            source["url"]
            for partner in inventory["partners"]
            for source in partner["related_instruments"]
            if source["source_type"] == "mli_synthesised_notice"
        }
    )

    def fetch_one(page_url: str) -> tuple[str, str]:
        page_html = _download(page_url)
        pdf_url = _pdf_url(page_url, page_html)
        return pdf_url, _pdf_text(_download(pdf_url))

    documents: dict[str, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_one, page_url): page_url
            for page_url in page_urls
        }
        for future in as_completed(futures):
            page_url = futures[future]
            documents[page_url] = future.result()
    return documents


def refresh_mli_effects(
    *,
    inventory_path: str | Path = DEFAULT_INVENTORY,
) -> dict[str, Any]:
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    return build_mli_effects(
        inventory,
        documents=fetch_mli_documents(inventory),
    )


def write_mli_effects(
    payload: dict[str, Any],
    path: str | Path = DEFAULT_OUTPUT,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
