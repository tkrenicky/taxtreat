import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "remaining_13_primary_treaty_review_batch.json"
)

EXPECTED = {
    "CZ-CL",
    "CZ-CY",
    "CZ-ET",
    "CZ-GB",
    "CZ-HK",
    "CZ-JP",
    "CZ-LU",
    "CZ-PA",
    "CZ-PL",
    "CZ-RW",
    "CZ-SM",
    "CZ-SN",
    "CZ-XK",
}


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_remaining_partners_are_included():
    payload = load()

    assert payload[
        "treaty_partner_count"
    ] == 13

    assert payload[
        "article_scope_count"
    ] == 39

    assert {
        row["treaty_pair_id"]
        for row in payload["treaty_partners"]
    } == EXPECTED


def test_every_partner_contains_articles_10_to_12():
    payload = load()

    for partner in payload["treaty_partners"]:
        assert {
            row["article_number"]
            for row in partner["articles"]
        } == {10, 11, 12}

        for article in partner["articles"]:
            assert len(
                article["article_text_sha256"]
            ) == 64

            assert article[
                "primary_text_extracted"
            ] is True

            assert article[
                "primary_text_legally_verified"
            ] is False


def test_candidate_findings_preserve_evidence():
    payload = load()

    assert payload[
        "candidate_rate_finding_count"
    ] > 0

    for partner in payload["treaty_partners"]:
        for article in partner["articles"]:
            for finding in article[
                "candidate_rate_findings"
            ]:
                assert isinstance(
                    finding["rate_percent"],
                    (int, float),
                )

                assert finding["source_form"]
                assert finding["excerpt"]

                assert finding[
                    "candidate_only"
                ] is True

                assert finding[
                    "legally_verified"
                ] is False


def test_entire_batch_remains_fail_closed():
    payload = load()

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False

    for partner in payload["treaty_partners"]:
        assert partner[
            "transaction_decision_ready"
        ] is False

        assert partner[
            "production_ready"
        ] is False

        assert partner["fail_closed"] is True
