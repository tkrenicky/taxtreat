import json
from pathlib import Path

PATH = Path(
    "data/legal_reviews/global_cz_outbound/"
    "stage4_final_runtime_release_gate.json"
)

def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )

def test_stage4_is_complete():
    data = load()

    assert data["stage"]["number"] == 4
    assert data["stage"]["status"] == "complete"
    assert data["stage4_complete"] is True

def test_all_stage4_release_gates_pass():
    data = load()

    assert data["release_gates"]
    assert all(
        data["release_gates"].values()
    )

def test_final23_runtime_scope_is_complete():
    data = load()

    assert (
        data["scope"]["treaty_pair_count"]
        == 18
    )

    assert (
        data["scope"]["income_scope_count"]
        == 54
    )

    assert (
        data["scope"]["runtime_rule_count"]
        == 78
    )

def test_all_54_scopes_are_e2e_fail_closed():
    data = load()

    assert data["e2e"]["scope_count"] == 54
    assert len(data["e2e"]["records"]) == 54

    for row in data["e2e"]["records"]:
        assert (
            row[
                "complete_fact_requires_review"
            ]
            is True
        )

        assert (
            row[
                "incomplete_fact_requires_review"
            ]
            is True
        )

        assert (
            row["final_result_possible"]
            is False
        )

def test_stage4_does_not_fake_legal_release():
    data = load()

    boundary = data[
        "legal_release_boundary"
    ]

    assert (
        boundary[
            "stage4_does_not_equal_legal_approval"
        ]
        is True
    )

    assert (
        boundary[
            "candidate_rules_remain_needs_review"
        ]
        is True
    )

    assert (
        boundary[
            "independent_legal_approval_required_for_verified_promotion"
        ]
        is True
    )

    assert (
        data[
            "production_legal_release_complete"
        ]
        is False
    )


def test_candidate_catalog_is_separate_from_production():
    data = load()

    boundary = data["runtime_catalog_boundary"]

    assert (
        boundary[
            "candidate_catalog_isolated_from_production"
        ]
        is True
    )

    assert (
        boundary["candidate_rule_count"]
        == 78
    )

    assert (
        boundary["candidate_verification_status"]
        == "needs_review"
    )

    assert (
        boundary["production_autoload_allowed"]
        is False
    )
