from dataclasses import replace
from datetime import date

import pytest

import app.sk_prerelease as sk_api
import taxtreat.services.reporting.calculation_context as report_calc
from taxtreat.countries.registry import get_country_config
from taxtreat.countries.sk import evaluate_domestic_precedence
from taxtreat.services.source_country_release_gate import (
    SourceCountryNotReleasedError,
    SourceCountryReleaseDecision,
)


def test_sk_domestic_precedence_non_dividend_falls_through():
    assert evaluate_domestic_precedence(
        recipient_country="AT",
        income_type="interest",
        transaction_date=date(2026, 8, 23),
        facts={},
    ) is None


def test_sk_prerelease_release_gate_serializes_closed_decision(monkeypatch):
    decision = SourceCountryReleaseDecision(
        source_country="SK",
        allowed=False,
        code="SOURCE_COUNTRY_NOT_RELEASED",
        release_status="pre_release",
        blockers=("synthetic_blocker",),
    )

    def closed(_code):
        raise SourceCountryNotReleasedError(decision)

    monkeypatch.setattr(sk_api, "require_source_country_analysis_release", closed)
    payload = sk_api.sk_prerelease_release_gate()

    assert payload == {
        "source_country": "SK",
        "allowed": False,
        "code": "SOURCE_COUNTRY_NOT_RELEASED",
        "release_status": "pre_release",
        "blockers": ["synthetic_blocker"],
    }


def test_report_net_helper_covers_explicit_missing_and_invalid_values():
    assert report_calc._net("100", "10", "77") == "77"
    assert report_calc._net(None, "10", None) is None
    assert report_calc._net("bad", "10", None) is None
    assert report_calc._net("100", "10", None) == 90.0


def test_report_calculation_context_rejects_unknown_strategy(monkeypatch):
    real = get_country_config("SK")
    monkeypatch.setattr(
        report_calc,
        "get_country_config",
        lambda code: replace(real, report_calculation_strategy="unknown"),
    )

    with pytest.raises(ValueError, match="Unsupported report calculation strategy"):
        report_calc.build_report_calculation_context(
            source_country="SK",
            calculation={"status": "CALCULATED"},
            currency="EUR",
        )
