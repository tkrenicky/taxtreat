from __future__ import annotations

from taxtreat.tools.build_batch_preliminary_findings import (
    build_findings,
)


def index_findings():
    payload = build_findings()
    return payload, {
        item["packet_id"]: item
        for item in payload["findings"]
    }


def test_registry_contains_twenty_two_findings() -> None:
    payload, _ = index_findings()

    assert payload["summary"]["preliminary_findings_completed"] == 22
    assert payload["summary"]["preliminary_completion_percent"] == 73.3


def test_dk_dividend_zero_rates_are_distinct() -> None:
    _, index = index_findings()

    rates = index[
        "CZ-DK-DIV-LEGAL-REVIEW"
    ]["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [0.0, 0.0, 15.0]
    assert "pension fund" in " ".join(rates[1]["conditions"])
    assert "10%" in " ".join(rates[0]["conditions"])


def test_it_royalty_categories_are_mapped() -> None:
    _, index = index_findings()

    rates = index[
        "CZ-IT-ROY-LEGAL-REVIEW"
    ]["treaty_findings"]["rates"]

    assert rates[0]["rate"] == 0.0
    assert rates[1]["rate"] == 5.0
    assert "patents" in rates[1]["categories"]


def test_se_royalty_does_not_invent_beneficial_owner() -> None:
    _, index = index_findings()

    finding = index["CZ-SE-ROY-LEGAL-REVIEW"]

    assert any(
        issue["code"] == "beneficial_owner_wording_not_explicit"
        for issue in finding["data_quality_issues"]
    )

    assert finding["treaty_findings"]["rates"][1]["conditions"] == []


def test_all_new_findings_remain_fail_closed() -> None:
    payload, index = index_findings()

    assert payload["policy"]["fail_closed"] is True

    for packet_id in (
        "CZ-DK-DIV-LEGAL-REVIEW",
        "CZ-IT-ROY-LEGAL-REVIEW",
        "CZ-SE-ROY-LEGAL-REVIEW",
    ):
        finding = index[packet_id]
        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
