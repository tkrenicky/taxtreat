import json
from pathlib import Path

ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)


def load(name):
    return json.loads(
        (ROOT / name).read_text(
            encoding="utf-8"
        )
    )


def test_pack_covers_clean_candidates():
    payload = load(
        "clean_candidate_article_pack.json"
    )

    assert payload[
        "treaty_partner_count"
    ] == 23

    assert len(
        payload["treaty_partners"]
    ) == 23

    assert len({
        row["treaty_pair_id"]
        for row in payload[
            "treaty_partners"
        ]
    }) == 23


def test_every_partner_has_explicit_article_status():
    payload = load(
        "clean_candidate_article_pack.json"
    )

    allowed = {
        "candidate_articles_extracted",
        "article_mapping_incomplete",
        "article_text_empty",
    }

    for row in payload[
        "treaty_partners"
    ]:
        assert (
            row["extraction_status"]
            in allowed
        )
        assert row["required_review"]
        assert row["fail_closed"] is True
        assert row["production_ready"] is False


def test_extracted_articles_have_hashes():
    payload = load(
        "clean_candidate_article_pack.json"
    )

    for row in payload[
        "treaty_partners"
    ]:
        if row["extraction_status"] != (
            "candidate_articles_extracted"
        ):
            continue

        assert set(row["articles"]) == {
            "10",
            "11",
            "12",
        }

        for article in row[
            "articles"
        ].values():
            assert article[
                "character_count"
            ] > 0
            assert article["text_sha256"]


def test_pack_remains_fail_closed():
    payload = load(
        "clean_candidate_article_pack.json"
    )

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload[
        "production_ready"
    ] is False

    assert payload[
        "fail_closed"
    ] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False


def test_summary_matches_pack():
    payload = load(
        "clean_candidate_article_pack.json"
    )

    summary = load(
        "clean_candidate_article_pack_summary.json"
    )

    assert summary[
        "treaty_partner_count"
    ] == 23

    assert sum(
        summary[
            "extraction_status_counts"
        ].values()
    ) == 23
