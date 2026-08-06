from taxtreat.tools.build_be_consolidated_primary_review import (
    build_consolidated_review,
)


def test_contains_all_three_belgium_scopes():
    payload = build_consolidated_review()

    assert payload["country"] == "BE"
    assert payload["scope_count"] == 3

    assert {
        scope["income_type"]
        for scope in payload["scopes"]
    } == {
        "dividend",
        "interest",
        "royalty",
    }


def test_all_scopes_are_fail_closed():
    payload = build_consolidated_review()

    for scope in payload["scopes"]:
        assert scope["status"] == "awaiting_primary_review"
        assert scope["review_outcome"] is None
        assert scope["proposed_rule_snapshot"] is None
        assert scope["promotable_to_active_rules"] is False

        assert all(
            value is None
            for value in scope["confirmations"].values()
        )


def test_summary_blocks_all_promotion():
    payload = build_consolidated_review()

    assert payload["summary"] == {
        "awaiting_primary_review": 3,
        "awaiting_independent_approval": 0,
        "returned_for_correction": 0,
        "promotable_scopes": 0,
    }


def test_every_scope_contains_source_bindings():
    payload = build_consolidated_review()

    for scope in payload["scopes"]:
        source_material = scope["source_material"]

        assert source_material["treaty_source_id"]
        assert source_material["domestic_source_id"]
        assert scope["review_row_sha256"]
        assert len(scope["review_row_sha256"]) == 64


def test_review_questions_are_unanswered():
    payload = build_consolidated_review()

    for scope in payload["scopes"]:
        assert scope["review_questions"]

        for question in scope["review_questions"]:
            assert question["answer"] is None
            assert question["legal_reasoning"] is None
            assert question["supporting_source_ids"] == []
