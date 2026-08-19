from __future__ import annotations

from typing import Any

from .country_copy import report_country_copy


_SK_REPLACEMENTS = (
    ("Informace k české srážkové dani", "Informácie k slovenskej zrážkovej dani"),
    ("Česká srážková daň", "Slovenská zrážková daň"),
    ("česká srážková daň", "slovenská zrážková daň"),
    ("české srážkové dani", "slovenskej zrážkovej dani"),
    ("české srážkové daně", "slovenskej zrážkovej dane"),
    ("Srážková daň", "Zrážková daň"),
    ("srážkové daně", "zrážkovej dane"),
    ("Vazba příjmu ke stálé provozovně v ČR", "Väzba príjmu na stálu prevádzkareň v SR"),
    ("v České republice", "v Slovenskej republike"),
    ("v ČR", "v SR"),
    ("Českou republikou", "Slovenskou republikou"),
    ("České republiky", "Slovenskej republiky"),
    ("Česká vnitrostátní úprava", "Slovenská vnútroštátna úprava"),
    ("český režim", "slovenský režim"),
    ("české právo zdanit", "slovenské právo zdaniť"),
    ("českého zdanění", "slovenského zdanenia"),
    ("Česká daň k odvodu", "Slovenská daň na odvod"),
    ("Smlouva mezi", "Zmluva medzi"),
    ("smlouvy mezi", "zmluvy medzi"),
    ("Smlouva o zamezení dvojího zdanění", "Zmluva o zamedzení dvojitého zdanenia"),
    ("smlouvy o zamezení dvojího zdanění", "zmluvy o zamedzení dvojitého zdanenia"),
    ("zákona č. 586/1992 Sb., o daních z příjmů", "zákona č. 595/2003 Z. z. o dani z príjmov"),
    ("586/1992 Sb.", "595/2003 Z. z."),
    ("Odvod srážkové daně", "Odvod zrážkovej dane"),
    (
        "Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP)",
        "Oznámenie o zrazení a odvedení dane (§ 43 ods. 11)",
    ),
    ("§ 38da ZDP", "§ 43 ods. 11"),
    ("§ 38d ZDP", "§ 43 ods. 11"),
    ("Oficiální zdroj", "Oficiálny zdroj"),
    ("Skutečný vlastník příjmu", "Skutočný vlastník príjmu"),
    ("Daňová rezidence pro účely smlouvy", "Daňová rezidencia na účely zmluvy"),
    ("Přímé držení podílu", "Priame držanie podielu"),
    ("Doba držby podílu", "Doba držby podielu"),
    ("měsíců", "mesiacov"),
    ("Potvrzení daňové rezidence", "Potvrdenie o daňovej rezidencii"),
    ("Smluvní a platební dokumentace", "Zmluvná a platobná dokumentácia"),
    ("Plátce – název neuveden", "Platiteľ – názov neuvedený"),
    ("Příjemce – název neuveden", "Príjemca – názov neuvedený"),
    (">Plátce<", ">Platiteľ<"),
    (">Příjemce<", ">Príjemca<"),
)


# These are not generic Czech-language words. They are Czech-source-country legal
# semantics that must never survive into a Slovak-source report. The check runs
# after localization so a newly introduced Czech-only template phrase fails closed
# instead of silently reaching the user.
_SK_FORBIDDEN_LEGAL_MARKERS = (
    "Informace k české srážkové dani",
    "Česká srážková daň",
    "česká srážková daň",
    "české právo zdanit",
    "český režim",
    "zákona č. 586/1992",
    "586/1992 Sb.",
    "§ 38da",
    "§ 38d ",
    "§ 38d<",
    "Kurzovní lístek ČNB",
)


def source_country(report: dict[str, Any]) -> str:
    return str((report.get("scope") or {}).get("source_country") or "CZ").upper()


def _assert_no_czech_legal_leakage(html: str) -> None:
    leaked = [marker for marker in _SK_FORBIDDEN_LEGAL_MARKERS if marker in html]
    if leaked:
        raise ValueError(
            "Slovak report contains Czech-source-country legal leakage: "
            + ", ".join(repr(marker) for marker in leaked)
        )


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
    _assert_no_czech_legal_leakage(localized)
    return localized
