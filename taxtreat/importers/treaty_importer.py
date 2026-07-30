from pathlib import Path
import json
import yaml

INPUT_DIR = Path("imports")
OUTPUT_DIR = Path("knowledge_base/countries")


def convert(record: dict) -> dict:
    return {
        "id": f"{record['payer']}-{record['recipient']}-{record['income_code']}",
        "payer_country": record["payer"],
        "recipient_country": record["recipient"],
        "income_type": record["income_type"],
        "domestic_law": {
            "standard_rate": record["domestic_rate"],
            "legal_reference": record.get("domestic_reference"),
            "notes": None,
        },
        "treaty": {
            "applicable": record["treaty_applicable"],
            "article": record.get("article"),
            "paragraph": record.get("paragraph"),
            "standard_rate": record.get("treaty_rate"),
            "beneficial_owner_required": record.get("beneficial_owner"),
            "reduced_rates": record.get("reduced_rates", []),
            "notes": None,
        },
        "protocol": record.get(
            "protocol",
            {
                "applicable": False,
                "effective_date": None,
                "reference": None,
                "notes": None,
            },
        ),
        "eu_directive": record.get(
            "eu_directive",
            {
                "applicable": False,
                "directive": None,
                "minimum_ownership_percent": None,
                "minimum_holding_months": None,
                "conditions": [],
            },
        ),
        "documentation": record.get("documentation", []),
        "sources": record.get("sources", []),
        "status": record.get("status", "draft"),
    }


def main():
    files = sorted(INPUT_DIR.glob("*.json"))

    created = 0

    for file in files:
        records = json.loads(file.read_text(encoding="utf-8"))

        for record in records:
            kb = convert(record)

            folder = OUTPUT_DIR / kb["payer_country"]
            folder.mkdir(parents=True, exist_ok=True)

            out = folder / f"{kb['recipient_country']}-{kb['income_type']}.yaml"

            out.write_text(
                yaml.safe_dump(
                    kb,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )

            created += 1

    print(f"Imported {created} treaty records.")


if __name__ == "__main__":
    main()
