from taxtreat.services.source_country_capabilities import (
    source_country_capabilities,
    source_country_capability,
)


def test_source_country_catalog_exposes_released_cz_and_prerelease_sk():
    payload = source_country_capabilities()

    assert payload["released_source_countries"] == ["CZ"]
    assert payload["pre_release_source_countries"] == ["SK"]
    assert [row["code"] for row in payload["countries"]] == ["CZ", "SK"]


def test_cz_capability_preserves_current_production_contract():
    cz = source_country_capability("CZ")

    assert cz["currency"] == "CZK"
    assert cz["runtime_released"] is True
    assert cz["availability"] == "released"
    assert cz["fx_provider"] == "CNB"
    assert cz["policy"]["final_analysis_allowed"] is True


def test_sk_capability_is_slovak_specific_and_fail_closed():
    sk = source_country_capability("SK")

    assert sk["currency"] == "EUR"
    assert sk["runtime_released"] is False
    assert sk["availability"] == "pre_release"
    assert sk["fx_provider"] is None
    assert "595/2003" in sk["domestic_law_label"]
    assert "slov-lex.sk" in sk["domestic_legal_source_url"]
    assert sk["compliance"] == {
        "form_code": "OZN4311v26",
        "legal_reference": "§ 43 ods. 11",
        "periodicity": "monthly",
    }
    assert sk["policy"]["czech_fallback_allowed"] is False
    assert sk["policy"]["final_analysis_allowed"] is False
