from pathlib import Path
import csv
import yaml

INPUT = Path("imports")
OUTPUT = Path("knowledge_base/countries")


def parse_bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "y")


def parse_float(value):
    if value in ("", None):
        return None
    return float(value)


created = 0

for csv_file in INPUT.glob("*.csv"):
    with csv_file.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            record = {
                "id": f"{row['payer']}-{row['recipient']}-{row['income_code']}",
                "payer_country": row["payer"],
                "recipient_country": row["recipient"],
                "income_type": row["income_type"],
                "domestic_law": {
                    "standard_rate": parse_float(row["domestic_rate"]),
                    "legal_reference": row["domestic_reference"],
                    "notes": None,
                },
                "treaty": {
                    "applicable": parse_bool(row["treaty_applicable"]),
                    "article": int(row["article"]) if row["article"] else None,
                    "paragraph": row["paragraph"] or None,
                    "standard_rate": parse_float(row["treaty_rate"]),
                    "beneficial_owner_required": parse_bool(row["beneficial_owner"]),
                    "reduced_rates": [],
                    "notes": None,
                },
                "protocol": {
                    "applicable": False,
                    "effective_date": None,
                    "reference": None,
                    "notes": None,
                },
                "eu_directive": {
                    "applicable": False,
                    "directive": None,
                    "minimum_ownership_percent": None,
                    "minimum_holding_months": None,
                    "conditions": [],
                },
                "documentation": [],
                "sources": [],
                "status": "draft",
            }

            outdir = OUTPUT / row["payer"]
            outdir.mkdir(parents=True, exist_ok=True)

            outfile = outdir / f"{row['recipient']}-{row['income_type']}.yaml"

            outfile.write_text(
                yaml.safe_dump(
                    record,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )

            created += 1

print(f"Imported {created} records from CSV.")
