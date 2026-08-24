import pytest

from taxtreat.tools.build_at_treaty_review_queue import build_review_queue


MACHINE = {
    "source_country": "AT",
    "status": "machine_source_inventory_not_reviewed",
    "records": [
        {
            "partner_label": "Exampleland / Example",
            "treaty_links": ["https://www.ris.bka.gv.at/example"],
            "mli_flag": True,
        },
        {
            "partner_label": "Otherland / Other",
            "treaty_links": ["https://www.ris.bka.gv.at/other"],
            "mli_flag": False,
        },
    ],
}


def test_review_queue_expands_each_treaty_to_three_income_scopes_fail_closed():
    queue = build_review_queue(MACHINE)

    assert queue["status"] == "review_queue_not_released"
    assert queue["treaty_partner_count"] == 2
    assert queue["scope_count"] == 6
    assert {row["income_type"] for row in queue["scopes"]} == {
        "dividend",
        "interest",
        "royalty",
    }
    assert all(row["release_eligible"] is False for row in queue["scopes"])
    assert all(row["rate_extraction"]["reviewed"] is False for row in queue["scopes"])


def test_review_queue_preserves_machine_mli_as_signal_not_legal_effect():
    queue = build_review_queue(MACHINE)
    example = next(row for row in queue["scopes"] if row["partner_label"].startswith("Exampleland"))

    assert example["machine_mli_flag"] is True
    assert example["mli"]["bilateral_matching_completed"] is False
    assert example["mli"]["wht_effective_date_completed"] is False
    assert example["mli"]["result_changing_effects"] == []


def test_review_queue_never_infers_rates_from_machine_treaty_inventory():
    queue = build_review_queue(MACHINE)

    for row in queue["scopes"]:
        rate = row["rate_extraction"]
        assert rate["article_number"] is None
        assert rate["base_rate_percent"] is None
        assert rate["qualifying_rate_percent"] is None
        assert rate["qualifying_conditions"] == []


def test_review_queue_requires_primary_instrument_chain_and_domestic_precedence_for_promotion():
    queue = build_review_queue(MACHINE)
    requirements = "\n".join(queue["promotion_requirements"])

    assert "current treaty instrument chain" in requirements
    assert "bilateral MLI matching" in requirements
    assert "withholding-tax effective date" in requirements
    assert "domestic-law precedence" in requirements


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"source_country": "SK", "status": "machine_source_inventory_not_reviewed", "records": [{}]}, "Expected Austrian"),
        ({"source_country": "AT", "status": "released", "records": [{}]}, "not in machine discovery state"),
        ({"source_country": "AT", "status": "machine_source_inventory_not_reviewed", "records": []}, "contains no records"),
    ],
)
def test_review_queue_fails_closed_on_invalid_machine_input(payload, message):
    with pytest.raises(ValueError, match=message):
        build_review_queue(payload)
