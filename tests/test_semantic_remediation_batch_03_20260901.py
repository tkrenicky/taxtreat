import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "legal_rule_candidates" / "semantic_remediation_20260901"
QUEUE = ROOT / "data" / "legal_reviews" / "global_cz_outbound" / "cz_country_qa_queue.json"
BATCH = ("ES", "FR", "GB", "GE", "HU")


def test_semantic_remediation_batch_03_is_hash_bound_and_fail_closed():
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    hashes = {
        str(row["partner_country"]).upper(): str(row["package_sha256"])
        for row in queue["packages"]
    }

    for country in BATCH:
        payload = json.loads(
            (CANDIDATES / f"{country.lower()}.json").read_text(encoding="utf-8")
        )
        production = payload["stage6_production"]

        assert production["package_sha256"] == hashes[country]
        assert production["production_approval"] == "not_approved"
        assert production["rule_promotion"] == "not_promoted"
        assert production["source_release"] == "not_released"
        assert production["additional_human_review_claimed"] is False
        assert (
            production["verification_authority"]
            == "semantic_remediation_machine_projection"
        )

        remediated = [
            rule
            for rule in payload["rules"]
            if rule.get("review_package_sha256") == hashes[country]
            and rule.get("verification_authority")
            == "semantic_remediation_machine_projection"
        ]
        assert remediated, country
        assert all(rule["verification_status"] == "needs_review" for rule in remediated)
        assert all(rule.get("approval_dataset_release") is None for rule in remediated)
        assert all(rule.get("approval_created_at") is None for rule in remediated)
