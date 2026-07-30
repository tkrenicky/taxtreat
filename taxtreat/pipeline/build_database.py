from __future__ import annotations

import csv
import json
from pathlib import Path

SOURCE_DIR = Path("data/parsed")
OUTPUT_DIR = Path("data/generated")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_records():
    records = []

    for file in sorted(SOURCE_DIR.glob("*.json")):
        with open(file, encoding="utf-8") as f:
            records.append(json.load(f))

    return records


def export_csv(records):
    fields = [
        "payer",
        "recipient",
        "income_type",
        "treaty_rate",
        "domestic_rate",
        "effective_rate",
        "beneficial_owner",
        "minimum_ownership",
        "holding_period_months",
        "confidence",
        "manual_review",
        "treaty_article",
        "treaty_source",
        "domestic_source",
    ]

    with open(
        OUTPUT_DIR / "taxtreat_master.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for r in records:
            writer.writerow({
                k: r.get(k)
                for k in fields
            })


def export_json(records):
    with open(
        OUTPUT_DIR / "taxtreat_master.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def main():
    records = load_records()

    export_csv(records)
    export_json(records)

    print(f"{len(records)} records exported.")


if __name__ == "__main__":
    main()
