from __future__ import annotations

from taxtreat.tools.build_belgium_review_worksheet import (
    build_worksheet,
)


def test_belgium_worksheet_contains_three_scopes() -> None:
    payload = build_worksheet()

    assert payload["country"] == "BE"
    assert payload["summary"]["scopes"] == 3
    assert {
        item["income_type"]
        for item in payload["scopes"]
    } == {"dividend", "interest", "royalty"}


def test_full_article_text_is_preserved() -> None:
    payload = build_worksheet()

    for scope in payload["scopes"]:
        assert scope["article_text"]
        assert len(scope["article_text"]) > 500
        assert len(scope["article_text_sha256"]) == 64


def test_worksheet_remains_fail_closed() -> None:
    payload = build_worksheet()

    assert payload["policy"]["fail_closed"] is True
    assert payload["policy"]["human_primary_review_required"] is True

    for scope in payload["scopes"]:
        assert scope["review_outcome"] is None
        assert scope["proposed_rule_snapshot"] is None
        assert scope["status"] == "awaiting_primary_review"
        assert all(
            value in (None, [],)
            for value in scope["reviewer_findings"].values()
        )


def test_scope_specific_questions_are_present() -> None:
    payload = build_worksheet()

    scopes = {
        item["income_type"]: item
        for item in payload["scopes"]
    }

    assert any(
        "Article 11(3)" in question
        for question in scopes["interest"]["review_questions"]
    )

    assert any(
        "5% rate" in question
        for question in scopes["royalty"]["review_questions"]
    )
