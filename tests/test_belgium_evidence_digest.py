from __future__ import annotations

from taxtreat.tools.build_belgium_evidence_digest import (
    build_digest,
)


def test_digest_contains_three_scopes() -> None:
    payload = build_digest()

    assert payload["country"] == "BE"
    assert len(payload["scopes"]) == 3


def test_digest_contains_source_paragraphs() -> None:
    payload = build_digest()

    for scope in payload["scopes"]:
        assert scope["relevant_article_paragraphs"]
        assert scope["article_text_sha256"]

        for paragraph in scope["relevant_article_paragraphs"]:
            assert paragraph["text"]
            assert paragraph["matched_markers"]


def test_digest_remains_fail_closed() -> None:
    payload = build_digest()

    assert payload["policy"]["fail_closed"] is True
    assert (
        payload["policy"]["no_automatic_legal_conclusion"]
        is True
    )

    for scope in payload["scopes"]:
        assert scope["status"] == "awaiting_primary_review"
        assert all(
            value in (None, [])
            for value in scope["preliminary_findings"].values()
        )
