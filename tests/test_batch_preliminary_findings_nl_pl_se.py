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


def test_nl_dividend_missing_zero_rate_is_corrected() -> None:
    _, index = findings_index()

    finding = index["CZ-NL-DIV-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [0.0, 10.0]
    assert finding["candidate_extraction_correction"]["missing_rate"] == 0.0

    assert any(
        issue["code"] == "participation_exemption_not_extracted"
        and issue["severity"] == "critical"
        for issue in finding["data_quality_issues"]
    )


def test_pl_interest_general_and_exempt_rates() -> None:
    _, index = findings_index()

    finding = index["CZ-PL-INT-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [5.0, 0.0]
    assert "loans or credits granted by a bank" in rates[1]["categories"]
    assert finding["treaty_findings"]["pe_exception_applies"] is True


def test_se_interest_does_not_invent_beneficial_owner() -> None:
    _, index = findings_index()

    finding = index["CZ-SE-INT-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert (
        finding["treaty_findings"][
            "beneficial_owner_wording_explicit"
        ]
        is False
    )
    assert (
        finding["mli_preliminary_finding"][
            "requires_separate_verification"
        ]
        is True
    )


def test_new_findings_remain_fail_closed() -> None:
    payload, index = findings_index()

    assert payload["policy"]["fail_closed"] is True

    for packet_id in (
        "CZ-NL-DIV-LEGAL-REVIEW",
        "CZ-PL-INT-LEGAL-REVIEW",
        "CZ-SE-INT-LEGAL-REVIEW",
    ):
        finding = index[packet_id]

        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
