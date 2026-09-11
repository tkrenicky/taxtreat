from pathlib import Path


SCRIPT = Path("app/web/workspace-locale-state-preservation-20260908.js")


def test_locale_switch_captures_state_before_canonical_route_navigation():
    script = SCRIPT.read_text(encoding="utf-8")

    assert 'const STORAGE_KEY = "taxtreat-locale-transition-state-v3"' in script
    assert 'document.addEventListener("pointerdown", captureForLanguageControl, true)' in script
    assert 'event.target?.closest?.("#taxtreat-language-controls [data-lang]")' in script
    assert 'sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))' in script
    assert 'activeView === "flow"' in script
    assert 'activeStep === "4"' in script


def test_result_step_is_recomputed_in_target_locale_instead_of_repainting_dom():
    script = SCRIPT.read_text(encoding="utf-8")

    assert "function rerunResult(state)" in script
    assert "form.requestSubmit(submit)" in script
    assert "if (cancelled || !state.rerunResult) return" in script
    assert "rerunResult(state)" in script
    assert "window.location.pathname ===" in script
    assert "/ui/${currentLocale}" in script
    assert "refreshDependencies()" in script
    assert "restoreFields(state)" in script

    # The canonical /ui/cs and /ui/en routes own localization. Reintroducing
    # a delayed live text-node translator would recreate the production race.
    assert "scheduleLiveRestore" not in script
    assert "translateResidue" not in script
    assert "createTreeWalker" not in script
