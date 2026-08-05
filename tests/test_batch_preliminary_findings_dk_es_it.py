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


def test_registry_contains_sixteen_findings() -> None:
    payload, _ = findings_index()

    assert payload["summary"]["preliminary_findings_completed"] == 16
    assert payload["summary"]["preliminary_completion_percent"] == 53.3


def test_dk_interest_general_zero_rate() -> None:
    _, index = findings_index()

    finding = index["CZ-DK-INT-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert finding["treaty_findings"]["rate_scope"] == "general"
    assert finding["treaty_findings"]["beneficial_owner_required"] is True
    assert finding["mli_preliminary_finding"]["effective_from"] == (
        "2021-01-01"
    )


def test_es_royalty_categories_and_conditions() -> None:
    _, index = findings_index()

    finding = index["CZ-ES-ROY-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert rates[0]["rate"] == 5.0
    assert rates[1]["rate"] == 0.0
    assert "cinematographic films" in rates[1]["excluded_categories"]

    assert any(
        issue["code"] == "subject_to_tax_condition_required"
        for issue in finding["data_quality_issues"]
    )

    assert (
        finding["treaty_findings"][
            "beneficial_owner_wording_explicit"
        ]
        is False
    )


def test_it_interest_general_zero_rate() -> None:
    _, index = findings_index()

    finding = index["CZ-IT-INT-LEGAL-REVIEW"]

    assert finding["treaty_findings"]["source_state_rate"] == 0.0
    assert finding["treaty_findings"]["beneficial_owner_required"] is True
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
        "CZ-DK-INT-LEGAL-REVIEW",
        "CZ-ES-ROY-LEGAL-REVIEW",
        "CZ-IT-INT-LEGAL-REVIEW",
    ):
        finding = index[packet_id]

        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
