import json
from pathlib import Path

from taxtreat.engine.legal_rule_engine import _PENDING_SEMANTIC_REMEDIATION_SCOPES

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "legal_consolidation" / "semantic_remediation_condition_candidates_20260829.json"
QUEUE = ROOT / "data" / "legal_reviews" / "global_cz_outbound" / "cz_country_qa_queue.json"
RULES = ROOT / "data" / "legal_rules_stage6"

MACHINE_AUTHORITY = "semantic_remediation_machine_validation"
MACHINE_APPROVAL = "stage6-semantic-remediation-machine-validation-2026-09-01.1"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _norm_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if text.lower() in {"true", "false"}:
        return text.lower()
    return text


def _norm_registry_condition(row):
    return (
        str(row["condition_type"]),
        str(row["operator"]).replace("not_in", "not in"),
        _norm_value(row.get("value")),
    )


def _norm_runtime_condition(row):
    return (
        str(row["fact"]),
        str(row["operator"]),
        _norm_value(row.get("value")),
    )


def test_all_semantic_remediation_scopes_are_machine_validated_and_unquarantined():
    registry = _load(REGISTRY)
    queue = _load(QUEUE)
    queue_hashes = {
        str(row["partner_country"]).upper(): str(row["package_sha256"])
        for row in queue["packages"]
    }

    corrections = {
        (str(row["country"]).upper(), str(row["income_type"])): row
        for row in registry["corrections"]
    }
    assert len(corrections) == 40
    assert _PENDING_SEMANTIC_REMEDIATION_SCOPES == set()

    for (country, income_type), correction in sorted(corrections.items()):
        payload = _load(RULES / f"{country.lower()}.json")
        expected_hash = queue_hashes[country]

        source_id = str(correction["evidence_source_id"])
        runtime_rules = [
            rule
            for rule in payload["rules"]
            if str(rule.get("income_type")) == income_type
            and str(rule.get("source_id")) == source_id
            and str(rule.get("legal_layer")) in {"treaty", "protocol"}
            and str(rule.get("effect") or "rate") == "rate"
            and rule.get("rate") is not None
        ]
        assert runtime_rules, (country, income_type)

        by_rate = {}
        for rule in runtime_rules:
            by_rate.setdefault(float(rule["rate"]), []).append(rule)

        for branch in correction["rate_candidates"]:
            rate = float(branch["rate"])
            matches = by_rate.get(rate, [])
            assert len(matches) == 1, (country, income_type, rate)
            rule = matches[0]

            assert rule["review_package_sha256"] == expected_hash
            assert rule["verification_status"] == "verified"
            assert rule["verification_authority"] == MACHINE_AUTHORITY
            assert rule["approval_dataset_release"] == MACHINE_APPROVAL
            assert rule["approval_created_at"] == "2026-09-01"

            actual = {
                _norm_runtime_condition(row)
                for row in rule.get("conditions", [])
                if str(row.get("fact")) in {
                    str(x["condition_type"]) for x in branch.get("conditions", [])
                }
            }
            expected = {
                _norm_registry_condition(row)
                for row in branch.get("conditions", [])
            }
            assert actual == expected, (country, income_type, rate, actual, expected)
