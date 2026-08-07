import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

QUEUE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "final23_clean_source_verification_queue.json"
)


def load():
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def test_queue_covers_18_clean_candidate_pairs():
    data = load()

    assert data["pair_count"] == 18
    assert data["scope_count"] == 54
    assert len(data["records"]) == 18


def test_each_pair_has_three_income_scopes():
    data = load()

    for row in data["records"]:
        assert row["scope_count"] == 3
        assert {
            scope["income_type"]
            for scope in row["scopes"]
        } == {"dividend", "interest", "royalty"}


def test_queue_remains_fail_closed():
    data = load()

    assert data["verified_pair_count"] == 0
    assert data["active_rule_allowed_count"] == 0
    assert data["fail_closed"] is True

    for row in data["records"]:
        assert row["verification_status"] == "pending"
        assert row["active_rule_allowed"] is False
        assert row["fail_closed"] is True


def test_every_scope_has_explicit_verification_gaps():
    data = load()

    for row in data["records"]:
        for scope in row["scopes"]:
            assert scope["missing_verification_fields"]
