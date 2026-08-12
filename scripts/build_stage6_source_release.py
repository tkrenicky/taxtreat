from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

PROMOTION = (
    BASE / "stage6_rule_promotion.json"
)

APPROVAL = (
    BASE / "stage6_production_approval.json"
)

GATE = (
    BASE
    / "production_source_release_gate_v2.json"
)

OUTPUT = (
    BASE / "stage6_source_release.json"
)

SUMMARY = (
    BASE / "stage6_source_release_summary.json"
)

RULE_DIR = (
    ROOT / "data/legal_rules_stage6"
)


def load(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


promotion = load(PROMOTION)
approval = load(APPROVAL)
gate = load(GATE)

promotion_by_pair = {
    row["treaty_pair_id"]: row
    for row in promotion["records"]
}

approval_by_pair = {
    row["treaty_pair_id"]: row
    for row in approval["records"]
}

gate_by_pair = {
    row["treaty_pair_id"]: row
    for row in gate["treaty_partners"]
}

if len(promotion_by_pair) != 101:
    raise RuntimeError(
        "Promotion manifest != 101 packages."
    )

if len(approval_by_pair) != 101:
    raise RuntimeError(
        "Approval manifest != 101 packages."
    )

if len(gate_by_pair) != 101:
    raise RuntimeError(
        "Canonical gate != 101 packages."
    )

if (
    promotion["counts"][
        "rule_promoted_scopes"
    ]
    != 303
):
    raise RuntimeError(
        "Promotion manifest != 303 scopes."
    )

records = []

for pair in sorted(
    promotion_by_pair
):
    p = promotion_by_pair[pair]
    a = approval_by_pair[pair]
    g = gate_by_pair[pair]

    package_hash = p[
        "package_sha256"
    ]

    if (
        a["package_sha256"]
        != package_hash
    ):
        raise RuntimeError(
            f"{pair}: approval hash mismatch"
        )

    if (
        g["package_sha256"]
        != package_hash
    ):
        raise RuntimeError(
            f"{pair}: gate hash mismatch"
        )

    if (
        a[
            "production_approval_status"
        ]
        != "production_approved"
    ):
        raise RuntimeError(
            f"{pair}: not production approved"
        )

    rule_path = (
        ROOT / p["rule_file"]
    )

    if not rule_path.exists():
        raise RuntimeError(
            f"{pair}: rule file missing"
        )

    actual_rule_hash = (
        hashlib.sha256(
            rule_path.read_bytes()
        ).hexdigest()
    )

    if (
        actual_rule_hash
        != p["rule_file_sha256"]
    ):
        raise RuntimeError(
            f"{pair}: promoted rule file changed"
        )

    records.append(
        {
            "treaty_pair_id":
                pair,
            "package_sha256":
                package_hash,
            "rule_file":
                p["rule_file"],
            "rule_file_sha256":
                actual_rule_hash,
            "production_approval_status":
                "production_approved",
            "rule_promotion_status":
                "promoted",
            "source_release_status":
                "released",
            "released_scopes":
                3,
        }
    )


payload = {
    "schema_version": 1,
    "dataset_release":
        "stage6-source-release-2026-08-12.1",
    "event_type":
        "explicit_stage6_source_release",
    "release_authority":
        "stage6_governance_policy",
    "additional_human_review_claimed":
        False,
    "semantics": {
        "promotion_required":
            True,
        "production_approval_required":
            True,
        "exact_package_hash_binding_required":
            True,
        "exact_rule_file_hash_binding_required":
            True,
        "secondary_ai_is_not_human_review":
            True,
        "runtime_still_fails_closed_for_unknown_pairs":
            True,
        "missing_transaction_facts_do_not_become_final":
            True,
    },
    "counts": {
        "released_packages":
            101,
        "released_scopes":
            303,
    },
    "records":
        records,
}

OUTPUT.write_text(
    json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

SUMMARY.write_text(
    json.dumps(
        {
            "dataset_release":
                payload[
                    "dataset_release"
                ],
            "released_packages":
                101,
            "released_scopes":
                303,
            "rule_files":
                101,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

print("Explicit source release manifest: PASS")
print("Released packages: 101/101")
print("Released scopes:   303/303")
