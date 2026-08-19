from __future__ import annotations

from datetime import date

from taxtreat.tools.build_sk_domestic_review_readiness import (
    build_readiness,
    cooperating_state_status,
    withholding_rate_candidate,
)


def _source(codes):
    return {
        "official_list": {
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
        },
        "cooperating_state_codes": codes,
    }


def _domestic():
    return {
        "common": {
            "standard_withholding_rate_percent": 19,
            "non_cooperative_state_rate_percent": 35,
        }
    }


def test_incomplete_official_list_blocks_non_cooperative_classification():
    result = cooperating_state_status(
        recipient_country="US",
        transaction_date=date(2026, 8, 19),
        source=_source(None),
    )
    assert result["status"] == "blocked_official_annual_list_body_not_ingested"
    assert result["is_cooperating_state"] is None
    assert result["is_non_cooperative_state"] is None


def test_transaction_date_outside_list_validity_blocks_classification():
    result = cooperating_state_status(
        recipient_country="US",
        transaction_date=date(2027, 1, 1),
        source=_source(["US"]),
    )
    assert result["status"] == "blocked_no_valid_annual_list_for_transaction_date"
    assert result["is_non_cooperative_state"] is None


def test_complete_positive_list_drives_19_or_35_candidate():
    source = _source(["AT", "US"])

    cooperating = withholding_rate_candidate(
        recipient_country="US",
        transaction_date=date(2026, 8, 19),
        source=source,
        domestic=_domestic(),
    )
    assert cooperating["is_cooperating_state"] is True
    assert cooperating["domestic_wht_rate_candidate"] == 19

    non_cooperating = withholding_rate_candidate(
        recipient_country="XX",
        transaction_date=date(2026, 8, 19),
        source=source,
        domestic=_domestic(),
    )
    assert non_cooperating["is_non_cooperative_state"] is True
    assert non_cooperating["domestic_wht_rate_candidate"] == 35


def test_incomplete_list_never_defaults_to_35_percent():
    result = withholding_rate_candidate(
        recipient_country="XX",
        transaction_date=date(2026, 8, 19),
        source=_source(None),
        domestic=_domestic(),
    )
    assert result["domestic_wht_rate_candidate"] is None
    assert result["rate_status"] == "blocked"


def test_current_repository_model_has_complete_2026_list_but_is_not_released():
    payload = build_readiness()
    assert payload["policy"]["non_treaty_partner_does_not_equal_non_cooperative_state"] is True
    assert payload["policy"]["35_percent_rate_requires_resolved_non_cooperative_status"] is True
    assert payload["policy"]["incomplete_positive_list_blocks_rate_selection"] is True
    assert payload["cooperating_state_list"]["ingestion_complete"] is True
    assert payload["review_ready"] is True
    assert payload["approval_eligible"] is False
    assert payload["runtime_status"] == "not_released"
