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

PACK_PATH = (
    REVIEW_ROOT
    / "flagged_text_remediation_pack.json"
)

SUMMARY_PATH = (
    REVIEW_ROOT
    / "flagged_text_remediation_pack_summary.json"
)

AUDIT_PATH = (
    REVIEW_ROOT
    / "clean_candidate_text_quality_audit.json"
)


def load(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_builder_runs():
    subprocess.run(
        [
            sys.executable,
            "-m",
            (
                "taxtreat.tools."
                "build_flagged_text_remediation_pack"
            ),
        ],
        cwd=ROOT,
        check=True,
    )

    assert PACK_PATH.is_file()
    assert SUMMARY_PATH.is_file()


def test_pack_matches_current_audit():
    pack = load(PACK_PATH)
    audit = load(AUDIT_PATH)

    expected = {
        row["treaty_pair_id"]
        for row in audit["treaty_partners"]
        if (
            row["quality_status"]
            != "automated_quality_gate_passed"
        )
    }

    actual = {
        row["treaty_pair_id"]
        for row in pack["treaty_partners"]
    }

    assert actual == expected
    assert pack["treaty_partner_count"] == len(expected)


def test_pack_contains_all_audit_findings():
    pack = load(PACK_PATH)
    audit = load(AUDIT_PATH)

    pack_findings = {
        (
            partner["treaty_pair_id"],
            article["article_number"],
            finding["code"],
            finding["offset"],
        )
        for partner in pack["treaty_partners"]
        for article in partner["articles"]
        for finding in article["findings"]
    }

    audit_findings = {
        (
            partner["treaty_pair_id"],
            int(article_number),
            finding["code"],
            finding["offset"],
        )
        for partner in audit["treaty_partners"]
        for article_number, article in (
            partner["article_results"].items()
        )
        for finding in article["findings"]
    }

    assert pack_findings == audit_findings


def test_confirmed_findings_are_removed():
    payload = load(PACK_PATH)

    assert payload["treaty_partner_count"] == 0
    assert payload["article_scope_count"] == 0
    assert payload["finding_count"] == 0
    assert payload["treaty_partners"] == []

    assert payload["legal_verification_completed"] is False
    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True
    assert payload["promotable_to_active_rules"] is False


def test_no_automatic_corrections_are_applied():
    pack = load(PACK_PATH)

    assert (
        pack["semantics"][
            "automatic_text_replacement_allowed"
        ]
        is False
    )

    assert pack["production_ready"] is False
    assert pack["fail_closed"] is True

    for partner in pack["treaty_partners"]:
        assert partner["production_ready"] is False
        assert partner["fail_closed"] is True

        for article in partner["articles"]:
            assert article["corrected_text"] is None

            assert (
                article["corrected_text_sha256"]
                is None
            )

            assert (
                article["comparison_completed"]
                is False
            )

            assert (
                article["clean_text_verified"]
                is False
            )

            assert (
                article["legal_text_verified"]
                is False
            )


def test_summary_matches_pack():
    pack = load(PACK_PATH)
    summary = load(SUMMARY_PATH)

    assert (
        summary["treaty_partner_count"]
        == len(pack["treaty_partners"])
    )

    assert (
        summary["article_scope_count"]
        == sum(
            len(partner["articles"])
            for partner in pack[
                "treaty_partners"
            ]
        )
    )

    assert (
        summary["finding_count"]
        == sum(
            len(article["findings"])
            for partner in pack[
                "treaty_partners"
            ]
            for article in partner["articles"]
        )
    )
