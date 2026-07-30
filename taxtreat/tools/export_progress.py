from pathlib import Path
import csv
import yaml

ROOT = Path("knowledge_base/countries")
OUT = Path("reports")
OUT.mkdir(exist_ok=True)

rows = []

for file in sorted(ROOT.rglob("*.yaml")):
    data = yaml.safe_load(file.read_text())

    treaty = data.get("treaty", {})
    protocol = data.get("protocol", {})
    directive = data.get("eu_directive", {})

    rows.append({
        "payer": data.get("payer_country"),
        "recipient": data.get("recipient_country"),
        "income_type": data.get("income_type"),
        "status": data.get("status"),
        "article": treaty.get("article"),
        "paragraph": treaty.get("paragraph"),
        "treaty_rate": treaty.get("standard_rate"),
        "reduced_rates": len(treaty.get("reduced_rates", [])),
        "protocol": protocol.get("applicable"),
        "eu_directive": directive.get("applicable"),
        "sources": len(data.get("sources", [])),
        "documentation": len(data.get("documentation", [])),
    })

outfile = OUT / "knowledge_base_progress.csv"

with outfile.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Exported {len(rows)} records to {outfile}")
