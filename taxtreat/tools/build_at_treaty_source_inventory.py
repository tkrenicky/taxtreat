from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup, Tag


BMF_DTT_LIST_URL = (
    "https://www.bmf.gv.at/themen/steuern/internationales-steuerrecht/"
    "doppelbesteuerungsabkommen/dba-liste.html"
)
DEFAULT_OUTPUT = Path(
    "data/legal_reviews/at_outbound/treaty_source_inventory_machine.json"
)


@dataclass(frozen=True)
class AustrianTreatySourceRecord:
    partner_label: str
    signature: str | None
    entry_into_force: str | None
    effective_from: str | None
    treaty_links: tuple[str, ...]
    mli_flag: bool
    source_url: str = BMF_DTT_LIST_URL


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _value_after_label(text: str, label: str) -> str | None:
    pattern = rf"{re.escape(label)}\s*\|\s*([^\n]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return _clean(match.group(1)) if match else None


def _section_nodes(heading: Tag) -> Iterable[Tag]:
    for node in heading.next_siblings:
        if isinstance(node, Tag) and node.name in {"h2", "h3"}:
            break
        if isinstance(node, Tag):
            yield node


def parse_bmf_treaty_list(html: str) -> list[AustrianTreatySourceRecord]:
    soup = BeautifulSoup(html, "lxml")
    records: list[AustrianTreatySourceRecord] = []

    for heading in soup.find_all("h3"):
        partner = _clean(heading.get_text(" ", strip=True))
        if not partner or partner.lower() in {"serviceangebote", "wichtige themen"}:
            continue

        nodes = list(_section_nodes(heading))
        text = "\n".join(node.get_text(" ", strip=True) for node in nodes)
        if "Unterzeichnung" not in text and "Date of Signature" not in text:
            continue

        links: list[str] = []
        for node in nodes:
            for anchor in node.find_all("a", href=True):
                href = str(anchor["href"]).strip()
                if href and href not in links:
                    links.append(href)

        records.append(
            AustrianTreatySourceRecord(
                partner_label=partner,
                signature=(
                    _value_after_label(text, "Unterzeichnung / Date of Signature")
                    or _value_after_label(text, "Unterzeichnung")
                ),
                entry_into_force=(
                    _value_after_label(text, "Inkrafttreten / Entry into Force")
                    or _value_after_label(text, "Inkrafttreten")
                ),
                effective_from=(
                    _value_after_label(text, "Anwendbar ab / Effective From")
                    or _value_after_label(text, "Anwendbar ab")
                ),
                treaty_links=tuple(links),
                mli_flag=(
                    "Multilaterales Instrument" in text
                    or re.search(r"\bMLI\b", text) is not None
                ),
            )
        )

    if not records:
        raise ValueError("No treaty records parsed from Austrian BMF DTT list")
    return records


def fetch_bmf_treaty_list(*, timeout: int = 30) -> str:
    response = requests.get(
        BMF_DTT_LIST_URL,
        timeout=timeout,
        headers={"User-Agent": "TaxTreat legal-source inventory/1.0"},
    )
    response.raise_for_status()
    return response.text


def build_inventory(html: str, *, as_of: str | None = None) -> dict:
    records = parse_bmf_treaty_list(html)
    return {
        "schema_version": 1,
        "source_country": "AT",
        "status": "machine_source_inventory_not_reviewed",
        "as_of": as_of or date.today().isoformat(),
        "source_url": BMF_DTT_LIST_URL,
        "treaty_partner_count": len(records),
        "treaty_scope_count": len(records) * 3,
        "mli_flagged_relationship_count": sum(row.mli_flag for row in records),
        "records": [
            {
                **asdict(row),
                "treaty_links": list(row.treaty_links),
            }
            for row in records
        ],
        "release_constraints": [
            "Machine extraction does not constitute legal review or release.",
            "MLI flags are discovery signals only and require bilateral matching and WHT-effective-date adjudication.",
            "Treaty links must be resolved to authoritative current instrument chains before rate extraction.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-html", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    html = (
        args.input_html.read_text(encoding="utf-8")
        if args.input_html
        else fetch_bmf_treaty_list()
    )
    inventory = build_inventory(html)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"AT treaty source inventory: {inventory['treaty_partner_count']} partners / "
        f"{inventory['treaty_scope_count']} scopes / "
        f"{inventory['mli_flagged_relationship_count']} MLI discovery flags"
    )


if __name__ == "__main__":
    main()
