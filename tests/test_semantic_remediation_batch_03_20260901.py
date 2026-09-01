import json
from pathlib import Path

BATCH = ("ES", "FR", "GB", "GE", "HU")

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "legal_consolidation" / "cz_country_qa_queue.json"
CANDIDATE_DIR = (
    ROOT / "data" / "legal_rule_candidates" / "semantic_remediation_20260901"
)


def test_semantic_remediation_batch_03_is_hash_bound_and_fail_closed() -> None:
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    queue_by_country = {
        item["country_code"]: item
        for item in queue
        if item["country_code"] in BATCH
    }

    assert set(queue_by_country) == set(BATCH)

    for country_code in BATCH:
        candidate_path = CANDIDATE_DIR / f"{country_code.lower()}.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        production = candidate["stage6_production"]
        expected_hash = queue_by_country[country_code]["package_sha256"]

        assert production["package_sha256"] == expected_hash
        assert production["production_approval"] == "not_approved"
        assert production["rule_promotion"] == "not_promoted"
        assert production["source_release"] == "not_released"
        assert production["additional_human_review_claimed"] is False
        assert (
            production["verification_authority"]
            == "semantic_remediation_machine_projection"
        )

        remediated_rules = [
            rule
            for rule in candidate["rules"]
            if rule.get("package_sha256") == expected_hash
            and rule.get("verification_authority")
            == "semantic_remediation_machine_projection"
        ]
        assert remediated_rules
        assert all(
            rule.get("verification_status") == "needs_review"
            for rule in remediated_rules
        )
        assert all(
            rule.get("approval_dataset_release") is None
            for rule in remediated_rules
        )
        assert all(
            rule.get("approval_created_at") is None
            for rule in remediated_rules
        )
