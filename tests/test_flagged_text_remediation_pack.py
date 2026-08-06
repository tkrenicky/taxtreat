import json
from pathlib import Path

ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

PACK = ROOT / "flagged_text_remediation_pack.json"
SUMMARY = (
    ROOT
    / "flagged_text_remediation_pack_summary.json"
)


def load(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_pack_contains_all_flagged_partners():
    payload = load(PACK)

    assert payload[
        "treaty_partner_count"
    ] == 5

    assert {
        row["treaty_pair_id"]
        for row in payload["treaty_partners"]
    } == {
        "CZ-AD",
        "CZ-BW",
        "CZ-GH",
        "CZ-KR",
        "CZ-QA",
    }


def test_every_entry_has_actionable_findings():
    payload = load(PACK)

    for partner in payload["treaty_partners"]:
        assert partner["articles"]

        for article in partner["articles"]:
            assert article["findings"]

            assert article[
                "required_action"
            ] == "compare_with_official_artifact"

            assert (
                article["comparison_completed"]
                is False
            )

            assert (
                article["clean_text_verified"]
                is False
            )


def test_pack_never_applies_automatic_correction():
    payload = load(PACK)

    assert payload["semantics"][
        "automatic_text_replacement_allowed"
    ] is False

    for partner in payload["treaty_partners"]:
        assert partner["production_ready"] is False
        assert partner["fail_closed"] is True

        for article in partner["articles"]:
            assert article["corrected_text"] is None

            assert (
                article[
                    "corrected_text_sha256"
                ]
                is None
            )


def test_andorra_contains_error_findings():
    payload = load(PACK)

    andorra = next(
        row
        for row in payload["treaty_partners"]
        if row["treaty_pair_id"] == "CZ-AD"
    )

    assert andorra["total_error_count"] == 2

    codes = {
        finding["code"]
        for article in andorra["articles"]
        for finding in article["findings"]
    }

    assert "isolated_ocr_pipe" in codes
    assert "broken_article_reference" in codes


def test_summary_matches_pack():
    payload = load(PACK)
    summary = load(SUMMARY)

    assert summary[
        "treaty_partner_count"
    ] == len(payload["treaty_partners"])

    assert summary[
        "article_scope_count"
    ] == sum(
        len(row["articles"])
        for row in payload["treaty_partners"]
    )
