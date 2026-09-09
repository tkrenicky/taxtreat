from pathlib import Path


SCRIPT = Path("app/web/workspace-locale-state-preservation-20260908.js")


def test_delayed_locale_restore_is_cancelled_by_explicit_navigation():
    script = SCRIPT.read_text(encoding="utf-8")

    assert "function cancelStaleRestoreForNavigation(event)" in script
    assert (
        '"[data-nav],[data-flow-step],[data-next-step],[data-start-flow],#workspace-submit"'
        in script
    )
    assert "liveRestoreToken += 1" in script
    assert "pendingLiveState = null" in script
    assert "sessionStorage.removeItem(STORAGE_KEY)" in script
    assert (
        'document.addEventListener("click", cancelStaleRestoreForNavigation, true)'
        in script
    )


def test_reload_and_live_locale_restoration_share_the_cancellable_scheduler():
    script = SCRIPT.read_text(encoding="utf-8")
    restore_state = script.split("function restoreState()", 1)[1].split(
        "function scheduleLiveRestore(state)", 1
    )[0]

    assert "scheduleLiveRestore(state)" in restore_state
    assert "window.setTimeout(() => applyState(state)" not in restore_state
