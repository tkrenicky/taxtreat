from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "data" / "legal_reviews" / "sk_outbound"

ADJUDICATION = SK / "mli_bilateral_adjudication_2026.json"
MACHINE = SK / "mli_notice_machine_extraction.json"
COVERAGE = SK / "human_review_coverage.json"

POSITIVE = {
    "BE", "NL", "IN", "IL", "IE", "ZA", "CA",
    "KZ", "DE", "SI", "RS", "ES", "TN",
}

NEGATIVE = {"KR", "LU", "GB", "VN"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_mli_adjudication_covers_all_46_relationships():
    data = load(ADJUDICATION)
    assert data["relationship_count"] == 46
    assert len(data["relationships"]) == 46
    assert len({
        r["recipient_country"]
        for r in data["relationships"]
    }) == 46


def test_article_8_exact_positive_population():
    data = load(ADJUDICATION)
    actual = {
        r["recipient_country"]
        for r in data["relationships"]
        if r["article_8_365_day_test_applies"]
    }
    assert actual == POSITIVE
    assert data["article_8_match_count"] == 13
    assert set(data["article_8_match_countries"]) == POSITIVE


def test_article_8_known_false_positives_stay_negative():
    data = load(ADJUDICATION)
    rows = {
        r["recipient_country"]: r
        for r in data["relationships"]
    }

    for country in NEGATIVE:
        assert not rows[country]["article_8_365_day_test_applies"]
        assert "8" not in rows[country]["applied_mli_articles"]
        assert "8" not in rows[country]["result_changing_articles"]


def test_adjudication_is_byte_semantically_aligned_with_machine():
    adjudication = load(ADJUDICATION)
    machine = load(MACHINE)

    a = {
        r["recipient_country"]: r
        for r in adjudication["relationships"]
    }
    m = {
        r["recipient_country"]: r
        for r in machine["relationships"]
    }

    assert set(a) == set(m)

    for country in a:
        assert a[country]["slovak_notice"] == m[country]["slovak_notice"]
        assert (
            a[country]["wht_effective_dates"]
            == m[country]["wht_effective_dates"]
        )
        assert (
            a[country]["applied_mli_articles"]
            == m[country]["applied_mli_articles"]
        )
        assert (
            a[country]["result_changing_articles"]
            == m[country]["candidate_result_changing_articles"]
        )


def test_error_classification_is_human_review_not_machine():
    data = load(ADJUDICATION)

    assert (
        data["policy"]["machine_extraction_discrepancy_count"]
        == 0
    )
    assert (
        data["policy"][
            "prior_human_review_interpretation_correction_count"
        ]
        == 4
    )

    assert {
        r["recipient_country"]
        for r in data["prior_human_review_corrections"]
    } == NEGATIVE

    assert all(
        r["machine_extraction_was_correct"]
        for r in data["prior_human_review_corrections"]
    )


def test_human_review_coverage_points_to_mli_adjudication():
    coverage = load(COVERAGE)
    mli = coverage["mli_post_review_adjudication"]

    assert mli["relationship_count"] == 46
    assert mli["article_8_match_count"] == 13
    assert set(mli["article_8_match_countries"]) == POSITIVE
    assert (
        set(mli["explicit_article_8_negative_regressions"])
        == NEGATIVE
    )
    assert mli["machine_extraction_discrepancies"] == 0
    assert (
        mli["prior_human_review_interpretation_corrections"]
        == 4
    )
    assert mli["final_reviewer_reconfirmation_required"] is False
    assert mli["final_reviewer_reconfirmation_completed"] is True
    assert (
        mli["final_reviewer_reconfirmation_evidence"]
        == "mli_final_reconfirmation_packet_2026.json"
    )
