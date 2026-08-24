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
        "ÚDAJE PODLE DRUHU PŘÍJMU",
        "Ano, přímo",
        "K datu transakce alespoň 12 měsíců",
        "Je příjemce běžnou obchodní společností",
        "Podléhá příjemce ve státě své daňové rezidence běžné dani",
    ]
    for phrase in required:
        assert phrase in content


def test_payer_and_step_four_english_residue_is_explicitly_covered():
    script = DYNAMIC.read_text(encoding="utf-8")
    required = [
        '["Platby", "Payments"]',
        '["Stav", "Status"]',
        '["Aktivní", "Active"]',
        '["Připraven", "Ready"]',
        '["Nastavit jako aktivního", "Set as active"]',
        "DIČ",
        "GENERAL CZECH RATE WITHOUT EXEMPTION",
        "SECONDARY TREATY PROTECTION",
        "No Czech tax is remitted under this tax treatment",
        "For dividends, the obligation to withhold tax",
    ]
    for phrase in required:
        assert phrase in script


def test_english_amounts_use_czk_not_czech_kc_symbol():
    script = DYNAMIC.read_text(encoding="utf-8")
    assert r"\s*Kč$" in script
    assert '" CZK"' in script
    assert r"\s+CZK$" in script


def test_pe_question_is_income_specific_in_all_three_income_types():
    script = DYNAMIC.read_text(encoding="utf-8")
    assert "The holding giving rise to this dividend" in script
    assert "The debt-claim giving rise to this interest" in script
    assert "The right or property giving rise to these royalties" in script
    assert "Podíl, z něhož je dividenda vyplácena" in script
    assert "Pohledávka, z níž plyne tento úrok" in script
    assert "Právo nebo majetek, za který jsou placeny licenční poplatky" in script


def test_section_19_english_wording_does_not_present_exemption_as_zero_percent_rate():
    script = DYNAMIC.read_text(encoding="utf-8")
    assert "Czech withholding tax does not apply; treaty protection is secondary." in script
    assert '["Czech withholding tax is therefore 0%; treaty protection is secondary.",' in script


def test_austrian_treaty_excerpt_switch_uses_verified_english_articles_10_11_12():
    script = DYNAMIC.read_text(encoding="utf-8")
    assert "AT_TREATY_EN" in script
    assert '"10": `Article 10' in script
    assert '"11": `Article 11' in script
    assert '"12": `Article 12' in script
    assert "tax so charged shall not exceed 10 per cent of the gross amount of the dividends" in script
    assert "Interest arising in a Contracting State and beneficially owned by a resident of the other Contracting State shall be taxable only in that other State" in script
    assert "tax so charged shall not exceed 5 per cent of the gross amount of the royalties" in script
    assert 'excerpt.dataset.ttTreatyLanguage = "en-official"' in script
    assert "originalTreatyText" in script


def test_austrian_copyright_exclusive_result_never_highlights_unrelated_5_percent_clause():
    script = CANONICAL.read_text(encoding="utf-8")
    assert "isAtCopyrightExclusive" in script
    assert 'mark.legal-decisive-passage' in script
    assert "5% source-state limitation in Article 12(2) does not apply" in script
    assert "5% omezení zdanění ve státě zdroje podle čl. 12 odst. 2 neuplatní" in script
