from __future__ import annotations

import json
from pathlib import Path

from scripts.project_stage6_semantic_remediation_20260901 import (
    project_country,
)


ROOT = Path(__file__).resolve().parents[1]
AD_RULES = ROOT / "data/legal_rules_stage6/ad.json"


def _conditions(rule):
    return {
        (row["fact"], row["operator"], str(row["value"]))
        for row in rule["conditions"]
    }


def test_ad_semantic_remediation_projection(tmp_path, monkeypatch):
    import scripts.project_stage6_semantic_remediation_20260901 as projector

    target = tmp_path / "legal_rules_stage6"
    target.mkdir()
    (target / "ad.json").write_text(
        AD_RULES.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(projector, "RULES_DIR", target)

    result = project_country("AD")
    assert result["package_sha256"] == (
        "6a2fecb997238bfcd6eb6eeee0e03d6add49c15b4485740cec50868de61aef1a"
    )
    assert len(result["changed_rule_ids"]) == 2

    payload = json.loads((target / "ad.json").read_text(encoding="utf-8"))
    five = next(
        row for row in payload["rules"]
        if row["rule_id"] == "CZ-AD-DIVIDEND-CURRENT-1"
    )
    fallback = next(
        row for row in payload["rules"]
        if row["rule_id"] == "CZ-AD-DIVIDEND-CURRENT-2"
    )

    assert _conditions(five) == {
        ("recipient_entity_type", "==", "company_other_than_partnership"),
        ("direct_ownership", "==", "true"),
        ("ownership_percent", ">=", "10"),
        ("beneficial_owner", "==", "true"),
    }
    assert _conditions(fallback) == {
        ("fallback_case", "==", "all_other_cases"),
        ("beneficial_owner", "==", "true"),
    }

    for rule in (five, fallback):
        assert rule["review_package_sha256"] == result["package_sha256"]
        assert rule["verification_status"] == "needs_review"
        assert rule["verification_authority"] == "semantic_remediation_machine_projection"
        assert rule["approval_dataset_release"] is None
        assert rule["approval_created_at"] is None


def test_all_semantic_remediation_packages_project_without_rate_ambiguity(
    tmp_path, monkeypatch
):
    import scripts.project_stage6_semantic_remediation_20260901 as projector

    registry = json.loads(projector.REGISTRY.read_text(encoding="utf-8"))
    countries = sorted({str(row["country"]).upper() for row in registry["corrections"]})
    assert len(countries) == 41

    target = tmp_path / "legal_rules_stage6"
    target.mkdir()
    for country in countries:
        source = ROOT / "data/legal_rules_stage6" / f"{country.lower()}.json"
        (target / f"{country.lower()}.json").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    monkeypatch.setattr(projector, "RULES_DIR", target)

    results = [project_country(country) for country in countries]
    assert len(results) == 41
    assert sum(item["correction_count"] for item in results) == 41
    assert all(item["changed_rule_ids"] for item in results)

    for result in results:
        payload = json.loads(
            (target / f"{result['country'].lower()}.json").read_text(
                encoding="utf-8"
            )
        )
        changed = {
            row["rule_id"]: row
            for row in payload["rules"]
            if row.get("rule_id") in set(result["changed_rule_ids"])
        }
        assert len(changed) == len(result["changed_rule_ids"])
        for rule in changed.values():
            assert rule["review_package_sha256"] == result["package_sha256"]
            assert rule["verification_status"] == "needs_review"
            assert (
                rule["verification_authority"]
                == "semantic_remediation_machine_projection"
            )
