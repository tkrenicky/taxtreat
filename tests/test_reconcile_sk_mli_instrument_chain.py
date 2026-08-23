from __future__ import annotations

from taxtreat.tools.reconcile_sk_mli_instrument_chain import (
    build_reconciliation,
    build_summary,
)


def test_sk_mli_instrument_chain_reconciliation_covers_all_46_relationships():
    payload = build_reconciliation()
    summary = build_summary(payload)

    assert payload["source_country"] == "SK"
    assert payload["relationship_count"] == 46
    assert len(payload["relationships"]) == 46
    assert len({row["recipient_country"] for row in payload["relationships"]}) == 46
    assert summary["resolved_relationships"] + summary[
        "unresolved_notice_mismatches"
    ] == 46


def test_finland_old_notice_is_resolved_only_through_verified_supersession():
    payload = build_reconciliation()
    finland = next(
        row
        for row in payload["relationships"]
        if row["recipient_country"] == "FI"
    )

    assert finland["instrument_inventory_notice"] == "255/2019"
    assert finland["current_mf_status_notice"] == "321/2023"
    assert finland["notice_alignment_status"] == "supersession_verified"
    assert finland["resolved"] is True
    assert finland["supersession_evidence_notice"] == "321/2023"


def test_unresolved_notice_mismatch_would_block_review_readiness_policy():
    payload = build_reconciliation()
    assert payload["policy"]["notice_mismatch_requires_evidence"] is True
    assert payload["policy"][
        "superseded_notice_must_not_be_treated_as_current"
    ] is True
    assert payload["policy"][
        "unresolved_mismatch_blocks_review_readiness"
    ] is True
