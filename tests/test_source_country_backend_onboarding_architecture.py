from pathlib import Path

from taxtreat.countries.registry import (
    get_country_config,
    supported_source_countries,
)


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "taxtreat" / "services" / "decision.py"
REGISTRY = ROOT / "taxtreat" / "countries" / "registry.py"
SK_PACKAGE = ROOT / "taxtreat" / "countries" / "sk.py"


def test_sk_runtime_behavior_is_registered_in_country_config():
    config = get_country_config("SK")

    assert config.domestic_precedence_handler is not None
    assert config.release_manifest_path is not None
    assert config.release_manifest_path.name == (
        "source_country_release_manifest.json"
    )


def test_cz_does_not_inherit_sk_release_manifest_or_domestic_handler():
    config = get_country_config("CZ")

    assert config.domestic_precedence_handler is None
    assert config.release_manifest_path is None


def test_canonical_decision_has_no_direct_sk_branching():
    text = DECISION.read_text(encoding="utf-8")

    assert 'source_country != "SK"' not in text
    assert 'source_country == "SK"' not in text
    assert 'request.source_country != "SK"' not in text
    assert 'request.source_country == "SK"' not in text
    assert "_evaluate_sk_dividend" not in text
    assert "SK_RELEASE_MANIFEST" not in text


def test_country_specific_sk_domestic_logic_lives_in_country_package():
    text = SK_PACKAGE.read_text(encoding="utf-8")

    assert "def evaluate_domestic_precedence(" in text
    assert "§ 12 ods. 7 písm. c)" in text
    assert "OUTSIDE_SUBJECT_OF_TAX" in text


def test_registry_is_backend_runtime_registration_point():
    text = REGISTRY.read_text(encoding="utf-8")

    assert "domestic_precedence_handler" in text
    assert "release_manifest_path" in text
    assert "evaluate_sk_domestic_precedence" in text

    assert supported_source_countries() == ("CZ", "SK")


def test_new_country_contract_can_be_config_only_for_default_runtime():
    # Countries with no special domestic terminal handler and no
    # country-specific release manifest can use the canonical engine
    # without adding branches to decision.py. Country-specific behavior
    # is opt-in through CountryConfig.
    cz = get_country_config("CZ")

    assert cz.domestic_precedence_handler is None
    assert cz.release_manifest_path is None
