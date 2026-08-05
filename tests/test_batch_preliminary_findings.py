from __future__ import annotations

from taxtreat.tools.build_batch_preliminary_findings import (
    build_findings,
)


def test_registry_contains_twenty_two_findings() -> None:
    payload = build_findings()

    assert payload["summary"]["total_scopes"] == 30
    assert payload["summary"]["preliminary_findings_completed"] == 22
    assert payload["summary"]["preliminary_completion_percent"] == 73.3


def test_nl_interest_general_zero_rate_is_recorded() -> None:
    payload = build_findings()

    finding = next(
        item
        for item in payload["findings"]
        if item["packet_id"] == "CZ-NL-INT-LEGAL-REVIEW"
    )

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert finding["treaty_findings"]["rate_scope"] == "general"
    assert finding["treaty_findings"]["pe_exception_applies"] is True


def test_nl_text_quality_issue_is_preserved() -> None:
    payload = build_findings()

    finding = next(
        item
        for item in payload["findings"]
        if item["packet_id"] == "CZ-NL-INT-LEGAL-REVIEW"
    )

    issue = finding["data_quality_issues"][0]

    assert issue["code"] == "article_text_truncated"
    assert issue["affects_general_rate_conclusion"] is False


def test_registry_remains_fail_closed() -> None:
    payload = build_findings()

    assert payload["policy"]["fail_closed"] is True
    assert payload["summary"]["completed_primary_reviews"] == 0
    assert payload["summary"]["approved_scopes"] == 0

    for finding in payload["findings"]:
        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
