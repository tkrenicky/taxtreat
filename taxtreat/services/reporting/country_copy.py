from __future__ import annotations

from dataclasses import dataclass

from taxtreat.countries.registry import get_country_config


@dataclass(frozen=True)
class ReportCountryCopy:
    source_country: str
    language: str
    withholding_tax_label: str
    permanent_establishment_fact_label: str
    domestic_law_reference: str
    treaty_country_prefix: str
    official_source_label: str
    payer_missing_label: str
    recipient_missing_label: str
    yes_label: str
    no_label: str
    months_label: str


_COPY = {
    "CZ": ReportCountryCopy(
        source_country="CZ",
        language="cs",
        withholding_tax_label="Česká srážková daň",
        permanent_establishment_fact_label="Vazba příjmu ke stálé provozovně v ČR",
        domestic_law_reference="zákona č. 586/1992 Sb., o daních z příjmů",
        treaty_country_prefix="Českou republikou",
        official_source_label="Oficiální zdroj",
        payer_missing_label="Plátce – název neuveden",
        recipient_missing_label="Příjemce – název neuveden",
        yes_label="Ano",
        no_label="Ne",
        months_label="měsíců",
    ),
    "SK": ReportCountryCopy(
        source_country="SK",
        language="sk",
        withholding_tax_label="Slovenská zrážková daň",
        permanent_establishment_fact_label="Väzba príjmu na stálu prevádzkareň v SR",
        domestic_law_reference="zákona č. 595/2003 Z. z. o dani z príjmov",
        treaty_country_prefix="Slovenskou republikou",
        official_source_label="Oficiálny zdroj",
        payer_missing_label="Platiteľ – názov neuvedený",
        recipient_missing_label="Príjemca – názov neuvedený",
        yes_label="Áno",
        no_label="Nie",
        months_label="mesiacov",
    ),
}


def report_country_copy(source_country: str) -> ReportCountryCopy:
    code = str(source_country or "").upper()
    # The registry check prevents report copy from silently supporting a country
    # that has no source-country package at all.
    get_country_config(code)
    try:
        return _COPY[code]
    except KeyError as exc:
        raise KeyError(f"No report copy configured for source country: {code}") from exc
