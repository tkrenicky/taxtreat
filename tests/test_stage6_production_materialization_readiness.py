from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

AUDIT = (
    BASE
    / "stage6_production_materialization_readiness.json"
)

APPROVAL = (
    BASE
    / "stage6_production_approval.json"
)

GATE = (
    BASE
    / "production_source_release_gate_v2.json"
)


def load(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_materialization_audit_covers_exact_universe():
    audit = load(AUDIT)

    assert audit["counts"]["packages"] == 101
    assert audit["counts"]["scopes"] == 303

    assert len(audit["records"]) == 101
    assert sum(
        row["scope_count"]
        for row in audit["records"]
    ) == 303


def test_materialization_audit_is_hash_bound():
    audit = load(AUDIT)
    approval = load(APPROVAL)
    gate = load(GATE)

    audit_hashes = {
        row["treaty_pair_id"]:
            row["package_sha256"]
        for row in audit["records"]
    }

    approval_hashes = {
        row["treaty_pair_id"]:
            row["package_sha256"]
        for row in approval["records"]
    }

    gate_hashes = {
        row["treaty_pair_id"]:
            row["package_sha256"]
        for row in gate["treaty_partners"]
    }

    assert (
        audit_hashes
        == approval_hashes
        == gate_hashes
    )


def test_readiness_audit_does_not_promote_or_release():
    audit = load(AUDIT)
    gate = load(GATE)

    assert audit["semantics"][
        "this_is_rule_promotion"
    ] is False

    assert audit["semantics"][
        "this_is_source_release"
    ] is False

    assert audit["semantics"][
        "this_opens_runtime"
    ] is False

    assert audit["counts"][
        "rule_promoted_packages"
    ] == 0

    assert audit["counts"][
        "released_packages"
    ] == 0

    assert gate["counts"][
        "rule_promoted_packages"
    ] == 0

    assert gate["counts"][
        "released_packages"
    ] == 0


def test_every_package_has_three_income_scopes():
    audit = load(AUDIT)

    for row in audit["records"]:
        assert row["scope_count"] == 3

        assert {
            scope["income_type"]
            for scope in row["income_scopes"]
        } == {
            "dividend",
            "interest",
            "royalty",
        }
