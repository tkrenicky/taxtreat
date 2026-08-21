import pytest

from taxtreat.services.reporting.country_copy import report_country_copy


def test_slovak_report_copy_never_reuses_czech_tax_labels():
    sk = report_country_copy("SK")

    assert sk.withholding_tax_label == "Slovenská zrážková daň"
    assert sk.permanent_establishment_fact_label.endswith("v SR")
    assert "595/2003 Z. z." in sk.domestic_law_reference
    assert "586/1992" not in sk.domestic_law_reference
    assert "ČR" not in sk.permanent_establishment_fact_label
    assert sk.treaty_country_prefix == "Slovenskou republikou"
    assert sk.official_source_label == "Oficiálny zdroj"
    assert sk.yes_label == "Áno"
    assert sk.no_label == "Nie"
    assert sk.months_label == "mesiacov"


def test_czech_report_copy_preserves_existing_language():
    cz = report_country_copy("CZ")

    assert cz.withholding_tax_label == "Česká srážková daň"
    assert "586/1992 Sb." in cz.domestic_law_reference
    assert cz.treaty_country_prefix == "Českou republikou"


def test_unknown_report_source_country_fails_closed():
    with pytest.raises(KeyError):
        report_country_copy("XX")
