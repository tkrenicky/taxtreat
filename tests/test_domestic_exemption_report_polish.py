from taxtreat.services.reporting.domestic_exemption_polish import apply_domestic_exemption_polish


def _report(language="cs"):
    return {
        "scope": {
            "source_country": "CZ",
            "recipient_country": "AT",
            "income_type": "dividend",
        },
        "result": {
            "status": "FINAL",
            "tax_treatment": "domestic_exemption",
            "rate": 0,
        },
        "assumptions": {
            "transaction_facts": {
                "__report_language": language,
            }
        },
        "official_sources": [
            {
                "legal_layer": "treaty",
                "article": "10",
                "source_url": "https://example.invalid/treaty",
            }
        ],
    }


def _html():
    return """<!doctype html><html><head></head><body>
    <div class="key-fact"><span>Použitá sazba</span><b>0 %</b></div>
    <article class="card result-card">
      <span class="kicker">Sazba české srážkové daně</span>
      <div class="rate">0 %</div>
      <div class="basis-row"><span>Vnitrostátní sazba</span><b>15 %</b></div>
      <div class="basis-row"><span>Smluvní sazba</span><b>0 %</b></div>
      <div class="basis-row"><span>Použitý právní základ</span><b>čl. 10 smlouvy</b></div>
      <div class="conclusion">Podle čl. 10 se daň neuplatní.</div>
      <div class="path-note">Výchozí sazba 15 % → 0 %.</div>
    </article>
    <div class="calc-row"><span>Použitá sazba</span><b>0 %</b></div>
    <div class="flow-node"><b>Konečná sazba</b><p>0 %</p></div>
    <article class="legal-source"><span class="kicker">Použité právní pravidlo</span><div class="quote">Treaty excerpt</div></article>
    <div class="hierarchy-note"><b>Jak se pravidla vzájemně vztahují</b>Old hierarchy.</div>
    </body></html>"""


def test_domestic_exemption_is_not_presented_as_zero_percent_rate():
    polished = apply_domestic_exemption_polish(_html(), _report())
    assert '<div class="rate tt-exemption-result">Neuplatňuje se</div>' in polished
    assert "Daňový režim" in polished
    assert "Osvobození podle § 19 ZDP" in polished
    assert "Použitý právní základ</span><b>§ 19 ZDP" in polished
    assert "PRIMÁRNÍ ČESKÝ PRÁVNÍ ZÁKLAD" not in polished  # primary card uses report-template kicker
    assert "§ 19 ZDP — vnitrostátní osvobození podílu na zisku" in polished
    assert "SEKUNDÁRNÍ SMLUVNÍ OCHRANA" in polished
    assert "smlouva není primárním právním titulem" in polished


def test_english_domestic_exemption_has_english_primary_basis_and_official_treaty_link():
    polished = apply_domestic_exemption_polish(_html(), _report("en"))
    assert "Section 19 of the Czech Income Taxes Act — domestic dividend exemption" in polished
    assert "Czech withholding tax therefore does not apply" in polished
    assert "SECONDARY TREATY PROTECTION" in polished
    assert "Official English synthesised Austria–Czech treaty text" in polished
