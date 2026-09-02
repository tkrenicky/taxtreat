from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxtreat.engine.legal_rule_loader import load_legal_rules

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
RULE_DIR = ROOT / "data/legal_rules_stage6"
MACHINE_AUTHORITY = "semantic_remediation_machine_validation"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def hash_map(rows):
    return {row["treaty_pair_id"]: row["package_sha256"] for row in rows}


def remediation_pairs():
    payload = load(ROOT / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json")
    return {f"CZ-{row['country']}" for row in payload["corrections"]}


def test_catalog_covers_101_pairs_and_303_scopes():
    files = sorted(RULE_DIR.glob("*.json"))
    assert len(files) == 101
    pairs = set()
    scopes = set()
    machine_rules = 0

    for path in files:
        rules = load_legal_rules(path)
        assert rules
        for rule in rules:
            assert rule.verification_status == "verified"
            assert rule.verification_authority in {
                "stage6_governance_policy",
                MACHINE_AUTHORITY,
            }
            if rule.verification_authority == MACHINE_AUTHORITY:
                machine_rules += 1
                assert rule.review_package_sha256
                assert rule.approval_dataset_release == (
                    "stage6-semantic-remediation-machine-validation-2026-09-01.1"
                )
                assert rule.reviewer_id is None
                assert rule.reviewed_at is None
                assert rule.approved_by is None
                assert rule.approved_at is None
            pairs.add((rule.source_country, rule.recipient_country))
            scopes.add((rule.source_country, rule.recipient_country, rule.income_type))

    assert len(pairs) == 101
    assert len(scopes) == 303
    assert machine_rules > 0


def test_exact_hash_binding_across_governance_after_semantic_release():
    q = load(BASE / "cz_country_qa_queue.json")
    a = load(BASE / "stage6_production_approval.json")
    g = load(BASE / "production_source_release_gate_v2.json")
    p = load(BASE / "stage6_rule_promotion.json")

    qh = hash_map(q["packages"])
    ah = hash_map(a["records"])
    gh = hash_map(g["treaty_partners"])
    ph = hash_map(p["records"])

    assert len(qh) == 101
    assert qh == ah == gh == ph

    rows = {row["treaty_pair_id"]: row for row in g["treaty_partners"]}
    for pair_id in remediation_pairs():
        machine = rows[pair_id]["release_evidence"]["semantic_remediation_machine_release"]
        assert machine["package_sha256"] == qh[pair_id]
        assert machine["additional_human_review_claimed"] is False


def test_promotion_complete_but_source_release_manifest_is_explicit():
    promotion = load(BASE / "stage6_rule_promotion.json")
    counts = promotion["counts"]
    assert counts["rule_promoted_packages"] == 101
    assert counts["rule_promoted_scopes"] == 303


def test_rule_file_hashes_match_promotion_manifest():
    promotion = load(BASE / "stage6_rule_promotion.json")
    for record in promotion["records"]:
        path = ROOT / record["rule_file"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == record["rule_file_sha256"], record["treaty_pair_id"]


def test_relief_source_provenance_is_explicit():
    allowed = {
        "explicit_candidate_source",
        "approved_czech_statutory_reference",
        "approved_czech_domestic_regime",
    }
    for path in RULE_DIR.glob("*.json"):
        payload = load(path)
        for rule in payload["rules"]:
            if rule["legal_layer"] != "eu_relief":
                continue
            assert rule["source_basis"] in allowed
            assert rule["source_id"]
            assert rule["source_url"].startswith("https://")


def test_gr_dividend_has_no_invented_treaty_cap():
    payload = load(RULE_DIR / "gr.json")
    treaty_rows = [
        row for row in payload["rules"]
        if row["income_type"] == "dividend"
        and row["legal_layer"] in {"treaty", "protocol"}
    ]
    assert len(treaty_rows) == 1
    rule = treaty_rows[0]
    assert rule["rule_id"] == "CZ-GR-DIVIDEND-CURRENT-1"
    assert rule["rate"] is None
    assert rule["tax_treatment"] == "domestic_rate_applies"
    assert rule["verification_status"] == "verified"
    assert rule["verification_authority"] == MACHINE_AUTHORITY
    assert any(
        condition["fact"] == "permanent_establishment_connection"
        and condition["operator"] == "=="
        and str(condition["value"]).lower() == "false"
        for condition in rule["conditions"]
    )


def test_canonical_gate_releases_semantically_rehashed_packages_after_validation():
    gate = load(BASE / "production_source_release_gate_v2.json")
    remediation = remediation_pairs()

    assert gate["counts"]["rule_promoted_packages"] == 101
    assert gate["counts"]["released_packages"] == 101
    assert gate["counts"]["released_scopes"] == 303
    assert gate["counts"]["semantic_remediation_pending_packages"] == 0

    rows = {row["treaty_pair_id"]: row for row in gate["treaty_partners"]}
    assert all(row["release_status"] == "released" for row in rows.values())
    for pair_id in remediation:
        row = rows[pair_id]
        assert row["human_review_status"] == "needs_review"
        assert row["fail_closed"] is False
        assert row["release_blockers"] == []
        machine = row["release_evidence"]["semantic_remediation_machine_release"]
        assert machine["package_sha256"] == row["package_sha256"]
        assert machine["additional_human_review_claimed"] is False
