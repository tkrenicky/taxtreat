from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxtreat.engine.legal_rule_loader import (
    load_legal_rules,
)


ROOT = Path(__file__).resolve().parents[1]

BASE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound"
)

RULE_DIR = (
    ROOT
    / "data/legal_rules_stage6"
)


def load(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def hash_map(rows):
    return {
        row["treaty_pair_id"]:
            row["package_sha256"]
        for row in rows
    }


def test_catalog_covers_101_pairs_and_303_scopes():
    files = sorted(
        RULE_DIR.glob("*.json")
    )

    assert len(files) == 101

    pairs = set()
    scopes = set()

    for path in files:
        rules = load_legal_rules(path)

        assert rules

        for rule in rules:
            assert rule.verification_status == "verified"
            assert (
                rule.verification_authority
                == "stage6_governance_policy"
            )

            pairs.add(
                (
                    rule.source_country,
                    rule.recipient_country,
                )
            )

            scopes.add(
                (
                    rule.source_country,
                    rule.recipient_country,
                    rule.income_type,
                )
            )

    assert len(pairs) == 101
    assert len(scopes) == 303


def test_exact_hash_binding_across_governance_fails_closed_for_semantic_rehash():
    q = load(BASE / "cz_country_qa_queue.json")
    a = load(BASE / "stage6_production_approval.json")
    r = load(BASE / "stage6_production_materialization_readiness.json")
    g = load(BASE / "production_source_release_gate_v2.json")
    p = load(BASE / "stage6_rule_promotion.json")
    remediation = load(
        ROOT / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json"
    )

    qh = hash_map(q["packages"])
    ah = hash_map(a["records"])
    rh = hash_map(r["records"])
    gh = hash_map(g["treaty_partners"])
    ph = hash_map(p["records"])
    remediation_pairs = {
        f"CZ-{row['country']}"
        for row in remediation["corrections"]
    }

    assert len(qh) == 101
    assert qh == gh

    stale_approval_pairs = {
        pair_id
        for pair_id in qh
        if qh[pair_id] != ah[pair_id]
    }
    assert len(stale_approval_pairs) == 40
    assert stale_approval_pairs == remediation_pairs

    for pair_id in qh:
        if pair_id in remediation_pairs:
            assert qh[pair_id] != ah[pair_id]
            assert qh[pair_id] != rh[pair_id]
            assert qh[pair_id] != ph[pair_id]
        else:
            assert qh[pair_id] == ah[pair_id] == rh[pair_id] == ph[pair_id]


def test_promotion_complete_but_source_release_zero():
    promotion = load(
        BASE / "stage6_rule_promotion.json"
    )

    counts = promotion["counts"]

    assert counts["rule_promoted_packages"] == 101
    assert counts["rule_promoted_scopes"] == 303
    assert counts["source_released_packages"] == 0
    assert counts["source_released_scopes"] == 0


def test_rule_file_hashes_match_manifest_or_are_quarantined():
    promotion = load(
        BASE / "stage6_rule_promotion.json"
    )
    from taxtreat.engine.legal_rule_engine import (
        _PENDING_SEMANTIC_REMEDIATION_SCOPES,
    )

    quarantined_countries = {
        country
        for country, _income_type in _PENDING_SEMANTIC_REMEDIATION_SCOPES
    }
    mismatches = []

    for record in promotion["records"]:
        path = ROOT / record["rule_file"]

        actual = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

        if actual == record["rule_file_sha256"]:
            continue

        country = path.stem.upper()
        mismatches.append(country)
        # Any package whose exact promoted hash no longer matches is
        # unapproved by definition. It may remain in the repository only
        # while the independent source-release gate is closed. Semantic
        # quarantine is an additional guard for known remediation scopes,
        # but hash drift must never be treated as promoted/released merely
        # because the country is not yet in that narrower registry.
        assert record["source_release_status"] == "not_released", (
            f"Hash-drifted Stage 6 package is source-released: {country}"
        )

    assert mismatches, "Expected at least one hash-bound remediation mismatch."


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
            assert rule["source_url"].startswith(
                "https://"
            )


def test_gr_dividend_has_no_invented_treaty_cap():
    payload = load(
        RULE_DIR / "gr.json"
    )

    treaty_rows = [
        row
        for row in payload["rules"]
        if (
            row["income_type"] == "dividend"
            and row["legal_layer"]
            in {"treaty", "protocol"}
        )
    ]

    assert treaty_rows == []


def test_canonical_gate_is_fail_closed_for_semantically_rehashed_packages():
    gate = load(BASE / "production_source_release_gate_v2.json")
    remediation = load(
        ROOT / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json"
    )
    remediation_pairs = {
        f"CZ-{row['country']}"
        for row in remediation["corrections"]
    }

    assert gate["counts"]["rule_promoted_packages"] == 61
    assert gate["counts"]["released_packages"] == 61
    assert gate["counts"]["released_scopes"] == 183

    released = {
        row["treaty_pair_id"]
        for row in gate["treaty_partners"]
        if row["release_status"] == "released"
    }
    blocked = {
        row["treaty_pair_id"]
        for row in gate["treaty_partners"]
        if row["release_status"] == "not_released"
    }
    assert len(released) == 61
    assert blocked == remediation_pairs
