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
