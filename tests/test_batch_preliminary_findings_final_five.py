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


def test_pl_dividend_general_five_percent() -> None:
    _, index = findings_index()

    finding = index["CZ-PL-DIV-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["rates"][0]["rate"] == 5.0
    assert finding["treaty_findings"]["rate_scope"] == "general"


def test_pl_royalty_general_ten_percent() -> None:
    _, index = findings_index()

    finding = index["CZ-PL-ROY-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["rates"][0]["rate"] == 10.0
    assert "copyright" in finding["treaty_findings"]["rates"][0]["categories"]


def test_se_dividend_missing_zero_rate_is_corrected() -> None:
    _, index = findings_index()

    finding = index["CZ-SE-DIV-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [0.0, 10.0]
    assert finding["candidate_extraction_correction"]["missing_rate"] == 0.0
    assert (
        finding["treaty_findings"][
            "beneficial_owner_wording_explicit"
        ]
        is False
    )


def test_sk_dividend_rates() -> None:
    _, index = findings_index()

    finding = index["CZ-SK-DIV-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [5.0, 15.0]
    assert "10%" in " ".join(rates[0]["conditions"])


def test_sk_royalty_contains_ten_and_zero() -> None:
    _, index = findings_index()

    finding = index["CZ-SK-ROY-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [10.0, 0.0]
    assert "computer software" in rates[0]["categories"]
    assert "computer software" in rates[1]["excluded_categories"]
    assert finding["candidate_extraction_correction"]["missing_rate"] == 0.0


def test_final_findings_remain_fail_closed() -> None:
    payload, index = findings_index()

    assert payload["policy"]["fail_closed"] is True

    for packet_id in (
        "CZ-PL-DIV-LEGAL-REVIEW",
        "CZ-PL-ROY-LEGAL-REVIEW",
        "CZ-SE-DIV-LEGAL-REVIEW",
        "CZ-SK-DIV-LEGAL-REVIEW",
        "CZ-SK-ROY-LEGAL-REVIEW",
    ):
        finding = index[packet_id]

        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
