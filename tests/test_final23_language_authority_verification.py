import json
from pathlib import Path

PATH = Path(
    "data/legal_reviews/global_cz_outbound/"
    "final23_language_authority_verification.json"
)

def load():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_language_dataset_has_18_clean_pairs():
    data = load()

    assert len(data["records"]) == 18
    assert data["summary"]["pair_count"] == 18

def test_language_evidence_remains_gate_specific():
    data = load()

    by_pair = {
        row["treaty_pair_id"]: row
        for row in data["records"]
    }

    assert by_pair["CZ-KR"]["release_gates"] == {
        "authentic_languages_verified": True,
        "official_english_version_assessed": True,
        "prevailing_language_rule_verified": True,
    }

    assert by_pair["CZ-BH"]["release_gates"] == {
        "authentic_languages_verified": False,
        "official_english_version_assessed": True,
        "prevailing_language_rule_verified": True,
    }

    assert by_pair["CZ-LU"]["release_gates"] == {
        "authentic_languages_verified": False,
        "official_english_version_assessed": True,
        "prevailing_language_rule_verified": False,
    }

    assert by_pair["CZ-GH"]["language_authority_complete"] is False
    assert by_pair["CZ-JP"]["language_authority_complete"] is False

def test_no_language_gap_is_promoted_to_release():
    data = load()

    assert data["production_ready"] is False
    assert data["fail_closed"] is True

    for row in data["records"]:
        assert row["fail_closed"] is True
