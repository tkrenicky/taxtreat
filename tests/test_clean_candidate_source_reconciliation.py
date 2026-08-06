import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]

REVIEW_ROOT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

OUTPUT = (
    REVIEW_ROOT
    / "clean_candidate_source_reconciliation.json"
)

SUMMARY = (
    REVIEW_ROOT
    / "clean_candidate_source_reconciliation_summary.json"
)


def load(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_reconciliation_builder_runs():
    subprocess.run(
        [
            sys.executable,
            "-m",
            (
                "taxtreat.tools."
                "build_clean_candidate_source_reconciliation"
            ),
        ],
        cwd=ROOT,
        check=True,
    )

    assert OUTPUT.is_file()
    assert SUMMARY.is_file()


def test_reconciliation_covers_all_candidates():
    payload = load(OUTPUT)

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


def test_candidate_artifact_hashes_are_valid():
    payload = load(OUTPUT)

    for row in payload["treaty_partners"]:
        assert (
            row[
                "candidate_artifact_exists"
            ]
            is True
        )

        assert (
            row["candidate_hash_valid"]
            is True
        )


def test_article_hashes_are_preserved():
    payload = load(OUTPUT)

    for row in payload["treaty_partners"]:
        assert set(
            row[
                "candidate_article_hashes"
            ]
        ) == {"10", "11", "12"}

        for digest in row[
            "candidate_article_hashes"
        ].values():
            assert len(digest) == 64


def test_all_results_remain_fail_closed():
    payload = load(OUTPUT)

    for row in payload["treaty_partners"]:
        assert (
            row[
                "official_source_identity_verified"
            ]
            is False
        )

        assert (
            row[
                "official_document_content_verified"
            ]
            is False
        )

        assert (
            row[
                "articles_10_12_legally_verified"
            ]
            is False
        )

        assert row["production_ready"] is False
        assert row["fail_closed"] is True

        assert (
            row[
                "promotable_to_active_rules"
            ]
            is False
        )


def test_only_identical_artifacts_are_reusable():
    payload = load(OUTPUT)

    for row in payload["treaty_partners"]:
        expected = (
            row["hash_relation"]
            == "identical"
        )

        assert (
            row[
                "existing_article_extraction_reusable"
            ]
            is expected
        )

        assert (
            row[
                "requires_fresh_official_extraction"
            ]
            is (not expected)
        )


def test_summary_matches_payload():
    payload = load(OUTPUT)
    summary = load(SUMMARY)

    assert (
        summary[
            "treaty_partner_count"
        ]
        == 23
    )

    assert sum(
        summary[
            "reconciliation_status_counts"
        ].values()
    ) == 23

    assert sum(
        summary[
            "hash_relation_counts"
        ].values()
    ) == 23
