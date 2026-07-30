from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path("data/cz_treaty_partners.json")


def load_registry():
    with REGISTRY.open(encoding="utf-8") as f:
        return json.load(f)


def generate_scope():
    rows = []

    for country in load_registry():
        for income in (
            "dividend",
            "interest",
            "royalty",
        ):
            rows.append(
                {
                    "payer": "CZ",
                    "recipient": country["iso2"],
                    "country": country["country"],
                    "income_type": income,
                }
            )

    return rows


if __name__ == "__main__":
    print(len(generate_scope()))
