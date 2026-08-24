from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
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
    status_instrument_flag: bool
    applicability_status: str
    release_universe_candidate: bool
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


def _table_value(nodes: list[Tag], labels: tuple[str, ...]) -> str | None:
    labels_lower = tuple(label.lower() for label in labels)
    for node in nodes:
        for row in node.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) < 2:
                continue
            label = _clean(cells[0].get_text(" ", strip=True)).lower()
            if any(candidate in label for candidate in labels_lower):
                value = _clean(cells[1].get_text(" ", strip=True))
                return value or None
    return None


def _field_value(
    nodes: list[Tag],
    text: str,
    *,
    table_labels: tuple[str, ...],
    text_labels: tuple[str, ...],
) -> str | None:
    value = _table_value(nodes, table_labels)
    if value is not None:
        return value
    for label in text_labels:
        value = _value_after_label(text, label)
        if value is not None:
            return value
    return None


def _treaty_text_links(nodes: list[Tag]) -> tuple[str, ...]:
    links: list[str] = []
    for node in nodes:
        for row in node.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) < 2:
                continue
            label = _clean(cells[0].get_text(" ", strip=True)).lower()
            if "abkommenstext" not in label and "treaty text" not in label:
                continue
            for anchor in cells[1].find_all("a", href=True):
                href = str(anchor["href"]).strip()
                if href and href not in links:
                    links.append(href)

    if links:
        return tuple(links)

    # Compatibility fallback for archived/simple fixtures where the official
    # source is represented as paragraphs rather than a table. Restrict links
    # to the paragraph that identifies itself as the treaty-text field.
    for node in nodes:
        label = _clean(node.get_text(" ", strip=True)).lower()
        if "abkommenstext" not in label and "treaty text" not in label:
            continue
        for anchor in node.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            if href and href not in links:
                links.append(href)
    return tuple(links)


def _parse_exact_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _classify_applicability(
    *,
    partner_label: str,
    entry_into_force: str | None,
    effective_from: str | None,
    as_of: date,
) -> str:
    normalized_partner = partner_label.lower()
    if "udssr" in normalized_partner or "ussr" in normalized_partner:
        return "historical_parent_instrument"

    entry_text = (entry_into_force or "").strip().lower()
    if not entry_text or "noch offen" in entry_text or "pending" in entry_text:
        return "signed_not_in_force"

    if not effective_from:
        return "in_force_effective_date_unresolved"

    exact_effective = _parse_exact_date(effective_from)
    if exact_effective is not None and exact_effective > as_of:
        return "in_force_future_effective"

    return "current_candidate"


def parse_bmf_treaty_list(
    html: str,
    *,
    as_of: date | None = None,
) -> list[AustrianTreatySourceRecord]:
    soup = BeautifulSoup(html, "lxml")
    records: list[AustrianTreatySourceRecord] = []
    reference_date = as_of or date.today()

    for heading in soup.find_all("h3"):
        partner = _clean(heading.get_text(" ", strip=True))
        if not partner or partner.lower() in {"serviceangebote", "wichtige themen"}:
            continue

        nodes = list(_section_nodes(heading))
        text = "\n".join(node.get_text(" ", strip=True) for node in nodes)
        if "Unterzeichnung" not in text and "Date of Signature" not in text:
            continue

        signature = _field_value(
            nodes,
            text,
            table_labels=("unterzeichnung", "date of signature"),
            text_labels=("Unterzeichnung / Date of Signature", "Unterzeichnung"),
        )
        entry_into_force = _field_value(
            nodes,
            text,
            table_labels=("inkrafttreten", "entry into force"),
            text_labels=("Inkrafttreten / Entry into Force", "Inkrafttreten"),
        )
        effective_from = _field_value(
            nodes,
            text,
            table_labels=("anwendbar ab", "effective from"),
            text_labels=("Anwendbar ab / Effective From", "Anwendbar ab"),
        )
        applicability_status = _classify_applicability(
            partner_label=partner,
            entry_into_force=entry_into_force,
            effective_from=effective_from,
            as_of=reference_date,
        )
        status_instrument_flag = bool(
            re.search(r"\bsuspend(?:iert|ierung|ed|sion)?\b", text, flags=re.IGNORECASE)
        )

        records.append(
            AustrianTreatySourceRecord(
                partner_label=partner,
                signature=signature,
                entry_into_force=entry_into_force,
                effective_from=effective_from,
                treaty_links=_treaty_text_links(nodes),
                mli_flag=(
                    "Multilaterales Instrument" in text
                    or re.search(r"\bMLI\b", text) is not None
                ),
                status_instrument_flag=status_instrument_flag,
                applicability_status=applicability_status,
                release_universe_candidate=(applicability_status == "current_candidate"),
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
    reference_date = date.fromisoformat(as_of) if as_of else date.today()
    records = parse_bmf_treaty_list(html, as_of=reference_date)
    current_candidates = [row for row in records if row.release_universe_candidate]
    return {
        "schema_version": 2,
        "source_country": "AT",
        "status": "machine_source_inventory_not_reviewed",
        "as_of": reference_date.isoformat(),
        "source_url": BMF_DTT_LIST_URL,
        "source_page_record_count": len(records),
        "treaty_partner_count": len(records),
        "treaty_scope_count": len(records) * 3,
        "release_universe_candidate_count": len(current_candidates),
        "release_universe_scope_count": len(current_candidates) * 3,
        "mli_flagged_relationship_count": sum(row.mli_flag for row in records),
        "status_instrument_flagged_relationship_count": sum(
            row.status_instrument_flag for row in records
        ),
        "applicability_status_counts": dict(
            sorted(
                {
                    status: sum(row.applicability_status == status for row in records)
                    for status in {row.applicability_status for row in records}
                }.items()
            )
        ),
        "records": [
            {
                **asdict(row),
                "treaty_links": list(row.treaty_links),
            }
            for row in records
        ],
        "release_constraints": [
            "Machine extraction does not constitute legal review or release.",
            "Only records classified as current_candidate may enter the current treaty review universe; signed-not-in-force, future-effective and historical parent instruments remain excluded until their status changes or is specifically resolved.",
            "MLI flags are discovery signals only and require bilateral matching and WHT-effective-date adjudication.",
            "Status-instrument flags are discovery signals only and require primary-source legal effect review.",
            "Treaty links are restricted to the BMF treaty-text row and must be resolved to authoritative current instrument chains before rate extraction.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-html", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--as-of")
    args = parser.parse_args()

    html = (
        args.input_html.read_text(encoding="utf-8")
        if args.input_html
        else fetch_bmf_treaty_list()
    )
    inventory = build_inventory(html, as_of=args.as_of)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"AT treaty source inventory: {inventory['source_page_record_count']} page records / "
        f"{inventory['release_universe_candidate_count']} current candidates / "
        f"{inventory['release_universe_scope_count']} current scopes / "
        f"{inventory['mli_flagged_relationship_count']} MLI discovery flags"
    )


if __name__ == "__main__":
    main()
