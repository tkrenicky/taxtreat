from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from taxtreat.engine.legal_rule_engine import (  # noqa: E402
    _PENDING_SEMANTIC_REMEDIATION_SCOPES,
)

BASE = ROOT / "data/legal_reviews/global_cz_outbound"
REGISTRY = ROOT / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json"
QUEUE = BASE / "cz_country_qa_queue.json"
RELEASE = BASE / "semantic_remediation_machine_release_20260901.json"
GATE = BASE / "production_source_release_gate_v2.json"
CANDIDATES = ROOT / "data/legal_rule_candidates/semantic_remediation_20260901"
RUNTIME = ROOT / "data/legal_rules_stage6"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm_condition(row):
    return (
        str(row.get("fact")),
        str(row.get("fact_source") or "transaction"),
        str(row.get("operator")),
        str(row.get("value")),
    )


def norm_rule(row):
    return (
        str(row.get("source_id")),
        str(row.get("income_type")),
        float(row["rate"]) if row.get("rate") is not None else None,
        tuple(sorted(norm_condition(c) for c in row.get("conditions", []))),
    )


def main() -> int:
    registry = load(REGISTRY)
    queue = load(QUEUE)
    release = load(RELEASE)
    gate = load(GATE)

    expected = {
        (str(row["country"]).upper(), str(row["income_type"]))
        for row in registry["corrections"]
    }
    assert len(expected) == 40
    assert _PENDING_SEMANTIC_REMEDIATION_SCOPES == set()

    queue_hash = {
        str(row["partner_country"]).upper(): str(row["package_sha256"])
        for row in queue["packages"]
    }
    release_by_scope = {
        (str(row["partner_country"]).upper(), str(row["income_type"])): row
        for row in release["records"]
    }
    assert set(release_by_scope) == expected
    assert release["additional_human_review_claimed"] is False
    assert release["counts"]["released_scopes"] == 40
    assert release["counts"]["released_packages"] == 40

    gate_by_pair = {
        str(row["treaty_pair_id"]): row
        for row in gate["treaty_partners"]
    }
    assert gate["counts"]["released_packages"] == 101
    assert gate["counts"]["released_scopes"] == 303
    assert gate["counts"]["semantic_remediation_pending_packages"] == 0
    assert gate["counts"]["semantic_remediation_pending_scopes"] == 0

    for country, income in sorted(expected):
        release_row = release_by_scope[(country, income)]
        current_hash = queue_hash[country]
        assert release_row["package_sha256"] == current_hash
        assert release_row["release_status"] == "released_after_machine_validation"

        gate_row = gate_by_pair[f"CZ-{country}"]
        assert gate_row["package_sha256"] == current_hash
        assert gate_row["production_approval_status"] == "production_approved"
        assert gate_row["rule_promotion_status"] == "promoted"
        assert gate_row["release_status"] == "released"
        assert gate_row["active_rule_allowed"] is True
        assert gate_row["production_ready"] is True
        assert gate_row["fail_closed"] is False
        assert gate_row["release_blockers"] == []
        machine_event = gate_row["release_evidence"]["semantic_remediation_machine_release"]
        assert machine_event["package_sha256"] == current_hash
        assert machine_event["additional_human_review_claimed"] is False
        assert machine_event["release_status"] == "released_after_machine_validation"

        candidate = load(CANDIDATES / f"{country.lower()}.json")
        runtime = load(RUNTIME / f"{country.lower()}.json")

        c_rules = [
            row for row in candidate["rules"]
            if row.get("income_type") == income
            and row.get("verification_authority")
            == "semantic_remediation_machine_projection"
            and row.get("review_package_sha256") == current_hash
        ]
        r_rules = [
            row for row in runtime["rules"]
            if row.get("income_type") == income
            and row.get("verification_authority")
            == "semantic_remediation_machine_validation"
            and row.get("review_package_sha256") == current_hash
        ]

        assert c_rules, (country, income, "candidate")
        assert r_rules, (country, income, "runtime")
        assert {norm_rule(row) for row in r_rules} == {norm_rule(row) for row in c_rules}
        assert all(row.get("verification_status") == "verified" for row in r_rules)
        assert all(
            row.get("approval_dataset_release")
            == "stage6-semantic-remediation-machine-validation-2026-09-01.1"
            for row in r_rules
        )

    print("CZ semantic remediation machine release verifier: PASS")
    print("released_scopes=40")
    print("released_packages=40")
    print("additional_human_review_claimed=false")
    print("pending_quarantine_scopes=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
