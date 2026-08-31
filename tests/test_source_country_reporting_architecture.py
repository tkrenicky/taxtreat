from pathlib import Path

from taxtreat.countries.registry import get_country_config
from taxtreat.services.reporting.calculation_context import (
    build_report_calculation_context,
)


ROOT = Path(__file__).resolve().parents[1]


def test_report_strategies_are_country_configured():
    cz = get_country_config("CZ")
    sk = get_country_config("SK")

    assert cz.report_calculation_strategy == "czk"
    assert sk.report_calculation_strategy == "payment_currency_eur"

    assert cz.html_localization_strategy == "cz"
    assert sk.html_localization_strategy == "sk"


def test_client_report_has_no_direct_sk_calculation_branch():
    text = (
        ROOT
        / "taxtreat"
        / "services"
        / "reporting"
        / "client_report.py"
    ).read_text(encoding="utf-8")

    assert 'source_country == "SK"' not in text


def test_html_localization_has_no_country_code_dispatch():
    text = (
        ROOT
        / "taxtreat"
        / "services"
        / "reporting"
        / "html_localization.py"
    ).read_text(encoding="utf-8")

    assert 'code == "CZ"' not in text
    assert 'code != "SK"' not in text


def test_sk_report_calculation_uses_registered_strategy():
    result = build_report_calculation_context(
        source_country="SK",
        calculation={
            "status": "CALCULATED",
            "gross_amount": "1000",
            "transaction_currency": "EUR",
            "withholding_tax_transaction_currency": "100",
            "withholding_tax_eur": "100",
            "net_amount_transaction_currency": "900",
            "exchange_rate": None,
        },
        currency="EUR",
    )

    assert result.calculation_base == "1 000 EUR"
    assert result.calculation_tax == "100 EUR"
    assert result.net_amount == "900 EUR"


def test_non_calculated_result_does_not_synthesize_zero():
    result = build_report_calculation_context(
        source_country="SK",
        calculation={
            "status": "NOT_APPLICABLE",
            "reason": "outside_subject_of_tax",
        },
        currency="EUR",
    )

    assert result.calculation_base == "—"
    assert result.calculation_tax == "—"
    assert result.net_amount == "—"
