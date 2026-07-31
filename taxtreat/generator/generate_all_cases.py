from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DB = Path("data/processed/taxtreat_cz.sqlite")
OUTPUT = Path("data/generated/cz_all_cases.csv")

INCOME_TYPES = (
    "dividend",
    "interest",
    "royalty",
)


def load_partners(db_path: Path = DB) -> list[str]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT country_cs
            FROM country_documents
            WHERE relation = 'treaty'
              AND country_cs IS NOT NULL
              AND TRIM(country_cs) <> ''
            ORDER BY country_cs
            """
        ).fetchall()

    return [row[0] for row in rows]


def generate(db_path: Path = DB) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for country_cs in load_partners(db_path):
        for income_type in INCOME_TYPES:
            rows.append(
                {
                    "payer": "CZ",
                    "recipient_country_cs": country_cs,
                    "recipient_iso2": "",
                    "income_type": income_type,
                    "status": "PENDING",
                    "confidence": 0,
                    "manual_review": True,
                }
            )

    return rows


def write_csv(rows: list[dict[str, object]], output: Path = OUTPUT) -> None:
    if not rows:
        raise RuntimeError("No Czech treaty cases were generated.")

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = generate()
    write_csv(rows)

    partners = len({row["recipient_country_cs"] for row in rows})

    print(f"Treaty partners: {partners}")
    print(f"Production cases: {len(rows)}")
    print(f"Saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
