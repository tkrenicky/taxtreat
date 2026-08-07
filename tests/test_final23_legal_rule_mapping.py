import json
from pathlib import Path

PATH = Path(
    "data/legal_reviews/global_cz_outbound/"
    "final23_legal_rule_mapping.json"
)

def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )

def test_mapping_has_all_54_scopes():
    data = load()

    assert data["scope"]["treaty_pair_count"] == 18
    assert data["scope"]["income_scope_count"] == 54
    assert len(data["records"]) == 54

def test_each_scope_has_base_treaty_mapping():
    data = load()

    for row in data["records"]:
        base = row["base_treaty"]

        assert base["article_number"] in {10, 11, 12}
        assert base["source_id"]
        assert base["candidate_rates"]

        assert base["rate_evidence_mode"] in {
            "semantic_rate_candidates",
            "numeric_candidates_only",
        }

        assert row["source_review_pack"]
        assert row["source_review_pack_sha256"]

def test_mapping_does_not_activate_candidates():
    data = load()

    assert data["legal_verification_completed"] is False
    assert data["production_ready"] is False
    assert data["fail_closed"] is True

    assert (
        data["summary"][
            "legal_rule_mapping_verified_count"
        ]
        == 0
    )

    assert (
        data["summary"]["active_rule_allowed_count"]
        == 0
    )

    assert (
        data["summary"]["production_ready_count"]
        == 0
    )

    for row in data["records"]:
        assert (
            row["mapping_status"]
            == "mapped_needs_release_review"
        )

        assert (
            row["legal_rule_mapping_verified"]
            is False
        )

        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True

def test_articles_match_income_types():
    data = load()

    expected = {
        "dividend": 10,
        "interest": 11,
        "royalty": 12,
    }

    for row in data["records"]:
        assert (
            row["base_treaty"]["article_number"]
            == expected[row["income_type"]]
        )

def test_numeric_only_candidates_remain_explicit():
    data = load()

    for row in data["records"]:
        base = row["base_treaty"]

        if (
            base["rate_evidence_mode"]
            != "numeric_candidates_only"
        ):
            continue

        for candidate in base["candidate_rates"]:
            assert (
                candidate["evidence_level"]
                == "numeric_candidate_only"
            )

            assert candidate["source_text"] is None
