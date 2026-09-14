import pytest

from taxtreat.tools.build_at_mli_bilateral_review_queue import build_mli_review_queue


INVENTORY = {
    "source_country": "AT",
    "status": "machine_source_inventory_not_reviewed",
    "records": [
        {
            "partner_label": "MLIland / MLIland",
            "release_universe_candidate": True,
            "mli_flag": True,
            "treaty_links": ["https://www.ris.bka.gv.at/mli"],
        },
        {
            "partner_label": "NoMLI / NoMLI",
            "release_universe_candidate": True,
            "mli_flag": False,
            "treaty_links": ["https://www.ris.bka.gv.at/no-mli"],
        },
        {
            "partner_label": "Future / Future",
            "release_universe_candidate": False,
            "mli_flag": True,
            "treaty_links": ["https://www.ris.bka.gv.at/future"],
        },
    ],
}


def test_queue_contains_only_current_mli_flagged_relationships_and_releases_nothing():
    queue = build_mli_review_queue(INVENTORY)

    assert queue["schema_version"] == 2
    assert queue["status"] == "bilateral_mli_review_queue_not_adjudicated"
    assert queue["wht_scope"] == "article_7_ppt_and_pair_specific_withholding_effective_date_only"
    assert queue["relationship_count"] == 1
    row = queue["relationships"][0]
    assert row["partner_label"] == "MLIland / MLIland"
    assert row["partner_mli_party_status_verified"] is False
    assert row["partner_cta_notification_verified"] is False
    assert row["wht_overlay"]["article_7_ppt"]["bilateral_match_resolved"] is False
    assert row["wht_overlay"]["article_8_dividend_transfer_transactions"] == {
        "austria_position": "reserved_in_full",
        "applicable": False,
        "result_changing_effects": [],
    }
    assert row["article_35"]["withholding_tax_effective_date_resolved"] is False
    assert row["article_35"]["withholding_tax_effective_date"] is None
    assert row["release_eligible"] is False


def test_queue_does_not_treat_machine_mli_flag_as_bilateral_effect():
    row = build_mli_review_queue(INVENTORY)["relationships"][0]

    assert row["austria_machine_mli_flag"] is True
    assert row["wht_overlay"]["article_7_ppt"]["result_changing_effects"] == []
    assert row["wht_overlay"]["other_rate_changing_articles"] == []
    assert row["bilateral_adjudication_completed"] is False


def test_queue_explicitly_prevents_article_8_holding_period_branch():
    queue = build_mli_review_queue(INVENTORY)
    constraints = "\n".join(queue["release_constraints"])
    assert "reserved Article 8 in full" in constraints
    assert "365-day" in constraints


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"source_country": "SK", "status": "machine_source_inventory_not_reviewed", "records": []}, "Expected Austrian"),
        ({"source_country": "AT", "status": "released", "records": []}, "not in discovery state"),
        ({"source_country": "AT", "status": "machine_source_inventory_not_reviewed", "records": []}, "No current Austrian MLI"),
    ],
)
def test_queue_fails_closed_on_invalid_input(payload, message):
    with pytest.raises(ValueError, match=message):
        build_mli_review_queue(payload)


def test_queue_rejects_flagged_relationship_without_partner_label():
    inventory = {
        "source_country": "AT",
        "status": "machine_source_inventory_not_reviewed",
        "records": [{"release_universe_candidate": True, "mli_flag": True, "treaty_links": []}],
    }
    with pytest.raises(ValueError, match="without partner label"):
        build_mli_review_queue(inventory)
