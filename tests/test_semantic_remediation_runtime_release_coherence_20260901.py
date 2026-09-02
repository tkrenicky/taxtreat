import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "legal_consolidation" / "semantic_remediation_condition_candidates_20260829.json"
RULES = ROOT / "data" / "legal_rules_stage6"
PRODUCTION_RELEASE = "stage6-semantic-remediation-production-2026-09-01.1"


def test_remediated_runtime_packages_use_one_production_release():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    countries = sorted({str(row["country"]).upper() for row in registry["corrections"]})
    assert len(countries) == 41

    for country in countries:
        payload = json.loads((RULES / f"{country.lower()}.json").read_text(encoding="utf-8"))
        releases = {
            str(rule.get("dataset_release"))
            for rule in payload.get("rules", [])
            if rule.get("dataset_release")
        }
        assert releases == {PRODUCTION_RELEASE}, (country, sorted(releases))
