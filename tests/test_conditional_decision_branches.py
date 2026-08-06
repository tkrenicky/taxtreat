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


def test_all_scopes_are_included():
    payload = load("conditional_decision_branches.json")

    assert payload["scope_count"] == 102
    assert len(payload["scopes"]) == 102
    assert len({
        row["packet_id"]
        for row in payload["scopes"]
    }) == 102


def test_scope_metadata():
    payload = load("conditional_decision_branches.json")

    for row in payload["scopes"]:
        assert row["scope_status"] in {
            "normalized_candidate_branches",
            "manual_condition_mapping_required",
        }
        assert row["fail_closed"] is True
        assert row["promotable_to_active_rules"] is False


def test_branch_metadata():
    payload = load("conditional_decision_branches.json")

    for row in payload["scopes"]:
        for branch in row["branches"]:
            assert branch["branch_id"]
            assert branch["priority"] >= 1
            assert branch["branch_status"] in {
                "candidate_branch",
                "incomplete_candidate_branch",
            }
            assert branch["fail_closed"] is True
            assert branch["promotable_to_active_rules"] is False


def test_fail_closed_semantics():
    payload = load("conditional_decision_branches.json")
    semantics = payload["decision_semantics"]

    assert semantics["candidate_rates_are_active_rules"] is False
    assert semantics["missing_fact_result"] == "fail_closed"
    assert semantics["no_matching_branch_result"] == "fail_closed"


def test_summary_matches_dataset():
    payload = load("conditional_decision_branches.json")
    summary = load("conditional_decision_branches_summary.json")

    assert summary["scope_count"] == 102
    assert sum(summary["scope_status_counts"].values()) == 102

    expected_branches = sum(
        row["branch_count"]
        for row in payload["scopes"]
    )

    assert (
        sum(summary["branch_status_counts"].values())
        == expected_branches
    )
