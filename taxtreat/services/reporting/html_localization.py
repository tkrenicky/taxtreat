from __future__ import annotations

from typing import Any

from .country_copy import report_country_copy


_SK_REPLACEMENTS = (
    ("Česká srážková daň", "Slovenská zrážková daň"),
    ("česká srážková daň", "slovenská zrážková daň"),
    ("Srážková daň", "Zrážková daň"),
    ("srážkové daně", "zrážkovej dane"),
    ("v České republice", "v Slovenskej republike"),
    ("v ČR", "v SR"),
    ("Českou republikou", "Slovenskou republikou"),
    ("České republiky", "Slovenskej republiky"),
    ("Smlouva mezi", "Zmluva medzi"),
    ("smlouvy mezi", "zmluvy medzi"),
    ("Smlouva o zamezení dvojího zdanění", "Zmluva o zamedzení dvojitého zdanenia"),
    ("smlouvy o zamezení dvojího zdanění", "zmluvy o zamedzení dvojitého zdanenia"),
    ("zákona č. 586/1992 Sb., o daních z příjmů", "zákona č. 595/2003 Z. z. o dani z príjmov"),
    ("Odvod srážkové daně", "Odvod zrážkovej dane"),
    (
        "Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP)",
        "Oznámenie o zrazení a odvedení dane (§ 43 ods. 11)",
    ),
    ("Oficiální zdroj", "Oficiálny zdroj"),
    ("Skutečný vlastník příjmu", "Skutočný vlastník príjmu"),
    ("Daňová rezidence pro účely smlouvy", "Daňová rezidencia na účely zmluvy"),
    ("Vazba příjmu ke stálé provozovně v ČR", "Väzba príjmu na stálu prevádzkareň v SR"),
    ("Přímé držení podílu", "Priame držanie podielu"),
    ("Doba držby podílu", "Doba držby podielu"),
    ("měsíců", "mesiacov"),
    ("Potvrzení daňové rezidence", "Potvrdenie o daňovej rezidencii"),
    ("Smluvní a platební dokumentace", "Zmluvná a platobná dokumentácia"),
)


def source_country(report: dict[str, Any]) -> str:
    return str((report.get("scope") or {}).get("source_country") or "CZ").upper()


def localize_report_html(html: str, report: dict[str, Any]) -> str:
    code = source_country(report)
    report_country_copy(code)
    if code == "CZ":
        return html
    if code != "SK":
        raise KeyError(f"No HTML report localization configured for source country: {code}")

    localized = html
    for old, new in _SK_REPLACEMENTS:
        localized = localized.replace(old, new)
    return localized
