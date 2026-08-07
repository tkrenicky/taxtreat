import json
from pathlib import Path

PATH = Path(
    "data/legal_reviews/global_cz_outbound/"
    "final23_mapping_release_verification.json"
)

def load():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_all_54_scopes_are_assessed():
    data = load()

    assert data["summary"]["scope_count"] == 54
    assert len(data["records"]) == 54

def test_numeric_candidates_are_not_treated_as_verified_mapping():
    data = load()

    for row in data["records"]:
        if row["rate_evidence_mode"] == "numeric_candidates_only":
            assert row["semantic_mapping_complete"] is False
            assert row["legal_rule_mapping_verified"] is False
            assert "semantic_rate_mapping_incomplete" in row["release_blockers"]

def test_verified_mapping_requires_no_blockers():
    data = load()

    for row in data["records"]:
        if row["legal_rule_mapping_verified"]:
            assert row["semantic_mapping_complete"] is True
            assert row["release_blockers"] == []

def test_mapping_verification_still_does_not_activate_rules():
    data = load()

    assert data["production_ready"] is False
    assert data["fail_closed"] is True
    assert data["summary"]["active_rule_allowed_count"] == 0
    assert data["summary"]["production_ready_count"] == 0

    for row in data["records"]:
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True
