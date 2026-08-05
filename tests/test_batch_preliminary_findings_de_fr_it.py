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


def test_registry_contains_twenty_two_findings() -> None:
    payload, _ = findings_index()

    assert payload["summary"]["preliminary_findings_completed"] == 22
    assert payload["summary"]["preliminary_completion_percent"] == 73.3


def test_de_royalty_general_five_percent() -> None:
    _, index = findings_index()

    finding = index["CZ-DE-ROY-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [5.0]
    assert (
        finding["treaty_findings"][
            "beneficial_owner_wording_explicit"
        ]
        is False
    )
    assert finding["mli_preliminary_finding"]["effective_from"] == (
        "2026-01-01"
    )


def test_fr_dividend_rates_and_legacy_refund() -> None:
    _, index = findings_index()

    finding = index["CZ-FR-DIV-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [0.0, 10.0]
    assert (
        finding["treaty_findings"][
            "legacy_refund_rule"
        ]["refund_treated_as_dividend"]
        is True
    )
    assert (
        finding["treaty_findings"][
            "legacy_refund_rule"
        ]["current_applicability_requires_confirmation"]
        is True
    )


def test_it_dividend_general_fifteen_percent() -> None:
    _, index = findings_index()

    finding = index["CZ-IT-DIV-LEGAL-REVIEW"]
    rates = finding["treaty_findings"]["rates"]

    assert [item["rate"] for item in rates] == [15.0]
    assert finding["treaty_findings"]["rate_scope"] == "general"
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
        "CZ-DE-ROY-LEGAL-REVIEW",
        "CZ-FR-DIV-LEGAL-REVIEW",
        "CZ-IT-DIV-LEGAL-REVIEW",
    ):
        finding = index[packet_id]

        assert finding["human_confirmation_required"] is True
        assert finding["review_outcome"] is None
        assert finding["status"] == "preliminary_findings_only"
