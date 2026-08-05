from __future__ import annotations

from taxtreat.tools.build_batch_preliminary_findings import (
    build_findings,
)


def findings_index():
    payload = build_findings()

    return payload, {
        item["packet_id"]: item
        for item in payload["findings"]
    }


def test_registry_contains_all_thirty_findings() -> None:
    payload, _ = findings_index()

    assert payload["summary"]["preliminary_findings_completed"] == 30
    assert payload["summary"]["preliminary_completion_percent"] == 100.0


def test_dk_royalty_contains_ten_and_zero() -> None:
    _, index = findings_index()

    finding = index["CZ-DK-ROY-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [10.0, 0.0]
    assert "computer software" in rates[0]["categories"]
    assert "cinematographic films" in rates[1]["categories"]

    assert finding["candidate_extraction_correction"]["missing_rate"] == 0.0

    assert any(
        issue["code"] == "copyright_zero_rate_not_extracted"
        and issue["severity"] == "critical"
        for issue in finding["data_quality_issues"]
    )


def test_es_dividend_rates() -> None:
    _, index = findings_index()

    finding = index["CZ-ES-DIV-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [5.0, 15.0]
    assert "25%" in " ".join(rates[0]["conditions"])
    assert "beneficial owner" in " ".join(rates[1]["conditions"])


def test_nl_royalty_general_five_percent() -> None:
    _, index = findings_index()

    finding = index["CZ-NL-ROY-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [5.0]
    assert (
        finding["treaty_findings"][
            "beneficial_owner_wording_explicit"
        ]
        is False
    )
    assert (
        finding["protocol_preliminary_finding"]["effect"]
        == "no_article_12_change"
    )


def test_new_findings_remain_fail_closed() -> None:
    payload, index = findings_index()

    assert payload["policy"]["fail_closed"] is True

    for packet_id in (
        "CZ-DK-ROY-LEGAL-REVIEW",
        "CZ-ES-DIV-LEGAL-REVIEW",
        "CZ-NL-ROY-LEGAL-REVIEW",
    ):
        finding = index[packet_id]

        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
