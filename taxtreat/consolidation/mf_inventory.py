from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from taxtreat.registry.legal_scope import load_partner_registry


MF_OVERVIEW_URL = (
    "https://mf.gov.cz/cs/zahranici-a-eu/"
    "smlouvy-o-zamezeni-dvojiho-zdaneni/prehled-platnych-smluv"
)
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"


def _compact(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _name_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", _compact(value))
    return "".join(
        character
        for character in normalized.casefold()
        if character.isalnum()
    )


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[dict[str, Any]]]] = []
        self.all_text: list[str] = []
        self._table: list[list[dict[str, Any]]] | None = None
        self._row: list[dict[str, Any]] | None = None
        self._cell: dict[str, Any] | None = None
        self._link: dict[str, Any] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = {"text_parts": [], "links": []}
        elif tag == "a" and self._cell is not None:
            self._link = {
                "href": attributes.get("href"),
                "text_parts": [],
            }

    def handle_data(self, data: str) -> None:
        self.all_text.append(data)
        if self._cell is not None:
            self._cell["text_parts"].append(data)
        if self._link is not None:
            self._link["text_parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._link is not None and self._cell is not None:
            href = self._link.get("href")
            if href:
                self._cell["links"].append(
                    {
                        "label": _compact("".join(self._link["text_parts"])),
                        "url": urljoin(MF_OVERVIEW_URL, href),
                    }
                )
            self._link = None
        elif tag in {"td", "th"} and self._cell is not None:
            if self._row is not None:
                self._row.append(
                    {
                        "text": _compact("".join(self._cell["text_parts"])),
                        "links": self._cell["links"],
                    }
                )
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._table is not None and self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def _iso_date(value: str) -> str:
    match = re.fullmatch(r"\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*", value)
    if not match:
        raise ValueError(f"Unrecognised Czech date: {value!r}")
    day, month, year = map(int, match.groups())
    return date(year, month, day).isoformat()


def _source_id(iso2: str, label: str, url: str) -> str:
    token = f"{iso2}|{label}|{url}".encode("utf-8")
    return f"CZ-MF-{iso2}-{hashlib.sha256(token).hexdigest()[:12].upper()}"


def _classify_note_link(
    label: str,
    *,
    mli_listed: bool,
    after_mli_convention: bool,
) -> str:
    lowered = label.casefold()
    if "úmluva č. 32/2020" in lowered:
        return "mli_convention"
    if "protokol" in lowered:
        return "protocol"
    if "redakční oprava" in lowered:
        return "correction"
    if "sdělení č. 439/2024" in lowered:
        return "mli_effect_notice"
    if "fz č." in lowered and mli_listed and after_mli_convention:
        return "mli_synthesised_notice"
    if "sdělení" in lowered:
        return "status_or_amendment_notice"
    if "pokyn" in lowered:
        return "administrative_guidance"
    return "other_related_instrument"


def _normalise_link(
    raw: dict[str, str],
    *,
    iso2: str,
    source_type: str,
) -> dict[str, str]:
    return {
        "source_id": _source_id(iso2, raw["label"], raw["url"]),
        "source_type": source_type,
        "label": raw["label"],
        "url": raw["url"],
        "authority": "Czech Ministry of Finance / official publication",
    }


def build_inventory(
    html_text: str,
    *,
    retrieved_at: str | None = None,
) -> dict[str, Any]:
    parser = _TableParser()
    parser.feed(html_text)
    table = next(
        (
            candidate
            for candidate in parser.tables
            if candidate
            and candidate[0]
            and "Smluvní stát" in candidate[0][0]["text"]
        ),
        None,
    )
    if table is None:
        raise ValueError("MF treaty overview table was not found.")

    partners_by_name = {
        _name_key(partner["country"]): partner
        for partner in load_partner_registry()
    }
    rows: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for cells in table[1:]:
        if len(cells) != 5:
            raise ValueError("MF treaty overview row must contain five cells.")
        country_name = cells[0]["text"]
        partner = partners_by_name.get(_name_key(country_name))
        if partner is None:
            raise ValueError(
                f"MF treaty overview contains an unknown partner: {country_name!r}."
            )
        iso2 = partner["iso2"]
        if iso2 in seen_codes:
            raise ValueError(f"Duplicate MF treaty overview partner: {iso2}.")
        seen_codes.add(iso2)

        note_text = cells[4]["text"]
        mli_listed = "32/2020" in note_text
        base_instruments = [
            _normalise_link(link, iso2=iso2, source_type="base_treaty")
            for link in cells[2]["links"]
        ]
        financial_reporter_sources = [
            _normalise_link(
                link,
                iso2=iso2,
                source_type="financial_reporter_publication",
            )
            for link in cells[3]["links"]
        ]
        related_instruments = []
        after_mli_convention = False
        for link in cells[4]["links"]:
            source_type = _classify_note_link(
                link["label"],
                mli_listed=mli_listed,
                after_mli_convention=after_mli_convention,
            )
            related_instruments.append(
                _normalise_link(
                    link,
                    iso2=iso2,
                    source_type=source_type,
                )
            )
            if source_type == "mli_convention":
                after_mli_convention = True
        related_types = {
            instrument["source_type"] for instrument in related_instruments
        }
        rows.append(
            {
                "country": partner["country"],
                "iso2": iso2,
                "entry_into_force": _iso_date(cells[1]["text"]),
                "base_instruments": base_instruments,
                "financial_reporter_sources": financial_reporter_sources,
                "related_instruments": related_instruments,
                "official_note": note_text,
                "mli_listed": mli_listed,
                "mli_notice_available": bool(
                    related_types.intersection(
                        {"mli_effect_notice", "mli_synthesised_notice"}
                    )
                ),
                "protocol_listed": "protocol" in related_types,
                "inventory_status": "official_inventory_captured",
            }
        )

    expected_codes = {partner["iso2"] for partner in load_partner_registry()}
    if seen_codes != expected_codes:
        missing = sorted(expected_codes.difference(seen_codes))
        extra = sorted(seen_codes.difference(expected_codes))
        raise ValueError(
            f"MF inventory mismatch; missing={missing}, extra={extra}."
        )

    page_text = _compact(" ".join(parser.all_text))
    as_of_match = re.search(
        r"podle stavu k\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        page_text,
        re.IGNORECASE,
    )
    if not as_of_match:
        raise ValueError("MF overview legal-data cut-off was not found.")
    page_hash = hashlib.sha256(html_text.encode("utf-8")).hexdigest()
    return {
        "schema_version": 1,
        "source_page": {
            "url": MF_OVERVIEW_URL,
            "authority": "Ministry of Finance of the Czech Republic",
            "legal_data_cutoff": _iso_date(as_of_match.group(1)),
            "retrieved_at": retrieved_at or datetime.now().date().isoformat(),
            "html_sha256": page_hash,
        },
        "partners": sorted(rows, key=lambda row: row["iso2"]),
    }


def fetch_overview() -> str:
    request = Request(
        MF_OVERVIEW_URL,
        headers={"User-Agent": "TaxTreat-official-source-refresh/1.0"},
    )
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def write_inventory(
    payload: dict[str, Any],
    path: str | Path = DEFAULT_OUTPUT,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
