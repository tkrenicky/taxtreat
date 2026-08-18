from taxtreat.countries.registry import (
    get_country_config,
    supported_source_countries,
)
from taxtreat.registry.legal_scope import (
    expected_legal_scopes,
    supported_scope_keys,
)


def test_country_registry_exposes_cz_and_fail_closed_sk():
    assert supported_source_countries() == ("CZ", "SK")

    cz = get_country_config("CZ")
    sk = get_country_config("SK")

    assert cz.runtime_released is True
    assert cz.currency == "CZK"
    assert cz.fx_provider == "CNB"

    assert sk.runtime_released is False
    assert sk.currency == "EUR"
    assert sk.treaty_partner_registry is None


def test_existing_cz_treaty_scope_inventory_remains_300():
    scopes = expected_legal_scopes(source_country="CZ")
    keys = supported_scope_keys(source_country="CZ")

    assert len(scopes) == 300
    assert len(keys) == 300
    assert all(scope["source_country"] == "CZ" for scope in scopes)


def test_sk_does_not_invent_treaty_scopes_before_onboarding():
    assert expected_legal_scopes(source_country="SK") == []
    assert supported_scope_keys(source_country="SK") == set()
