from pathlib import Path
import csv
import re
import yaml

ROOT = Path("knowledge_base/countries")
SCOPE_FILE = Path("knowledge_base/scope/phase_1_oecd.yaml")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

scope = yaml.safe_load(SCOPE_FILE.read_text())

ISO = re.compile(r"^[A-Z]{2}$")

income_types = tuple(scope["income_types"])
rows = []

for payer in scope["payer_countries"]:
    payer_dir = ROOT / payer
    available = set()

    if payer_dir.exists():
        for file in payer_dir.glob("*.yaml"):
            data = yaml.safe_load(file.read_text())

            recipient = data.get("recipient_country")

            if not isinstance(recipient, str):
                continue

            recipient = recipient.strip().upper()

            if not ISO.fullmatch(recipient):
                continue

            available.add((recipient, data.get("income_type")))

    for recipient in scope["recipient_countries"]:
        for income_type in income_types:
            if (recipient, income_type) not in available:
                rows.append({
                    "payer": payer,
                    "recipient": recipient,
                    "income_type": income_type,
                    "priority": "HIGH",
                    "status": "MISSING",
                    "scope": scope["scope_id"],
                })

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

print(f"Missing records: {len(rows)}")
