from pathlib import Path
import yaml

ROOT = Path("knowledge_base/countries")

score = 0
maximum = 0

weights = {
    "domestic_law": 10,
    "treaty": 25,
    "protocol": 10,
    "eu_directive": 10,
    "documentation": 10,
    "sources": 20,
    "reference": 5,
    "verified": 10,
}

for file in sorted(ROOT.rglob("*.yaml")):
    data = yaml.safe_load(file.read_text())

    file_score = 0
    maximum += sum(weights.values())

    if data.get("domestic_law", {}).get("standard_rate") is not None:
        file_score += weights["domestic_law"]

    treaty = data.get("treaty", {})
    if treaty.get("applicable") is not None:
        file_score += 5
    if treaty.get("article") is not None:
        file_score += 5
    if treaty.get("paragraph") is not None:
        file_score += 5
    if treaty.get("standard_rate") is not None or treaty.get("reduced_rates"):
        file_score += 10

    protocol = data.get("protocol", {})
    if protocol.get("applicable") is not None:
        file_score += weights["protocol"]

    directive = data.get("eu_directive", {})
    if directive.get("applicable") is not None:
        file_score += weights["eu_directive"]

    if data.get("documentation") and data["documentation"] != ["TO_BE_COMPLETED"]:
        file_score += weights["documentation"]

    if data.get("sources"):
        file_score += weights["sources"]

    ref = Path("knowledge_base/reference_cases") / data["income_type"] / f"{data['id']}-001.yaml"
    if ref.exists():
        file_score += weights["reference"]

    if data.get("status") == "verified":
        file_score += weights["verified"]

    score += file_score

overall = score / maximum * 100 if maximum else 0

print("=" * 60)
print("KNOWLEDGE BASE QUALITY")
print("=" * 60)
print(f"Overall quality: {overall:.1f}%")
print(f"Score: {score}/{maximum}")
