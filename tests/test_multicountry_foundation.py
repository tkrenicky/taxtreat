from taxtreat.countries.registry import (
    get_country_config,
    supported_source_countries,
)
from taxtreat.registry.legal_scope import (
    expected_legal_scopes,
    load_partner_registry,
    supported_scope_keys,
)


def test_country_registry_exposes_cz_and_fail_closed_sk():
    assert supported_source_countries() == ("CZ", "SK")

    cz = get_country_config("CZ")
    sk = get_country_config("SK")

    assert cz.runtime_released is True
    assert cz.currency == "CZK"
    assert cz.fx_provider == "CNB"

    assert sk.runtime_released is True
    assert sk.currency == "EUR"
    assert sk.treaty_partner_registry is not None
    assert sk.treaty_partner_registry.name == "sk_treaty_partners.json"
    assert sk.fx_provider == "ECB/NBS"
    assert sk.domestic_law_label == "zákon č. 595/2003 Z. z."
    assert "/2003/595/20260101.print.html" in sk.domestic_legal_source_url
    assert "e-sbirka" not in sk.domestic_legal_source_url
    assert sk.compliance_form_code == "OZN4311v26"
    assert sk.compliance_legal_reference == "§ 43 ods. 11"
    assert sk.compliance_periodicity == "monthly"


def test_existing_cz_treaty_scope_inventory_remains_300():
    scopes = expected_legal_scopes(source_country="CZ")
    keys = supported_scope_keys(source_country="CZ")

    assert len(scopes) == 300
    assert len(keys) == 300
    assert all(scope["source_country"] == "CZ" for scope in scopes)


def test_sk_official_treaty_inventory_exposes_75_partners_and_225_scopes():
    partners = load_partner_registry(source_country="SK")
    scopes = expected_legal_scopes(source_country="SK")
    keys = supported_scope_keys(source_country="SK")

    assert len(partners) == 75
    assert len({partner["iso2"] for partner in partners}) == 75
    assert {partner["iso2"] for partner in partners}.issuperset({"CZ", "TW", "US"})

    assert len(scopes) == 225
    assert len(keys) == 225
    assert all(scope["source_country"] == "SK" for scope in scopes)
