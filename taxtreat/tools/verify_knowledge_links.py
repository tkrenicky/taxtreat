from pathlib import Path
import yaml

ROOT = Path("knowledge_base/countries")

errors = 0
checked = 0

for file in sorted(ROOT.rglob("*.yaml")):
    checked += 1
    data = yaml.safe_load(file.read_text())

    if data["status"] != "verified":
        continue

    treaty = data["treaty"]

    if treaty.get("applicable") and treaty.get("article") is None:
        print(f"{file}: missing treaty article")
        errors += 1

    if treaty.get("applicable") and treaty.get("paragraph") is None:
        print(f"{file}: missing treaty paragraph")
        errors += 1

    if treaty.get("applicable") and treaty.get("standard_rate") is None and not treaty.get("reduced_rates"):
        print(f"{file}: no treaty rate defined")
        errors += 1

    if not data.get("sources"):
        print(f"{file}: verified record without official sources")
        errors += 1

print()
print(f"Checked : {checked}")
print(f"Errors  : {errors}")

raise SystemExit(1 if errors else 0)
