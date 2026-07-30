from pathlib import Path
import csv
import yaml

ROOT = Path("knowledge_base/countries")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

EXPECTED = ("dividends", "interest", "royalties")
rows = []

for payer_dir in sorted(ROOT.iterdir()):
    if not payer_dir.is_dir():
        continue

    payer = payer_dir.name

    recipients = {}

    for file in payer_dir.glob("*.yaml"):
        data = yaml.safe_load(file.read_text())
        recipients.setdefault(data["recipient_country"], set()).add(data["income_type"])

    for recipient, available in sorted(recipients.items()):
        for income_type in EXPECTED:
            if income_type not in available:
                rows.append({
                    "payer": payer,
                    "recipient": recipient,
                    "income_type": income_type,
                    "priority": "HIGH",
                    "status": "MISSING",
                })

outfile = REPORTS / "missing_dataset.csv"

with outfile.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["payer", "recipient", "income_type", "priority", "status"],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Missing records: {len(rows)}")
print(f"Saved to {outfile}")
