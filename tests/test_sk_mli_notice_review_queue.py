from __future__ import annotations

from taxtreat.tools.build_sk_mli_notice_review_queue import (
    build_queue,
    build_summary,
)


def test_sk_mli_notice_queue_covers_all_relationships_and_scopes():
    payload = build_queue()
    summary = build_summary(payload)

    assert payload["source_country"] == "SK"
    assert payload["relationship_count"] == 46
    assert payload["scope_count"] == 138
    assert len(payload["relationships"]) == 46
    assert len(payload["scopes"]) == 138
    assert len({row["recipient_country"] for row in payload["relationships"]}) == 46
    assert len({row["packet_id"] for row in payload["scopes"]}) == 138

    assert summary["notice_urls_ready"] == 46
    assert summary["correction_notice_relationship_count"] == 1
    assert summary["substantive_matching_completed_relationships"] == 0
    assert summary["wht_effective_dates_completed_relationships"] == 0
    assert summary["review_ready_scopes"] == 0
    assert summary["human_reviewed_scopes"] == 0
    assert summary["production_released_scopes"] == 0


def test_mf_sr_effective_date_is_not_treated_as_wht_effective_date():
    payload = build_queue()
    by_country = {
        row["recipient_country"]: row
        for row in payload["relationships"]
    }

    assert by_country["AT"]["mf_sr_modification_effective_from"] == "2019-01-01"
    assert by_country["AT"]["slovak_notice"] == "410/2018"
    assert by_country["AT"]["wht_effective_date"] is None
    assert by_country["AT"]["wht_effective_date_status"] == "pending_notice_review"

    assert by_country["DE"]["mf_sr_modification_effective_from"] == "2025-01-01"
    assert by_country["DE"]["slovak_notice"] == "262/2024"
    assert by_country["DE"]["wht_effective_date"] is None


def test_french_mli_correction_notice_is_preserved():
    payload = build_queue()
    france = next(
        row
        for row in payload["relationships"]
        if row["recipient_country"] == "FR"
    )

    assert france["slovak_notice"] == "405/2018"
    assert france["correction_notice"] == "254/2019"
    assert france["correction_notice_url"].endswith("/2019/254/")


def test_mli_notice_scope_queue_remains_fail_closed():
    payload = build_queue()

    assert payload["policy"]["fail_closed"] is True
    assert payload["policy"][
        "mf_sr_modification_effective_date_is_not_wht_effective_date"
    ] is True
    assert payload["policy"][
        "human_review_starts_only_after_all_machine_evidence_is_ready"
    ] is True

    assert all(not row["review_ready"] for row in payload["scopes"])
    assert all(not row["approval_eligible"] for row in payload["scopes"])
    assert all(
        row["runtime_status"] == "not_released"
        for row in payload["scopes"]
    )
