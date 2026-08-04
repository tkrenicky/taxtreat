import json

import pytest

from taxtreat.pipeline import release


def test_committed_baseline_manifest_is_honest_and_consistent():
    source_manifest = release.build_source_manifest()
    legal_registry = release.build_legal_registry()
    manifest = release.validate_release()

    assert len(source_manifest["sources"]) == 100
    assert all(
        source["source_id"].startswith("SRC-")
        for source in source_manifest["sources"]
    )
    assert len(legal_registry["scopes"]) == 300
    assert sum(
        scope["review_ready"] for scope in legal_registry["scopes"]
    ) == 6
    assert sum(
        scope["scope_status"] == "pending_consolidation"
        for scope in legal_registry["scopes"]
    ) == 294
    assert manifest["parser"] == {
        "datasets": 100,
        "relevant_articles": 300,
        "structurally_complete": True,
    }
    assert manifest["sources"]["auditability"] == "blocked"
    assert manifest["legal"]["verified_scopes"] == 0
    assert manifest["legal"]["review_ready_scopes"] == 6
    assert manifest["legal"]["pending_consolidation_scopes"] == 294
    assert manifest["legal"]["instrument_inventory_partners"] == 100
    assert manifest["legal"]["base_candidate_scopes"] == 294
    assert manifest["legal"]["base_candidate_scopes_with_rates"] == 293
    assert manifest["legal"]["base_candidate_scopes_without_rates"] == 1
    assert manifest["legal"]["base_candidate_no_numeric_cap_scopes"] == 1
    assert manifest["legal"]["base_candidate_unresolved_scopes"] == 0
    assert manifest["legal"]["protocol_effect_candidate_documents"] == 12
    assert manifest["legal"]["protocol_effect_candidate_partners"] == 11
    assert manifest["legal"]["protocol_effect_candidate_scopes"] == 33
    assert manifest["legal"]["domestic_candidate_scopes"] == 300
    assert manifest["legal"]["remaining_domestic_candidate_scopes"] == 294
    assert manifest["legal"]["eu_relief_candidate_partners"] == 30
    assert manifest["legal"]["eu_relief_candidate_scopes"] == 90
    assert manifest["legal"]["remaining_eu_relief_candidate_scopes"] == 84
    assert manifest["legal"]["instrument_chain_candidate_scopes"] == 294
    assert manifest["legal"]["instrument_chain_assembled_scopes"] == 294
    assert manifest["legal"]["instrument_chain_blocked_scopes"] == 0
    assert manifest["legal"]["instrument_chain_blocked_partners"] == 0
    assert manifest["legal"]["mli_wht_effect_candidate_partners"] == 64
    assert manifest["legal"]["remaining_mli_wht_effect_candidate_partners"] == 62
    assert manifest["legal"]["mli_no_current_effect_determinations"] == 7
    assert manifest["legal"]["status_instrument_candidate_partners"] == 2
    assert manifest["legal"]["resolved_instrument_chain_blocker_scopes"] == 34
    assert manifest["legal"]["candidate_review_packets"] == 294
    assert manifest["legal"]["candidate_review_awaiting_primary"] == 294
    assert (
        manifest["legal"]["candidate_review_awaiting_independent_approval"]
        == 0
    )
    assert manifest["legal"]["candidate_review_independently_approved"] == 0
    assert manifest["legal"]["candidate_review_approval_eligible"] == 0
    assert manifest["legal"]["candidate_review_promotable"] == 0
    assert manifest["golden_cases"] == 8
    assert manifest["production_ready"] is False
    assert len(manifest["manifest_sha256"]) == 64


def test_production_release_gate_fails_closed():
    with pytest.raises(RuntimeError, match="Production gate failed"):
        release.validate_release(production=True)


def test_release_manifest_files_are_valid_json():
    release.build_source_manifest()
    release.build_legal_registry()
    release.build_release_manifest()
    for path in (
        release.SOURCE_MANIFEST,
        release.LEGAL_REGISTRY,
        release.RELEASE_MANIFEST,
    ):
        assert json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("missing", "must cover 294 scopes"),
        ("scope_drift", "does not match the instrument-chain scopes"),
        ("stale_hash", "has a stale candidate hash"),
    ],
)
def test_release_registry_rejects_invalid_review_queue(
    monkeypatch,
    tmp_path,
    mutation,
    match,
):
    payload = json.loads(release.REVIEW_QUEUE.read_text(encoding="utf-8"))
    if mutation == "missing":
        payload["packets"].pop()
    elif mutation == "scope_drift":
        payload["packets"][0]["recipient_country"] = "AT"
    else:
        payload["packets"][0]["candidate_sha256"] = "0" * 64
    target = tmp_path / "review-queue.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(release, "REVIEW_QUEUE", target)

    with pytest.raises(ValueError, match=match):
        release.build_legal_registry()
