from pathlib import Path

from taxtreat.services.source_country_capabilities import (
    source_country_capabilities,
    source_country_capability,
)


def test_source_country_catalog_exposes_released_cz_and_sk():
    payload = source_country_capabilities()

    assert payload["released_source_countries"] == ["CZ", "SK"]
    assert payload["pre_release_source_countries"] == []
    assert [row["code"] for row in payload["countries"]] == ["CZ", "SK"]


def test_cz_capability_preserves_current_production_contract():
    cz = source_country_capability("CZ")

    assert cz["currency"] == "CZK"
    assert cz["runtime_released"] is True
    assert cz["availability"] == "released"
    assert cz["fx_provider"] == "CNB"
    assert cz["policy"]["czech_fallback_allowed"] is True
    assert cz["policy"]["final_analysis_allowed"] is True


def test_sk_capability_is_slovak_specific_and_released():
    sk = source_country_capability("SK")

    assert sk["currency"] == "EUR"
    assert sk["runtime_released"] is True
    assert sk["availability"] == "released"
    assert sk["fx_provider"] == "ECB/NBS"
    assert "595/2003" in sk["domestic_law_label"]
    assert "slov-lex.sk" in sk["domestic_legal_source_url"]
    assert sk["compliance"] == {
        "form_code": "OZN4311v26",
        "legal_reference": "§ 43 ods. 11",
        "periodicity": "monthly",
    }
    assert sk["policy"]["czech_fallback_allowed"] is False
    assert sk["policy"]["final_analysis_allowed"] is True


def test_capability_layer_has_no_country_code_branching():
    source = (
        Path(__file__).resolve().parents[1]
        / "taxtreat"
        / "services"
        / "source_country_capabilities.py"
    ).read_text(encoding="utf-8")

    assert 'config.code == "CZ"' not in source
    assert 'config.code == "SK"' not in source
