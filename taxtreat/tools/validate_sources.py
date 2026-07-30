from pathlib import Path
import yaml

ROOT = Path("knowledge_base/countries")

failed = 0
checked = 0

for file in sorted(ROOT.rglob("*.yaml")):
    checked += 1

    data = yaml.safe_load(file.read_text(encoding="utf-8"))

    sources = data.get("sources", [])

    if data["status"] == "verified" and len(sources) < 2:
        print(f"FAIL {file}: verified record must contain at least 2 official sources")
        failed += 1
        continue

    for source in sources:
        for field in ("title", "authority", "url", "source_type"):
            if field not in source:
                print(f"FAIL {file}: missing '{field}'")
                failed += 1
                break

print()
print(f"Checked: {checked}")
print(f"Failed : {failed}")

raise SystemExit(1 if failed else 0)
