from pathlib import Path

ROOT = Path("knowledge_base/countries/CZ")

TARGETS = [
    "AT","AU","BE","BG","BR","CA","CH","CN","CY","DE","DK","EE","ES","FI",
    "FR","GB","GR","HK","HR","HU","IE","IL","IN","IS","IT","JP","KR","LT",
    "LU","LV","MX","MY","NL","NO","NZ","PL","PT","RO","SE","SG","SI","SK",
    "TH","TR","TW","UA","US","VN","ZA"
]

existing = {
    p.stem.split("-")[0] + "-" + p.stem.split("-")[1]
    for p in ROOT.glob("*.yaml")
}

missing = []

for country in TARGETS:
    pair = f"CZ-{country}"
    if pair not in existing:
        missing.append(pair)

print("=" * 50)
print("Missing country pairs")
print("=" * 50)

for pair in missing:
    print(pair)

print()
print(f"Completed : {len(existing)}")
print(f"Missing   : {len(missing)}")
print(f"Progress  : {len(existing)/(len(existing)+len(missing))*100:.1f}%")
