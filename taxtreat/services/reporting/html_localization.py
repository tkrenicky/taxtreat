from __future__ import annotations

from taxtreat.countries.registry import get_country_config

from typing import Any

from .country_copy import report_country_copy


_SK_REPLACEMENTS = (
    ('<html lang="cs">', '<html lang="sk">'),
    ("Informace k české srážkové dani", "Informácie k slovenskej zrážkovej dani"),
    ("Sazba české srážkové daně", "Sadzba slovenskej zrážkovej dane"),
    ("Česká srážková daň", "Slovenská zrážková daň"),
    ("česká srážková daň", "slovenská zrážková daň"),
    ("české srážkové dani", "slovenskej zrážkovej dani"),
    ("české srážkové daně", "slovenskej zrážkovej dane"),
    ("Srážková daň", "Zrážková daň"),
    ("srážkové daně", "zrážkovej dane"),
    ("Vygenerováno", "Vygenerované"),
    ("Souhrn transakce", "Súhrn transakcie"),
    (
        "Shrnutí transakce, použité sazby a výpočtu srážkové daně.",
        "Zhrnutie transakcie, použitej sadzby a výpočtu zrážkovej dane.",
    ),
    ("Vnitrostátní sazba", "Vnútroštátna sadzba"),
    ("Smluvní sazba", "Zmluvná sadzba"),
    ("Použitý právní základ", "Použitý právny základ"),
    ("Údaje o transakci", "Údaje o transakcii"),
    (">Plátce<", ">Platiteľ<"),
    (">Příjemce<", ">Príjemca<"),
    ("Plátce – název neuveden", "Platiteľ – názov neuvedený"),
    ("Příjemce – název neuveden", "Príjemca – názov neuvedený"),
    ("Plátce (název neuveden)", "Platiteľ (názov neuvedený)"),
    ("Příjemce (název neuveden)", "Príjemca (názov neuvedený)"),
    ("Typ příjmu", "Typ príjmu"),
    ("Datum platby", "Dátum platby"),
    ("Hrubá částka", "Hrubá suma"),
    ("Použité předpoklady", "Použité predpoklady"),
    (
        "Následující údaje byly zadány uživatelem a nebyly nezávisle ověřeny; výsledek vychází z jejich správnosti a úplnosti.",
        "Nasledujúce údaje zadal používateľ a neboli nezávisle overené; výsledok vychádza z ich správnosti a úplnosti.",
    ),
    ("Daňový základ", "Základ dane"),
    ("Česká daň k odvodu", "Slovenská daň na odvod"),
    ("Použitá sazba", "Použitá sadzba"),
    ("Čistá částka po srážce", "Čistá suma po zrážke"),
    ("Přepočet měny", "Prepočet meny"),
    ("Jak se stanoví sazba", "Ako sa určuje sadzba"),
    ("Od českého pravidla ke konečné sazbě", "Od slovenského pravidla k výslednej sadzbe"),
    ("Od českého pravidla ke konečnému režimu", "Od slovenského pravidla k výslednému režimu"),
    ("Zjednodušené schéma logiky srážkové daně", "Zjednodušená schéma logiky zrážkovej dane"),
    ("Vzniká česká srážková daň? Jaký je její výchozí režim?", "Vzniká slovenská zrážková daň? Aký je jej východiskový režim?"),
    ("Podléhá transakce české srážkové dani? Jaký je její výchozí režim?", "Podlieha transakcia slovenskej zrážkovej dani? Aký je jej východiskový režim?"),
    ("SZDZ / osvobození", "Zmluva / vnútroštátne alebo EÚ pravidlo"),
    (
        "Je použitelné smluvní pravidlo nebo jiné pravidlo, které výchozí český režim omezuje nebo nahrazuje?",
        "Je použiteľné zmluvné, vnútroštátne alebo EÚ pravidlo, ktoré východiskový slovenský režim obmedzuje alebo nahrádza?",
    ),
    ("Podmínky použití", "Podmienky použitia"),
    (
        "Jsou splněny podmínky daňové rezidence, skutečného vlastnictví, typu příjmu a další podmínky příslušného pravidla?",
        "Sú splnené podmienky daňovej rezidencie, skutočného vlastníctva, typu príjmu a ďalšie podmienky príslušného pravidla?",
    ),
    ("Je-li relevantní, zohlední se modifikace smlouvy a test hlavního účelu.", "Ak je MLI relevantné, zohľadnia sa párovo uplatniteľné modifikácie vrátane testu hlavného účelu."),
    ("Konečná sazba", "Výsledný režim / sadzba"),
    ("Právní základ", "Právny základ"),
    ("Použité ustanovení a praktické kroky", "Použité ustanovenie a praktické kroky"),
    (
        "Právní pravidlo rozhodné pro zobrazenou sazbu a informace navazující na posuzovanou transakci.",
        "Právne pravidlo rozhodné pre zobrazenú sadzbu a informácie nadväzujúce na posudzovanú transakciu.",
    ),
    ("Použité právní pravidlo", "Použité právne pravidlo"),
    ("Vazba na tuto transakci:", "Väzba na túto transakciu:"),
    (
        "Zobrazen je pouze výňatek relevantní pro posuzovanou platbu; úplné znění je dostupné prostřednictvím odkazu na oficiální zdroj.",
        "Zobrazený je iba výňatok relevantný pre posudzovanú platbu; úplné znenie je dostupné prostredníctvom odkazu na oficiálny zdroj.",
    ),
    ("Lhůty", "Lehoty"),
    ("Pro tento výstup nejsou uvedeny navazující lhůty.", "Pre tento výstup nie sú uvedené nadväzujúce lehoty."),
    ("Podklady", "Podklady"),
    ("Dokumentace vztahující se k této transakci", "Dokumentácia vzťahujúca sa k tejto transakcii"),
    ("Otevřené body", "Otvorené body"),
    ("Další právní zdroje", "Ďalšie právne zdroje"),
    ("Jak se pravidla vzájemně vztahují", "Ako sa pravidlá vzájomne uplatňujú"),
    (
        "Česká vnitrostátní úprava stanoví výchozí režim. Je-li použitelná smlouva o zamezení dvojího zdanění a jsou splněny její podmínky, může omezit české právo zdanit. Případné MLI nebo jiné pravidlo proti zneužití se zohlední pouze tehdy, je-li pro danou smlouvu a transakci relevantní.",
        "Slovenská vnútroštátna úprava stanovuje východiskový režim. Ak je použiteľná zmluva o zamedzení dvojitého zdanenia a sú splnené jej podmienky, môže obmedziť slovenské právo zdaniť. Prípadné MLI alebo iné pravidlo proti zneužitiu sa zohľadní iba vtedy, ak je pre danú zmluvu a transakciu relevantné.",
    ),
    ("Česká vnitrostátní úprava", "Slovenská vnútroštátna úprava"),
    ("český režim", "slovenský režim"),
    ("české právo zdanit", "slovenské právo zdaniť"),
    ("českého zdanění", "slovenského zdanenia"),
    ("Vazba příjmu ke stálé provozovně v ČR", "Väzba príjmu na stálu prevádzkareň v SR"),
    ("v České republice", "v Slovenskej republike"),
    ("v ČR", "v SR"),
    ("Českou republikou", "Slovenskou republikou"),
    ("České republiky", "Slovenskej republiky"),
    ("Smlouva mezi", "Zmluva medzi"),
    ("smlouvy mezi", "zmluvy medzi"),
    ("Smlouva o zamezení dvojího zdanění", "Zmluva o zamedzení dvojitého zdanenia"),
    ("smlouvy o zamezení dvojího zdanění", "zmluvy o zamedzení dvojitého zdanenia"),
    ("Mnohostranné úmluvy MLI", "Mnohostranného dohovoru MLI"),
    ("zákona č. 586/1992 Sb., o daních z příjmů", "zákona č. 595/2003 Z. z. o dani z príjmov"),
    ("586/1992 Sb.", "595/2003 Z. z."),
    (
        "Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP)",
        "Oznámenie o zrazení a odvedení dane (§ 43 ods. 11)",
    ),
    ("§ 38da ZDP", "§ 43 ods. 11"),
    ("§ 38d ZDP", "§ 43 ods. 11"),
    (" ZDP)", " zákona č. 595/2003 Z. z.)"),
    ("Odvod srážkové daně", "Odvod zrážkovej dane"),
    ("Lhůta pro odvod daně plátcem.", "Lehota na odvod dane platiteľom."),
    ("Plátce je povinen sraženou daň odvést správci daně nejpozději do tohoto data.", "Platiteľ je povinný zrazenú daň odviesť správcovi dane najneskôr do tohto dátumu."),
    ("Oficiální zdroj", "Oficiálny zdroj"),
    ("Skutečný vlastník příjmu", "Skutočný vlastník príjmu"),
    ("Daňová rezidence pro účely smlouvy", "Daňová rezidencia na účely zmluvy"),
    ("Přímé držení podílu", "Priame držanie podielu"),
    ("Doba držby podílu", "Doba držby podielu"),
    ("měsíců", "mesiacov"),
    ("Potvrzení daňové rezidence", "Potvrdenie o daňovej rezidencii"),
    ("Smluvní a platební dokumentace", "Zmluvná a platobná dokumentácia"),
    ("Název neuveden", "Názov neuvedený"),
    ("Použitá sazba vychází z těchto zadaných údajů:", "Použitá sadzba vychádza z týchto zadaných údajov:"),
    ("Nejbližší lhůta", "Najbližšia lehota"),
    ("Neuplatňuje se", "Neuplatňuje sa"),
)


# These markers identify Czech-source-country legal or role semantics. They are
# checked after localization so future changes to the shared Czech template fail
# closed for SK instead of silently reaching the client report.
_SK_FORBIDDEN_LEGAL_MARKERS = (
    "Informace k české srážkové dani",
    "Sazba české srážkové daně",
    "Česká srážková daň",
    "česká srážková daň",
    "Od českého pravidla",
    "Vzniká česká srážková daň",
    "Podléhá transakce české srážkové dani",
    "Česká vnitrostátní úprava",
    "české právo zdanit",
    "český režim",
    "zákona č. 586/1992",
    "586/1992 Sb.",
    "§ 38da",
    "§ 38d ",
    "§ 38d<",
    " ZDP)",
    "Kurzovní lístek ČNB",
    ">Plátce<",
    ">Příjemce<",
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
    config = get_country_config(code)

    strategy = config.html_localization_strategy

    if strategy == "identity":
        return html

    if strategy == "sk":
        localized = html
        for old, new in _SK_REPLACEMENTS:
            localized = localized.replace(old, new)
        _assert_no_czech_legal_leakage(localized)
        return localized

    raise KeyError(
        f"No HTML report localization strategy configured for "
        f"source country {code}: {strategy}"
    )
