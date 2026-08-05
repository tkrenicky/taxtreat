from __future__ import annotations

from taxtreat.tools.build_batch_review_dossiers import (
    build_dossiers,
)


def test_dossiers_cover_complete_batch() -> None:
    payload = build_dossiers()

    assert payload["summary"]["countries"] == 10
    assert payload["summary"]["scopes"] == 30
    assert len(payload["countries"]) == 10


def test_each_country_contains_three_scopes() -> None:
    payload = build_dossiers()

    for country in payload["countries"]:
        assert len(country["scopes"]) == 3
        assert {
            scope["income_type"]
            for scope in country["scopes"]
        } == {"dividend", "interest", "royalty"}


def test_source_material_is_preserved() -> None:
    payload = build_dossiers()

    for country in payload["countries"]:
        for scope in country["scopes"]:
            assert scope["treaty_source_id"]
            assert scope["article_text_sha256"]
            assert scope["article_paragraphs"]
            assert scope["domestic_rate_candidate"]


def test_all_dossiers_remain_fail_closed() -> None:
    payload = build_dossiers()

    assert payload["policy"]["fail_closed"] is True
    assert (
        payload["policy"]["automatic_approval_prohibited"]
        is True
    )

    for country in payload["countries"]:
        assert country["review_completion_percent"] == 0

        for scope in country["scopes"]:
            assert scope["status"] == "awaiting_primary_review"
            assert scope["approval_eligible"] is False
            assert scope["review"]["outcome"] is None
            assert scope["review"]["reviewer_id"] is None
