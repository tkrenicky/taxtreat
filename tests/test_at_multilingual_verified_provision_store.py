import json
from pathlib import Path


STORE = Path("data/legal_texts/at_verified_provisions.json")


def test_at_multilingual_verified_provision_store_is_fail_closed_before_legal_selection():
    data = json.loads(STORE.read_text(encoding="utf-8"))

    assert data["schema_version"] == 1
    assert data["source_country"] == "AT"
    assert data["status"] == "multilingual_verified_provision_store_not_released"
    assert data["required_languages"] == ["de", "en"]
    assert data["provisions"] == {}
    assert data["release_state"] == {
        "verified_provision_count": 0,
        "german_provision_count": 0,
        "english_provision_count": 0,
        "translated_english_provision_count": 0,
        "step4_wording_released": False,
    }

    policy = data["materialization_policy"]
    assert policy["controlling_text_selected_required"] is True
    assert policy["language_authority_review_completed_required"] is True
    assert policy["official_source_sha256_required"] is True
    assert policy["canonical_text_sha256_required"] is True
    assert policy["machine_translation_must_not_be_marked_authentic"] is True
    assert policy["translated_english_must_reference_selected_source_text_sha256"] is True
    assert policy["step4_web_wording_release_requires_persistent_record"] is True
    assert policy["automatic_machine_candidate_materialization_forbidden"] is True
