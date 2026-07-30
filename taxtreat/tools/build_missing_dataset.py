from pathlib import Path
import csv
import yaml

ROOT = Path("knowledge_base/countries")
SCOPE_FILE = Path("knowledge_base/scope/phase_1_oecd.yaml")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

scope = yaml.safe_load(SCOPE_FILE.read_text(encoding="utf-8"))
income_types = tuple(scope["income_types"])
rows = []

for payer in scope["payer_countries"]:
    payer_dir = ROOT / payer

    available = set()

    if payer_dir.exists():
        for file in payer_dir.glob("*.yaml"):
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
            available.add(
                (
                    data.get("recipient_country"),
                    data.get("income_type"),
                )
            )

    for recipient in scope["recipient_countries"]:
        for income_type in income_types:
            key = (recipient, income_type)

            if key not in available:
                rows.append(
                    {
                        "payer": payer,
                        "recipient": recipient,
                        "income_type": income_type,
                        "priority": "HIGH",
                        "status": "MISSING",
                        "scope": scope["scope_id"],
                    }
                )

outfile = REPORTS / "missing_dataset.csv"

with outfile.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "payer",
            "recipient",
            "income_type",
            "priority",
            "status",
            "scope",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

expected = scope["expected_records"]
completed = expected - len(rows)

print(f"Scope: {scope['name']}")
print(f"Expected records: {expected}")
print(f"Completed records: {completed}")
print(f"Missing records: {len(rows)}")
print(f"Saved to {outfile}")
