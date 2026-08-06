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
    / "clean_candidate_text_quality_audit.json"
)

SUMMARY = (
    REVIEW_ROOT
    / "clean_candidate_text_quality_audit_summary.json"
)


def load(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_quality_audit_builder_runs():
    subprocess.run(
        [
            sys.executable,
            "-m",
            (
                "taxtreat.tools."
                "build_clean_candidate_text_quality_audit"
            ),
        ],
        cwd=ROOT,
        check=True,
    )

    assert OUTPUT.is_file()
    assert SUMMARY.is_file()


def test_quality_audit_covers_23_partners():
    payload = load(OUTPUT)

    assert payload[
        "treaty_partner_count"
    ] == 23

    assert payload[
        "article_scope_count"
    ] == 69

    assert len(
        payload["treaty_partners"]
    ) == 23


def test_every_partner_uses_official_artifact():
    payload = load(OUTPUT)

    for row in payload["treaty_partners"]:
        assert (
            row[
                "official_artifact_identical"
            ]
            is True
        )


def test_all_articles_have_quality_results():
    payload = load(OUTPUT)

    for row in payload["treaty_partners"]:
        assert set(
            row["article_results"]
        ) == {"10", "11", "12"}

        for article in row[
            "article_results"
        ].values():
            assert len(
                article["text_sha256"]
            ) == 64

            assert (
                article[
                    "clean_text_verified"
                ]
                is False
            )


def test_audit_never_promotes_legal_text():
    payload = load(OUTPUT)

    for row in payload["treaty_partners"]:
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


def test_summary_counts_match():
    payload = load(OUTPUT)
    summary = load(SUMMARY)

    assert sum(
        summary[
            "partner_status_counts"
        ].values()
    ) == 23

    assert (
        summary["article_scope_count"]
        == 69
    )
