import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "final23_source_identity_verification.json"
)


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_source_identity_verified_for_all_18():
    data = load()

    assert data["pair_count"] == 18
    assert data["verified_source_identity_count"] == 18

    for row in data["records"]:
        assert (
            row["official_source_identity_verified"]
            is True
        )
        assert row["authority_class"] == "official"
        assert row["source_title"]
        assert row["official_urls"]
        assert len(row["artifact_sha256"]) == 64


def test_source_identity_closes_seventh_gate():
    data = load()

    for row in data["records"]:
        assert row["release_gate"][
            "official_source_identity_verified"
        ] is True

        assert row["completed_gate_count"] == 7
        assert row["remaining_gate_count"] == 9


def test_legal_text_gates_remain_open():
    data = load()

    for row in data["records"]:
        gate = row["release_gate"]

        assert gate["clean_text_verified"] is False
        assert gate["article_10_verified"] is False
        assert gate["article_11_verified"] is False
        assert gate["article_12_verified"] is False

        assert row["release_status"] == "blocked"
        assert row["legal_text_verified"] is False
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True
