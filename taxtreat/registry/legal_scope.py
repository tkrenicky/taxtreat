from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taxtreat.countries.registry import get_country_config


SUPPORTED_INCOME_TYPES = ("dividend", "interest", "royalty")
DEFAULT_PARTNER_REGISTRY = get_country_config("CZ").treaty_partner_registry


def load_partner_registry(
    path: str | Path | None = None,
    *,
    source_country: str = "CZ",
) -> list[dict[str, str]]:
    config = get_country_config(source_country)
    registry_path = Path(path) if path is not None else config.treaty_partner_registry
    if registry_path is None:
        return []

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Treaty-partner registry must be a JSON list.")

    partners: list[dict[str, str]] = []
    seen_codes: set[str] = set()
    seen_files: set[str] = set()
    for raw in payload:
        if not isinstance(raw, dict):
            raise ValueError("Every treaty partner must be an object.")
        country = raw.get("country")
        iso2 = raw.get("iso2")
        parsed_file = raw.get("parsed_file")
        if not all(isinstance(value, str) and value for value in (
            country,
            iso2,
            parsed_file,
        )):
            raise ValueError(
                "Every treaty partner requires country, iso2 and parsed_file."
            )
        if len(iso2) != 2 or iso2 != iso2.upper() or not iso2.isalpha():
            raise ValueError(f"Invalid partner ISO-like code: {iso2!r}.")
        if not parsed_file.endswith(".json") or "/" in parsed_file:
            raise ValueError(f"Invalid parsed treaty filename: {parsed_file!r}.")
        if iso2 in seen_codes:
            raise ValueError(f"Duplicate treaty-partner code: {iso2}.")
        if parsed_file in seen_files:
            raise ValueError(
                f"Duplicate parsed treaty filename: {parsed_file}."
            )
        seen_codes.add(iso2)
        seen_files.add(parsed_file)
        partners.append(
            {
                "country": country,
                "iso2": iso2,
                "parsed_file": parsed_file,
            }
        )

    return partners


def expected_legal_scopes(
    path: str | Path | None = None,
    *,
    source_country: str = "CZ",
) -> list[dict[str, Any]]:
    config = get_country_config(source_country)
    return [
        {
            "source_country": config.code,
            "recipient_country": partner["iso2"],
            "recipient_country_name": partner["country"],
            "parsed_file": partner["parsed_file"],
            "income_type": income_type,
        }
        for partner in load_partner_registry(
            path,
            source_country=config.code,
        )
        for income_type in config.supported_income_types
    ]


def supported_scope_keys(
    path: str | Path | None = None,
    *,
    source_country: str = "CZ",
) -> set[tuple[str, str, str]]:
    return {
        (
            scope["source_country"],
            scope["recipient_country"],
            scope["income_type"],
        )
        for scope in expected_legal_scopes(
            path,
            source_country=source_country,
        )
    }
