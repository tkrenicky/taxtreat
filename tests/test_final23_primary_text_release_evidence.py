import json
from pathlib import Path


ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

PATH = ROOT / "final23_primary_text_release_evidence.json"


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


VERIFIED = {
    "CZ-AD",
    "CZ-BA",
    "CZ-BB",
    "CZ-BH",
    "CZ-BW",
    "CZ-CM",
    "CZ-CO",
    "CZ-GH",
    "CZ-KR",
    "CZ-QA",
}


def test_primary_text_release_split():
    data = load()

    assert data["pair_count"] == 18
    assert data["primary_text_verified_pair_count"] == 18
    assert data["primary_text_pending_pair_count"] == 0


def test_verified_pairs_close_four_text_gates():
    data = load()

    for row in data["records"]:
        gate = row["release_gate"]

        if row["treaty_pair_id"] not in VERIFIED:
            continue

        assert row["primary_text_release_verified"] is True

        assert gate["clean_text_verified"] is True
        assert gate["article_10_verified"] is True
        assert gate["article_11_verified"] is True
        assert gate["article_12_verified"] is True

        assert row["completed_gate_count"] == 11
        assert row["remaining_gate_count"] == 5

        assert set(row["article_evidence"]) == {
            "10", "11", "12"
        }

        for evidence in row["article_evidence"].values():
            assert evidence["hash_match"] is True
            assert (
                evidence["verification_status"]
                == "primary_treaty_text_verified"
            )


def test_every_pair_has_all_primary_text_gates():
    data = load()

    for row in data["records"]:
        gate = row["release_gate"]

        assert row["primary_text_release_verified"] is True
        assert gate["clean_text_verified"] is True
        assert gate["article_10_verified"] is True
        assert gate["article_11_verified"] is True
        assert gate["article_12_verified"] is True

        assert row["completed_gate_count"] == 11
        assert row["remaining_gate_count"] == 5


def test_every_pair_remains_fail_closed():
    data = load()

    for row in data["records"]:
        assert row["release_status"] == "blocked"
        assert row["active_rule_allowed"] is False
        assert row["production_ready"] is False
        assert row["fail_closed"] is True
