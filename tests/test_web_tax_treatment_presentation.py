from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "app" / "web" / "source-country-context.js"
CLIENT = ROOT / "app" / "web" / "client-polish.js"


def test_generic_presentation_contract_has_four_distinct_non_rate_semantics():
    text = CONTEXT.read_text(encoding="utf-8")

    assert 'exclusive_foreign_taxation: Object.freeze({' in text
    assert 'domestic_exemption: Object.freeze({' in text
    assert 'outside_subject_of_tax: Object.freeze({' in text
    assert 'domestic_rate_applies: Object.freeze({' in text

    assert 'resultLabel: "Není předmětem daně"' in text
    assert 'rateLabel: "N/A"' in text

    # Genuine exemption remains a separate concept.
    assert 'resultLabel: "Osvobození"' in text
    assert 'rateLabel: "0 %"' in text

    # Treaty permission to tax at source without a treaty ceiling is not a 0% rule.
    assert 'resultLabel: "Smlouva sazbu neomezuje"' in text
    assert 'rateLabel: "Dle vnitrostátního práva"' in text


def test_client_uses_shared_tax_treatment_presentation_adapter():
    text = CLIENT.read_text(encoding="utf-8")

    assert "TaxTreatSourceCountries?.taxTreatmentPresentation" in text
    assert 'analysis?.tax_treatment === "outside_subject_of_tax"' in text


def test_outside_subject_never_displays_zero_percent():
    text = CLIENT.read_text(encoding="utf-8")

    assert '["Sazba srážkové daně", "N/A"]' in text
    assert '["Srážková daň k odvodu", "N/A"]' in text
    assert "Nejde o sazbu 0 % ani o osvobození" in text


def test_old_two_treatment_inline_mapping_is_removed():
    text = CLIENT.read_text(encoding="utf-8")

    assert (
        '["exclusive_foreign_taxation", "domestic_exemption"].includes(treatment)'
        not in text
    )


def test_source_country_api_exports_generic_treatment_presenter():
    text = CONTEXT.read_text(encoding="utf-8")

    assert "function taxTreatmentPresentation(treatment)" in text
    assert "taxTreatmentPresentation," in text
