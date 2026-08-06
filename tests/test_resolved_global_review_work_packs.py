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


def test_resolved_work_pack_counts():
    assert (
        load("single_rate_review_pack.json")
        ["scope_count"]
        == 192
    )
    assert (
        load("conditional_rate_review_pack.json")
        ["scope_count"]
        == 102
    )
    assert (
        load("source_exception_review_queue.json")
        ["scope_count"]
        == 0
    )


def test_resolved_work_packs_cover_every_scope():
    packs = [
        load("single_rate_review_pack.json"),
        load("conditional_rate_review_pack.json"),
    ]

    packet_ids = [
        row["packet_id"]
        for pack in packs
        for row in pack["scopes"]
    ]

    assert len(packet_ids) == 294
    assert len(set(packet_ids)) == 294


def test_exception_queue_is_empty():
    payload = load(
        "source_exception_review_queue.json"
    )

    assert payload["scopes"] == []


def test_summary_confirms_exception_resolution():
    payload = load(
        "global_review_work_packs_summary.json"
    )

    assert (
        payload["all_source_exceptions_resolved"]
        is True
    )
    assert payload["work_pack_counts"] == {
        "single_rate": 192,
        "conditional": 102,
        "exceptions": 0,
    }


def test_all_outputs_remain_fail_closed():
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
