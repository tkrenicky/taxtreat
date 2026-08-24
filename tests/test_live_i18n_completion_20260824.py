from pathlib import Path


BOOTSTRAP = Path("app/web/workspace-report-export.js")
CANONICAL = Path("app/web/workspace-canonical-live-i18n-20260824.js")
DYNAMIC = Path("app/web/workspace-canonical-live-i18n-dynamic-20260824.js")


def test_final_i18n_passes_are_loaded_after_income_visibility_fix():
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    visibility = bootstrap.index("workspace-income-type-visibility-fix-20260824.js")
    canonical = bootstrap.index("workspace-canonical-live-i18n-20260824.js")
    dynamic = bootstrap.index("workspace-canonical-live-i18n-dynamic-20260824.js")
    report_core = bootstrap.index("workspace-report-export-core.js")
    assert visibility < canonical < dynamic < report_core


def test_final_i18n_passes_do_not_add_broad_mutation_observer():
    assert "MutationObserver" not in CANONICAL.read_text(encoding="utf-8")
    assert "MutationObserver" not in DYNAMIC.read_text(encoding="utf-8")


def test_language_button_drives_underlying_language_state():
    script = CANONICAL.read_text(encoding="utf-8")
    assert '#taxtreat-language-controls .tt-lang-mini button[data-lang]' in script
    assert 'localStorage.setItem(UI_KEY, lang)' in script
    assert 'select.dispatchEvent(new Event("change", { bubbles: true }))' in script


def test_recipient_profile_and_document_strings_are_covered():
    content = CANONICAL.read_text(encoding="utf-8") + DYNAMIC.read_text(encoding="utf-8")
    required = [
        "Skutečný vlastník příjmu",
        "Vazba ke stálé provozovně v ČR",
        "Skutečný vlastník",
        "Vazba na stálou provozovnu",
        "Podíl na plátci",
        "Datum nabytí podílu",
        "Potvrzení o daňovém rezidentství",
        "Zatím nebylo bezpečně uloženo.",
        "profilové údaje vyplněny",
    ]
    for phrase in required:
        assert phrase in content


def test_step_two_and_step_three_strings_are_covered():
    content = CANONICAL.read_text(encoding="utf-8") + DYNAMIC.read_text(encoding="utf-8")
    required = [
        "Komu je placeno?",
        "Pokračovat k platbě →",
        "Druh příjmu *",
        "Doplňující údaje pro možné vnitrostátní osvobození",
        "Předmět licenční platby",
        "Autorské dílo",
        "Odpovídá výše úroku běžným tržním podmínkám?",
    ]
    for phrase in required:
        assert phrase in content


def test_austrian_copyright_exclusive_result_never_highlights_unrelated_5_percent_clause():
    script = CANONICAL.read_text(encoding="utf-8")
    assert "isAtCopyrightExclusive" in script
    assert 'mark.legal-decisive-passage' in script
    assert "5% source-state limitation in Article 12(2) does not apply" in script
    assert "5% omezení zdanění ve státě zdroje podle čl. 12 odst. 2 neuplatní" in script
