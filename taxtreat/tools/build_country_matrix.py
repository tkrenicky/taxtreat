from pathlib import Path
import csv
import yaml

ROOT = Path("knowledge_base/countries")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

rows = []

for payer_dir in sorted(ROOT.iterdir()):
    if not payer_dir.is_dir():
        continue

    payer = payer_dir.name

    countries = {}

    for f in payer_dir.glob("*.yaml"):
        data = yaml.safe_load(f.read_text())

        recipient = data["recipient_country"]
        countries.setdefault(
            recipient,
            {"dividends": False, "interest": False, "royalties": False},
        )

        countries[recipient][data["income_type"]] = True

    for recipient, values in sorted(countries.items()):
        completeness = sum(values.values())

        rows.append({
            "payer": payer,
            "recipient": recipient,
            "dividends": values["dividends"],
            "interest": values["interest"],
            "royalties": values["royalties"],
            "coverage_percent": round(completeness / 3 * 100),
        })

outfile = REPORTS / "country_matrix.csv"

with outfile.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "payer",
            "recipient",
            "dividends",
            "interest",
            "royalties",
            "coverage_percent",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {outfile}")
