from pathlib import Path
import yaml

ROOT = Path("knowledge_base/countries")

stats = {}

for file in ROOT.rglob("*.yaml"):
    data = yaml.safe_load(file.read_text())

    income = data["income_type"]
    status = data["status"]

    stats.setdefault(income, {"draft": 0, "reviewed": 0, "verified": 0})

    stats[income][status] += 1

print("=" * 60)
print("TAXTREAT KNOWLEDGE BASE DASHBOARD")
print("=" * 60)

total = 0
verified = 0

for income, values in sorted(stats.items()):
    s = sum(values.values())
    total += s
    verified += values["verified"]

    print(f"\n{income.upper()}")
    print(f"  Draft     : {values['draft']}")
    print(f"  Reviewed  : {values['reviewed']}")
    print(f"  Verified  : {values['verified']}")
    print(f"  Total     : {s}")

print("\n" + "=" * 60)
print(f"TOTAL RECORDS : {total}")
print(f"VERIFIED      : {verified}")
print(f"PROGRESS      : {verified/total*100 if total else 0:.1f}%")
