import json
from pathlib import Path

PATH = Path(
    "data/legal_reviews/global_cz_outbound/"
    "final23_semantic_release_reconciliation.json"
)

def load():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_all_54_scopes_reconciled():
    data = load()

    assert data["summary"]["scope_count"] == 54
    assert len(data["records"]) == 54

def test_all_scopes_remain_non_active():
    data = load()

    assert data["production_ready"] is False
    assert data["fail_closed"] is True
    assert data["summary"]["active_rule_allowed_count"] == 0
    assert data["summary"]["production_ready_count"] == 0

    for row in data["records"]:
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True

def test_semantic_candidates_have_text_and_hash():
    data = load()

    for row in data["records"]:
        if not row["semantic_mapping_complete"]:
            continue

        assert row["candidate_rates"]

        for candidate in row["candidate_rates"]:
            assert candidate["evidence_level"] == "semantic_rate_candidate"
            assert candidate["rate"] is not None
            assert candidate["legal_basis"]
            assert candidate["source_text"]
            assert candidate["source_text_sha256"]
            assert len(candidate["source_text_sha256"]) == 64

def test_verified_mapping_requires_no_release_blockers():
    data = load()

    for row in data["records"]:
        if row["legal_rule_mapping_verified"]:
            assert row["release_blockers"] == []
            assert row["semantic_mapping_complete"] is True
            assert row["source_identity_verified"] is True
            assert row["country_level_legal_review_verified"] is True
            assert all(row["primary_release_gates"].values())

def test_language_gates_do_not_get_silently_promoted():
    data = load()

    for row in data["records"]:
        assert set(row["language_gates"]) == {
            "authentic_languages_verified",
            "prevailing_language_rule_verified",
            "official_english_version_assessed",
        }
