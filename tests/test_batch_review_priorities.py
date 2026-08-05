from __future__ import annotations

from taxtreat.tools.build_batch_review_priorities import (
    build_priorities,
)


def test_priorities_cover_all_scopes() -> None:
    payload = build_priorities()

    assert payload["summary"]["scopes"] == 30
    assert len(payload["review_order"]) == 30


def test_review_order_is_score_sorted() -> None:
    payload = build_priorities()

    scores = [
        item["priority_score"]
        for item in payload["review_order"]
    ]

    assert scores == sorted(scores, reverse=True)


def test_known_complex_scopes_are_flagged() -> None:
    payload = build_priorities()

    index = {
        item["packet_id"]: item
        for item in payload["review_order"]
    }

    assert any(
        flag["code"] == "dividend_20_percent_candidate"
        for flag in index[
            "CZ-DE-DIV-LEGAL-REVIEW"
        ]["flags"]
    )

    assert any(
        flag["code"] == "multiple_protocol_documents"
        for flag in index[
            "CZ-NL-DIV-LEGAL-REVIEW"
        ]["flags"]
    )

    assert any(
        flag["code"] == "royalty_category_mapping_required"
        for flag in index[
            "CZ-BE-ROY-LEGAL-REVIEW"
        ]["flags"]
    )


def test_priority_report_remains_fail_closed() -> None:
    payload = build_priorities()

    assert payload["policy"]["fail_closed"] is True
    assert (
        payload["policy"][
            "priority_is_not_legal_conclusion"
        ]
        is True
    )
    assert payload["summary"]["completed_primary_reviews"] == 0

    for item in payload["review_order"]:
        assert (
            item["review_status"]
            == "awaiting_primary_review"
        )
