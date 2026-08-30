from pathlib import Path

import scripts.build_sk_claude_review_pass2_followup_bundle as bundle


def test_followup_bundle_targets_visible_workspace_root_only():
    assert bundle.VISIBLE_WORKSPACE_ROOT == Path("/workspaces/taxtreat")
    source = Path(bundle.__file__).read_text(encoding="utf-8")
    assert "taxtreat-sk-claude-review-pass2-followup-" in source
    assert "VISIBLE_WORKSPACE_ROOT /" in source
    assert "artifacts/taxtreat-sk-claude-review" not in source


def test_followup_bundle_requires_validated_runtime_and_browser_invariants():
    source = Path(bundle.__file__).read_text(encoding="utf-8")

    assert '"evaluated_scopes": 225' in source
    assert '"review_required_scopes": 225' in source
    assert '"final_rate_scopes": 0' in source
    assert '"czech_runtime_fallback_scopes": 0' in source
    assert '"foreign_runtime_dependency_scopes": 0' in source
    assert "BROWSER_SMOKE_OK" in source
    assert "return require_source_country_analysis_release(source)" in source
    assert "source_country_runtime_dataset_version(" in source
    assert "build_source_country_withholding_tax_calculation(" in source
    assert "build_source_country_withholding_compliance_schedule(" in source
    assert "SOURCE_COUNTRY_RELEASE_GATE_MISSING" in source
    assert "app/main.py has uncommitted changes" in source
