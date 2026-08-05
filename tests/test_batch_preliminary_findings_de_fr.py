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


def test_registry_contains_twenty_five_findings() -> None:
    payload, _ = findings_index()

    assert payload["summary"]["preliminary_findings_completed"] == 25
    assert payload["summary"]["preliminary_completion_percent"] == 83.3


def test_de_dividend_extraction_error_is_corrected() -> None:
    _, index = findings_index()

    finding = index["CZ-DE-DIV-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [
        5.0,
        15.0,
        25.0,
    ]

    correction = finding["candidate_extraction_correction"]

    assert correction["incorrect_extracted_rate"] == 20.0
    assert correction["correct_source_text_rate"] == 25.0
    assert correction["base_candidate_must_not_be_promoted"] is True

    assert any(
        issue["code"] == "rate_condition_misclassified_as_rate"
        and issue["severity"] == "critical"
        for issue in finding["data_quality_issues"]
    )


def test_de_interest_general_zero_rate_is_recorded() -> None:
    _, index = findings_index()

    finding = index["CZ-DE-INT-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert finding["treaty_findings"]["rate_scope"] == "general"
    assert finding["treaty_findings"]["pe_exception_applies"] is True
    assert finding["treaty_findings"]["excess_payment_limitation"] is True


def test_fr_interest_requires_beneficial_owner() -> None:
    _, index = findings_index()

    finding = index["CZ-FR-INT-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert finding["treaty_findings"]["beneficial_owner_required"] is True
    assert finding["mli_preliminary_finding"]["effective_from"] == (
        "2021-01-01"
    )


def test_new_findings_remain_fail_closed() -> None:
    payload, index = findings_index()

    assert payload["policy"]["fail_closed"] is True

    for packet_id in (
        "CZ-DE-DIV-LEGAL-REVIEW",
        "CZ-DE-INT-LEGAL-REVIEW",
        "CZ-FR-INT-LEGAL-REVIEW",
    ):
        finding = index[packet_id]

        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
