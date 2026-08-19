import pytest

import taxtreat.services.source_country_release_gate as gate_module
from taxtreat.countries.registry import CountryConfig
from taxtreat.services.source_country_release_gate import (
    SourceCountryNotReleasedError,
    UnsupportedSourceCountryError,
    require_source_country_analysis_release,
)


def test_sk_is_rejected_at_source_country_release_layer_before_analysis():
    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("sk")

    decision = exc_info.value.decision
    assert decision.source_country == "SK"
    assert decision.allowed is False
    assert decision.code == "SOURCE_COUNTRY_NOT_RELEASED"
    assert decision.release_status == "pre_release"
    assert "source_country_runtime_release_false" in decision.blockers
    assert "full_human_legal_review_not_completed" in decision.blockers


def test_runtime_flag_alone_cannot_release_sk(monkeypatch):
    real = gate_module.get_country_config("SK")
    monkeypatch.setattr(
        gate_module,
        "get_country_config",
        lambda code: CountryConfig(
            code=real.code,
            currency=real.currency,
            supported_income_types=real.supported_income_types,
            treaty_partner_registry=real.treaty_partner_registry,
            runtime_released=True,
            fx_provider=real.fx_provider,
            domestic_legal_source_url=real.domestic_legal_source_url,
            domestic_law_label=real.domestic_law_label,
            compliance_form_code=real.compliance_form_code,
            compliance_legal_reference=real.compliance_legal_reference,
            compliance_periodicity=real.compliance_periodicity,
        ),
    )

    with pytest.raises(SourceCountryNotReleasedError) as exc_info:
        require_source_country_analysis_release("SK")

    decision = exc_info.value.decision
    assert decision.allowed is False
    assert decision.code == "SOURCE_COUNTRY_RELEASE_EVIDENCE_INCOMPLETE"
    assert "release_manifest_not_eligible" in decision.blockers
    assert "country_specific_legal_source_gates_not_ready" in decision.blockers
    assert "full_human_legal_review_not_completed" in decision.blockers


def test_non_cz_release_requires_second_independent_evidence_gate(monkeypatch):
    real = gate_module.get_country_config("SK")
    monkeypatch.setattr(
        gate_module,
        "get_country_config",
        lambda code: CountryConfig(
            code=real.code,
            currency=real.currency,
            supported_income_types=real.supported_income_types,
            treaty_partner_registry=real.treaty_partner_registry,
            runtime_released=True,
            fx_provider=real.fx_provider,
            domestic_legal_source_url=real.domestic_legal_source_url,
            domestic_law_label=real.domestic_law_label,
            compliance_form_code=real.compliance_form_code,
            compliance_legal_reference=real.compliance_legal_reference,
            compliance_periodicity=real.compliance_periodicity,
        ),
    )
    calls = []

    decision = require_source_country_analysis_release(
        "SK",
        release_evidence_gate=lambda code: calls.append(code),
    )

    assert calls == ["SK"]
    assert decision.allowed is True


def test_cz_remains_released_and_can_delegate_to_existing_pair_gate():
    calls = []

    decision = require_source_country_analysis_release(
        "CZ",
        released_country_gate=lambda code: calls.append(code),
    )

    assert calls == ["CZ"]
    assert decision.allowed is True
    assert decision.code == "SOURCE_COUNTRY_RELEASED"
    assert decision.release_status == "released"
    assert decision.blockers == ()


def test_unknown_source_country_fails_closed():
    with pytest.raises(UnsupportedSourceCountryError):
        require_source_country_analysis_release("XX")
