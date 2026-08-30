from pathlib import Path

import scripts.build_sk_claude_review_pass2_bundle as bundle


def test_pass2_bundle_targets_second_review_and_repo_root():
    source = Path(bundle.__file__).read_text(encoding="utf-8")

    assert "CLAUDE_ADVERSARIAL_REVIEW_PASS2.md" in source
    assert "CLAUDE_PASS1_FINDINGS_SUMMARY.md" in source
    assert "foreign_runtime_dependency_scopes" in source
    assert "czech_runtime_fallback_scopes" in source
    assert 'output = ROOT / f"taxtreat-sk-claude-review-pass2-' in source
    assert "BROWSER_SMOKE_OK" in source
    assert "git add" not in source
    assert "git commit" not in source
    assert "git push" not in source


def test_pass2_review_brief_requires_omitted_first_pass_coverage():
    brief = bundle.PASS2_BRIEF.read_text(encoding="utf-8")

    assert "Slovak domestic dividends" in brief
    assert "Slovak interest and royalties" in brief
    assert "MLI — systematic review" in brief
    assert "Compliance" in brief
    assert "UI/report — rendered-behavior review" in brief
    assert "FINDING-001" in brief
    assert "FINDING-003" in brief
    assert "all 46 MLI relationships" in brief
    assert "all 225 scopes" in brief
