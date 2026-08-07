import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

INDEX = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "final23_source_verification_index.json"
)


def load():
    return json.loads(INDEX.read_text(encoding="utf-8"))


def test_final23_index_covers_exactly_23_pairs():
    data = load()

    assert data["pair_count"] == 23
    assert len(data["records"]) == 23
    assert len({
        row["treaty_pair_id"]
        for row in data["records"]
    }) == 23


def test_no_final23_pair_is_prematurely_production_ready():
    data = load()

    assert data["production_ready_count"] == 0

    assert all(
        row["active_rule_allowed"] is False
        for row in data["records"]
    )


def test_expected_source_verification_categories():
    counts = load()["verification_category_counts"]

    assert counts["clean_candidate_verification_required"] == 18
    assert counts["source_remediation_required"] == 3
    assert counts["status_instrument_special_handling"] == 1
    assert counts["status_blocked"] == 1


def test_russia_and_belarus_remain_explicit():
    rows = {
        row["treaty_pair_id"]: row
        for row in load()["records"]
    }

    assert rows["CZ-RU"]["verification_category"] == "status_blocked"
    assert rows["CZ-BY"]["verification_category"] == (
        "status_instrument_special_handling"
    )
