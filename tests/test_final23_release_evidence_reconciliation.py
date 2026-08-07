import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "final23_release_evidence_reconciliation.json"
)


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_reconciliation_covers_18_clean_pairs():
    data = load()

    assert data["pair_count"] == 18
    assert len(data["records"]) == 18
    assert data["release_gate_count"] == 16


def test_existing_evidence_closes_supported_gates():
    data = load()

    for row in data["records"]:
        gate = row["release_gate"]

        assert gate["official_document_hash_verified"] is True
        assert gate["protocol_inventory_complete"] is True
        assert gate["protocol_overlay_verified"] is True
        assert gate["mli_status_verified"] is True
        assert gate["mli_overlay_verified"] is True
        assert gate["withholding_effective_date_verified"] is True


def test_unproven_source_and_rule_gates_remain_open():
    data = load()

    open_gates = {
        "official_source_identity_verified",
        "clean_text_verified",
        "article_10_verified",
        "article_11_verified",
        "article_12_verified",
        "authentic_languages_verified",
        "prevailing_language_rule_verified",
        "official_english_version_assessed",
        "legal_rule_mapping_verified",
        "end_to_end_tests_passed",
    }

    for row in data["records"]:
        assert set(row["remaining_release_gates"]) == open_gates
        assert row["completed_gate_count"] == 6
        assert row["remaining_gate_count"] == 10


def test_reconciliation_remains_fail_closed():
    data = load()

    assert data["released_pair_count"] == 0
    assert data["production_ready_count"] == 0
    assert data["fail_closed"] is True

    for row in data["records"]:
        assert row["release_status"] == "blocked"
        assert row["legal_text_verified"] is False
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True
