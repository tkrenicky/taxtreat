import taxtreat.tools.run_sk_prerelease_runtime_validation as runtime_validation


def test_offline_runtime_validation_pipeline_writes_manifest_matrix_and_readiness(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest_summary_path = tmp_path / "manifest-summary.json"
    matrix_path = tmp_path / "matrix-summary.json"
    readiness_path = tmp_path / "readiness.json"

    manifest = {
        "source_country": "SK",
        "policy": {"runtime_release": False},
        "scopes": [],
    }
    manifest_summary = {"scope_count": 225, "production_released_scopes": 0}
    matrix_summary = {
        "evaluated_scopes": 225,
        "review_required_scopes": 225,
        "final_rate_scopes": 0,
        "czech_runtime_fallback_scopes": 0,
        "production_released_scopes": 0,
        "fail_closed": True,
    }
    readiness = {
        "all_machine_evidence_ready": False,
        "blockers": ["official_2026_cooperating_state_list_body_not_ingested"],
        "human_review": {"started": False, "reviewed_scopes": 0, "may_start": False},
        "runtime": {"released": False, "production_released_scopes": 0},
    }

    monkeypatch.setattr(runtime_validation.manifest_module, "OUTPUT_PATH", manifest_path)
    monkeypatch.setattr(runtime_validation.manifest_module, "SUMMARY_PATH", manifest_summary_path)
    monkeypatch.setattr(runtime_validation.matrix_module, "SUMMARY_PATH", matrix_path)
    monkeypatch.setattr(runtime_validation.readiness_module, "OUTPUT_PATH", readiness_path)
    monkeypatch.setattr(runtime_validation.manifest_module, "build_manifest", lambda: manifest)
    monkeypatch.setattr(runtime_validation.manifest_module, "build_summary", lambda _: manifest_summary)
    monkeypatch.setattr(runtime_validation.matrix_module, "validate_matrix", lambda _: matrix_summary)
    monkeypatch.setattr(runtime_validation.readiness_module, "build_readiness", lambda: readiness)

    result = runtime_validation.run()

    assert result["offline"] is True
    assert result["network_fetches_performed"] is False
    assert result["decision_matrix"]["evaluated_scopes"] == 225
    assert result["decision_matrix"]["review_required_scopes"] == 225
    assert result["decision_matrix"]["final_rate_scopes"] == 0
    assert result["decision_matrix"]["czech_runtime_fallback_scopes"] == 0
    assert result["decision_matrix"]["production_released_scopes"] == 0
    assert result["readiness"]["blockers"] == [
        "official_2026_cooperating_state_list_body_not_ingested"
    ]
    assert manifest_path.is_file()
    assert manifest_summary_path.is_file()
    assert matrix_path.is_file()
    assert readiness_path.is_file()
