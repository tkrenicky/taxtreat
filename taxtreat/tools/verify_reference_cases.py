from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "reference_cases"

passed = 0
failed = 0

print("=" * 70)
print("TaxTreat Reference Case Verification")
print("=" * 70)

for file in sorted(REFERENCE_DIR.rglob("*.yaml")):
    data = yaml.safe_load(file.read_text(encoding="utf-8"))

    required = [
        "id",
        "payer_country",
        "recipient_country",
        "income_type",
        "facts",
        "expected",
    ]

    missing = [x for x in required if x not in data]

    if missing:
        print(f"❌ {file.name}")
        print(f"   Missing fields: {', '.join(missing)}")
        failed += 1
        continue

    print(f"✅ {data['id']}")
    passed += 1

print()
print("=" * 70)
print(f"Passed : {passed}")
print(f"Failed : {failed}")
print("=" * 70)

sys.exit(1 if failed else 0)
