from __future__ import annotations

from pathlib import Path

import taxtreat.countries.registry as country_registry
from taxtreat.countries.registry import CountryConfig
from taxtreat.services.calculation import (
    build_withholding_compliance_schedule,
    build_withholding_tax_calculation,
)
from taxtreat.services.reporting.country_copy import report_country_copy
from taxtreat.services.source_country_calculation import (
    build_source_country_withholding_compliance_schedule,
    build_source_country_withholding_tax_calculation,
)
from taxtreat.services.source_country_capabilities import source_country_capability


ROOT = Path(__file__).resolve().parents[1]
GENERIC_RUNTIME_FILES = (
    ROOT / "taxtreat" / "services" / "decision.py",
    ROOT / "taxtreat" / "services" / "source_country_calculation.py",
    ROOT / "taxtreat" / "services" / "source_country_release_gate.py",
    ROOT / "taxtreat" / "services" / "source_country_runtime_metadata.py",
    ROOT / "taxtreat" / "services" / "reporting" / "country_copy.py",
)


def _xt_config(*, runtime_released: bool = True) -> CountryConfig:
    return CountryConfig(
        code="XT",
        currency="XCU",
        supported_income_types=("dividend", "interest", "royalty"),
        treaty_partner_registry=None,
        runtime_released=runtime_released,
        fx_provider=None,
        domestic_legal_source_url="https://example.invalid/xt-tax-act",
        domestic_law_label="Synthetic Tax Act",
        compliance_form_code="XT-WHT",
        compliance_legal_reference="Synthetic Tax Act s. 10",
        compliance_periodicity="monthly",
    )


def test_third_country_registration_is_config_only(monkeypatch):
    monkeypatch.setitem(country_registry._COUNTRIES, "XT", _xt_config())

    assert country_registry.get_country_config("XT").code == "XT"
    assert "XT" in country_registry.supported_source_countries()

    capability = source_country_capability("XT")
    assert capability["code"] == "XT"
    assert capability["currency"] == "XCU"
    assert capability["runtime_released"] is True
    assert capability["domestic_law_label"] == "Synthetic Tax Act"


def test_third_country_default_calculation_and_compliance_need_no_core_branch(monkeypatch):
    monkeypatch.setitem(country_registry._COUNTRIES, "XT", _xt_config())

    amount = {"amount": "1000", "currency": "XCU"}
    direct_calculation = build_withholding_tax_calculation(
        amount,
        decision_status="FINAL",
        rate_percent=15,
    )
    routed_calculation = build_source_country_withholding_tax_calculation(
        "XT",
        amount,
        decision_status="FINAL",
        rate_percent=15,
    )
    assert routed_calculation == direct_calculation

    kwargs = dict(
        income_type="interest",
        decision_status="FINAL",
        rate_percent=15,
    )
    direct_schedule = build_withholding_compliance_schedule("2026-08-24", **kwargs)
    routed_schedule = build_source_country_withholding_compliance_schedule(
        "XT", "2026-08-24", **kwargs
    )
    assert routed_schedule == direct_schedule


def test_third_country_gets_safe_generic_report_copy(monkeypatch):
    monkeypatch.setitem(country_registry._COUNTRIES, "XT", _xt_config())

    copy = report_country_copy("XT")
    assert copy.source_country == "XT"
    assert copy.language == "en"
    assert copy.domestic_law_reference == "Synthetic Tax Act"
    assert copy.withholding_tax_label == "XT withholding tax"
    assert copy.transaction_labels["dividend"] == "Dividend payment"


def test_synthetic_country_does_not_leak_into_generic_runtime_source():
    for path in GENERIC_RUNTIME_FILES:
        text = path.read_text(encoding="utf-8")
        assert '== "XT"' not in text
        assert '!= "XT"' not in text
        assert '"XT":' not in text


def test_pre_release_third_country_is_governed_by_country_config(monkeypatch):
    monkeypatch.setitem(
        country_registry._COUNTRIES,
        "XT",
        _xt_config(runtime_released=False),
    )

    capability = source_country_capability("XT")
    assert capability["runtime_released"] is False
    assert capability["availability"] == "pre_release"
    assert capability["policy"]["final_analysis_allowed"] is False
