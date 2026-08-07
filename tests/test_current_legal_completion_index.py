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
        (ROOT / name).read_text(
            encoding="utf-8"
        )
    )


def test_index_covers_all_pairs():
    payload = load(
        "current_legal_completion_index.json"
    )

    assert payload[
        "treaty_pair_count"
    ] == 98

    assert len(
        payload["treaty_pairs"]
    ) == 98

    assert len({
        row["treaty_pair_id"]
        for row in payload[
            "treaty_pairs"
        ]
    }) == 98


def test_counts_reconcile():
    payload = load(
        "current_legal_completion_index.json"
    )

    assert (
        payload[
            "review_evidence_pair_count"
        ]
        + payload[
            "remaining_pair_count"
        ]
        == 98
    )


def test_no_production_readiness_is_inferred():
    payload = load(
        "current_legal_completion_index.json"
    )

    for row in payload[
        "treaty_pairs"
    ]:
        assert row[
            "production_ready_inferred"
        ] is False

        assert row[
            "production_ready_must_be_explicit"
        ] is True


def test_summary_matches():
    payload = load(
        "current_legal_completion_index.json"
    )

    summary = load(
        "current_legal_completion_index_summary.json"
    )

    assert summary[
        "treaty_pair_count"
    ] == 98

    assert (
        summary[
            "production_legal_review_complete_count"
        ]
        == payload[
            "production_legal_review_complete_count"
        ]
    )

    assert (
        summary[
            "not_production_complete_count"
        ]
        == payload[
            "not_production_complete_count"
        ]
    )

    assert (
        summary[
            "legal_completion_stage_counts"
        ]
        == payload[
            "legal_completion_stage_counts"
        ]
    )

    assert (
        len(summary["pairs_with_review_evidence"])
        == 23
    )

    assert (
        len(summary["pairs_requiring_primary_review"])
        == 75
    )

    assert (
        len(summary["pairs_requiring_final_completion"])
        == 23
    )
