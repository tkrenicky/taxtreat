from pathlib import Path

import scripts.build_sk_claude_review_bundle as bundle


def test_claude_bundle_requires_real_generated_review_artifacts():
    names = {
        path.name
        for path in bundle.REQUIRED_GENERATED_ARTIFACTS
    }

    assert "prerelease_runtime_manifest.json" in names
    assert "prerelease_runtime_manifest_summary.json" in names
    assert "prerelease_decision_matrix_summary.json" in names
    assert "pre_review_readiness.json" in names
    assert "treaty_article_machine_extraction.json" in names
    assert "treaty_semantic_candidates.json" in names
    assert "mli_notice_machine_extraction.json" in names
    assert "prerelease_decision_matrix.json" not in names


def test_claude_bundle_builder_is_fail_closed_and_does_not_stage_generated_data():
    source = Path(bundle.__file__).read_text(encoding="utf-8")

    assert 'if not path.is_file()' in source
    assert '"evaluated_scopes": 225' in source
    assert '"review_required_scopes": 225' in source
    assert '"final_rate_scopes": 0' in source
    assert '"czech_runtime_fallback_scopes": 0' in source
    assert 'human review to remain 0/225' in source
    assert 'runtime to remain unreleased' in source
    assert 'git", "diff", "--binary", "main...HEAD"' in source
    assert "git add" not in source
    assert "git commit" not in source
    assert "git push" not in source
