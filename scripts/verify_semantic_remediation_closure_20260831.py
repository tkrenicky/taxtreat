from __future__ import annotations

import json
from pathlib import Path

from taxtreat.engine.legal_rule_engine import _PENDING_SEMANTIC_REMEDIATION_SCOPES

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
REGISTRY = ROOT / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json"
QUEUE = BASE / "cz_country_qa_queue.json"
APPROVAL = BASE / "stage6_production_approval.json"
GATE = BASE / "production_source_release_gate_v2.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm_condition(row):
    return (
        str(row.get("condition_type")),
        str(row.get("operator")),
        None if row.get("unit") is None else str(row.get("unit")),
        str(row.get("value")),
    )


def norm_branch(row):
    return (
        float(row["rate"]),
        tuple(sorted(norm_condition(c) for c in row.get("conditions", []))),
    )


def main() -> int:
    registry = load(REGISTRY)
    queue = load(QUEUE)
    approval = load(APPROVAL)
    gate = load(GATE)

    corrections = {
        (str(row["country"]).upper(), str(row["income_type"])): row
        for row in registry["corrections"]
    }
    assert len(corrections) == 40
    assert set(corrections) == set(_PENDING_SEMANTIC_REMEDIATION_SCOPES)

    queue_by_country = {row["partner_country"]: row for row in queue["packages"]}
    approval_hash = {row["partner_country"]: row["package_sha256"] for row in approval["records"]}
    gate_by_country = {row["partner_country"]: row for row in gate["treaty_partners"]}

    changed_hashes = set()
    for (country, income_type), correction in sorted(corrections.items()):
        package = queue_by_country[country]
        scope = next(row for row in package["income_scopes"] if row["income_type"] == income_type)
        actual = tuple(sorted(norm_branch(row) for row in scope["material_conditions"]))
        expected = tuple(sorted(norm_branch(row) for row in correction["rate_candidates"]))
        assert actual == expected, f"{country}:{income_type}: corrected branches do not match registry"

        status = scope["candidate_status"]
        remediation = status.get("semantic_remediation") or {}
        assert status["verification_status"] == "needs_review"
        assert status["fail_closed"] is True
        assert status["production_releasable"] is False
        assert remediation.get("status") == "needs_human_review"
        assert remediation.get("automatic_production_approval_forbidden") is True
        assert remediation.get("evidence_source_id") == correction.get("evidence_source_id")

        current_hash = package["package_sha256"]
        assert current_hash != approval_hash[country], f"{country}: stale approval unexpectedly matches new hash"
        changed_hashes.add(country)

        gate_row = gate_by_country[country]
        assert gate_row["package_sha256"] == current_hash
        assert gate_row["human_review_status"] == "needs_review"
        assert gate_row["production_approval_eligible"] is False
        assert gate_row["production_approval_status"] == "not_approved"
        assert gate_row["rule_promotion_status"] == "not_promoted"
        assert gate_row["release_status"] == "not_released"
        assert gate_row["active_rule_allowed"] is False
        assert gate_row["production_ready"] is False
        assert gate_row["fail_closed"] is True
        assert gate_row["release_blockers"] == [
            "semantic_remediation_requires_hash_bound_human_review"
        ]

    all_countries = set(queue_by_country)
    unchanged = all_countries - changed_hashes
    assert len(changed_hashes) == 40
    assert len(unchanged) == 61

    for country in unchanged:
        assert queue_by_country[country]["package_sha256"] == approval_hash[country]
        row = gate_by_country[country]
        assert row["release_status"] == "released"
        assert row["production_approval_status"] == "production_approved"
        assert row["active_rule_allowed"] is True
        assert row["fail_closed"] is False

    counts = gate["counts"]
    assert counts["released_packages"] == 61
    assert counts["released_scopes"] == 183
    assert counts["semantic_remediation_pending_packages"] == 40
    assert counts["semantic_remediation_pending_scopes"] == 40

    print("CZ semantic remediation closure verifier: PASS")
    print("remediation_scopes=40")
    print("rehash_packages=40")
    print("unchanged_released_packages=61")
    print("automatic_approval_forbidden=true")
    print("remaining_blocker=hash_bound_human_review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
