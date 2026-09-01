from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "data" / "legal_reviews" / "sk_outbound"

MANIFEST = SK / "source_country_release_manifest.json"
COVERAGE = SK / "human_review_coverage.json"
ADJUDICATION = SK / "mli_bilateral_adjudication_2026.json"

POSITIVE = {
    "BE", "NL", "IN", "IL", "IE", "ZA", "CA",
    "KZ", "DE", "SI", "RS", "ES", "TN",
}
NEGATIVE = {"KR", "LU", "GB", "VN"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_release_manifest_points_to_completed_46_pair_adjudication():
    manifest = load(MANIFEST)

    assert manifest["mli_bilateral_adjudication_ready"] is True
    assert (
        manifest["mli_bilateral_adjudication_evidence"]
        == "mli_bilateral_adjudication_2026.json"
    )
    assert manifest["mli_relationships_adjudicated"] == 46
    assert manifest["mli_article_8_match_count"] == 13


def test_review_interpretation_error_is_not_machine_error():
    manifest = load(MANIFEST)
    adjudication = load(ADJUDICATION)

    assert manifest["mli_machine_extraction_discrepancies"] == 0
    assert (
        manifest["mli_prior_human_review_interpretation_corrections"]
        == 4
    )
    assert (
        adjudication["policy"]["machine_extraction_discrepancy_count"]
        == 0
    )


def test_corrected_mli_population_is_locked():
    adjudication = load(ADJUDICATION)

    assert set(adjudication["article_8_match_countries"]) == POSITIVE
    assert (
        set(adjudication["article_8_negative_regression_countries"])
        == NEGATIVE
    )


def test_mli_reconfirmation_and_full_structured_coverage_allow_source_country_release():
    manifest = load(MANIFEST)
    coverage = load(COVERAGE)

    mli = coverage["mli_post_review_adjudication"]

    assert mli["final_reviewer_reconfirmation_required"] is False
    assert mli["final_reviewer_reconfirmation_completed"] is True
    assert (
        mli["final_reviewer_reconfirmation_evidence"]
        == "mli_final_reconfirmation_packet_2026.json"
    )

    assert manifest["release_eligible"] is True
    assert manifest["release_status"] == "released"
    assert manifest["blockers"] == []
    assert manifest["structured_treaty_rule_materialization"]["structured_scope_coverage"] == 225
    assert manifest["structured_treaty_rule_materialization"]["rule_level_fail_closed"] is True

    assert (
        manifest["mli_final_reviewer_reconfirmation_required"]
        is False
    )
    assert (
        manifest["mli_final_reviewer_reconfirmation_completed"]
        is True
    )


def test_existing_225_scope_coverage_is_preserved():
    manifest = load(MANIFEST)

    assert manifest["expected_scope_count"] == 225
    assert manifest["legal_review_covered_scopes"] == 225
    assert manifest["human_reviewed_scopes"] == 24
    assert manifest["pattern_reconciled_scopes"] == 201
