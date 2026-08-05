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


def test_es_interest_does_not_invent_beneficial_owner() -> None:
    _, index = findings_index()

    finding = index["CZ-ES-INT-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert (
        finding["treaty_findings"][
            "beneficial_owner_wording_explicit"
        ]
        is False
    )


def test_fr_royalty_contains_zero_five_and_ten() -> None:
    _, index = findings_index()

    finding = index["CZ-FR-ROY-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [
        0.0,
        5.0,
        10.0,
    ]

    assert "computer software" in rates[0]["excluded_categories"]
    assert "computer software" in rates[2]["categories"]

    assert any(
        issue["code"] == "zero_rate_not_extracted"
        for issue in finding["data_quality_issues"]
    )


def test_sk_interest_general_zero_rate() -> None:
    _, index = findings_index()

    finding = index["CZ-SK-INT-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert finding["treaty_findings"]["beneficial_owner_required"] is True
    assert finding["mli_preliminary_finding"]["effective_from"] == (
        "2021-01-01"
    )


def test_new_findings_remain_fail_closed() -> None:
    payload, index = findings_index()

    assert payload["policy"]["fail_closed"] is True

    for packet_id in (
        "CZ-ES-INT-LEGAL-REVIEW",
        "CZ-FR-ROY-LEGAL-REVIEW",
        "CZ-SK-INT-LEGAL-REVIEW",
    ):
        finding = index[packet_id]

        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
