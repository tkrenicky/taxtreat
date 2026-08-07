import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "final23_clean_verification_evidence.json"
)


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_evidence_bridge_covers_all_18_clean_pairs():
    data = load()

    assert data["pair_count"] == 18
    assert len(data["records"]) == 18


def test_all_clean_candidates_match_verified_artifacts():
    data = load()

    assert data[
        "artifact_identity_confirmed_count"
    ] == 18

    assert data[
        "fresh_extraction_required_count"
    ] == 0

    for row in data["records"]:
        assert row["evidence"][
            "official_artifact_identical_to_candidate"
        ] is True

        assert row["evidence"][
            "candidate_artifact_hash_verified"
        ] is True

        assert row["evidence"][
            "official_artifact_hash_verified"
        ] is True

        assert row["evidence"][
            "existing_article_extraction_reusable"
        ] is True


def test_country_legal_review_exists_for_all_18():
    data = load()

    assert data[
        "country_legal_review_complete_count"
    ] == 18

    for row in data["records"]:
        assert row["evidence"][
            "country_level_legal_review_complete"
        ] is True

        assert row["evidence"][
            "subsequent_instrument_review_present"
        ] is True


def test_bridge_does_not_prematurely_release_sources():
    data = load()

    assert data["production_ready_count"] == 0
    assert data["fail_closed"] is True

    for row in data["records"]:
        assert row["legal_text_verified"] is False
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True
        assert row["remaining_release_gates"]
