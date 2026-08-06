import json
from pathlib import Path


ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)


def load(name):
    return json.loads(
        (ROOT / name).read_text(encoding="utf-8")
    )


def test_expected_counts():
    assert (
        load("single_rate_review_pack.json")
        ["scope_count"]
        == 189
    )
    assert (
        load("conditional_rate_review_pack.json")
        ["scope_count"]
        == 98
    )
    assert (
        load("source_exception_review_queue.json")
        ["scope_count"]
        == 7
    )


def test_complete_unique_coverage():
    packs = [
        load("single_rate_review_pack.json"),
        load("conditional_rate_review_pack.json"),
        load("source_exception_review_queue.json"),
    ]

    packet_ids = [
        row["packet_id"]
        for pack in packs
        for row in pack["scopes"]
    ]

    assert len(packet_ids) == 294
    assert len(set(packet_ids)) == 294


def test_single_rate_candidates_have_rate():
    rows = load(
        "single_rate_review_pack.json"
    )["scopes"]

    assert all(
        row["resolved_rate_candidate"] is not None
        for row in rows
    )


def test_conditional_cases_have_marker():
    rows = load(
        "conditional_rate_review_pack.json"
    )["scopes"]

    assert all(
        "multiple_rate_conditions"
        in row["conditional_codes"]
        for row in rows
    )


def test_exceptions_have_hard_reason():
    rows = load(
        "source_exception_review_queue.json"
    )["scopes"]

    assert all(
        row["hard_unresolved_codes"]
        for row in rows
    )


def test_outputs_remain_fail_closed():
    for name in (
        "single_rate_review_pack.json",
        "conditional_rate_review_pack.json",
        "source_exception_review_queue.json",
        "global_review_work_packs_summary.json",
    ):
        payload = load(name)

        assert payload["fail_closed"] is True
        assert (
            payload["promotable_to_active_rules"]
            is False
        )
