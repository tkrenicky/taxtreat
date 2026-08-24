from pathlib import Path


SCRIPT = Path("app/web/workspace-live-language-and-ir-layout-20260824.js")
BOOTSTRAP = Path("app/web/workspace-report-export.js")


def test_live_language_script_is_loaded():
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    assert "workspace-live-language-and-ir-layout-20260824.js" in bootstrap


def test_live_language_switch_drives_real_ui_select():
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'document.querySelector("#taxtreat-ui-language")' in script
    assert 'select.dispatchEvent(new Event("change", { bubbles:true }))' in script
    assert 'localStorage.setItem(UI_LANGUAGE_KEY, lang)' in script
    assert '#taxtreat-language-controls .tt-lang-mini button[data-lang]' in script


def test_interest_and_royalty_facts_are_stacked():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "#interest-facts" in script
    assert "#royalty-facts" in script
    assert "grid-template-columns:1fr!important" in script


def test_ir_exemption_notice_moves_after_legal_sources():
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'step.querySelector("#workspace-citations")' in script
    assert "sourcesCard.after(notice)" in script
    assert "#cz-ir-exemption-notice" in script


def test_new_script_does_not_add_broad_dom_observer():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "MutationObserver" not in script
