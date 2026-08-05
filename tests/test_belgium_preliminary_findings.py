from __future__ import annotations

from taxtreat.tools.build_belgium_preliminary_findings import (
    build_findings,
)


def test_findings_cover_all_three_scopes() -> None:
    payload = build_findings()

    assert payload["summary"]["scopes"] == 3
    assert {
        item["income_type"]
        for item in payload["findings"]
    } == {"dividend", "interest", "royalty"}


def test_interest_exemptions_are_recorded() -> None:
    payload = build_findings()

    interest = next(
        item
        for item in payload["findings"]
        if item["income_type"] == "interest"
    )

    assert interest["treaty_findings"]["general_rate"] == 10.0
    assert (
        interest["treaty_findings"][
            "source_state_exemption_rate"
        ]
        == 0.0
    )
    assert len(
        interest["treaty_findings"][
            "source_state_exemptions"
        ]
    ) == 5


def test_royalty_categories_are_split() -> None:
    payload = build_findings()

    royalty = next(
        item
        for item in payload["findings"]
        if item["income_type"] == "royalty"
    )

    rates = royalty["treaty_findings"]["rates"]

    assert rates[0]["rate"] == 5.0
    assert rates[1]["rate"] == 10.0
    assert "software" in rates[1]["categories"]
    assert "know-how" in rates[1]["categories"]


def test_findings_are_not_legal_approval() -> None:
    payload = build_findings()

    assert payload["policy"]["fail_closed"] is True
    assert (
        payload["policy"]["not_a_completed_legal_review"]
        is True
    )
    assert payload["summary"]["completed_primary_reviews"] == 0
    assert payload["summary"]["approved_scopes"] == 0

    for item in payload["findings"]:
        assert item["human_confirmation_required"] is True
        assert item["review_outcome"] is None
        assert item["status"] == "preliminary_findings_only"
