from __future__ import annotations

import re
from typing import Any

from .country_copy import report_country_copy


_EN_REPLACEMENTS = (
    ('<html lang="cs">', '<html lang="en">'),
    ("Informace k české srážkové dani", "Czech withholding tax information"),
    ("Vygenerováno", "Generated"),
    ("SOUHRN TRANSAKCE", "TRANSACTION SUMMARY"),
    ("Souhrn transakce", "Transaction summary"),
    ("Shrnutí transakce, použité sazby a výpočtu srážkové daně.", "Summary of the transaction, applied rates and withholding tax calculation."),
    ("Výplata dividend", "Dividend payment"),
    ("Úroková platba", "Interest payment"),
    ("Licenční platba", "Royalty payment"),
    ("Přeshraniční platba", "Cross-border payment"),
    ("POUŽITÁ SAZBA", "APPLIED RATE"),
    ("Použitá sazba", "Applied rate"),
    ("TYP PŘÍJMU", "INCOME TYPE"),
    ("Typ příjmu", "Income type"),
    ("Dividendy", "Dividends"),
    ("Úroky", "Interest"),
    ("Licenční poplatky", "Royalties"),
    ("PRÁVNÍ USTANOVENÍ", "LEGAL PROVISION"),
    ("NEJBLIŽŠÍ LHŮTA", "NEXT DEADLINE"),
    ("Nejbližší lhůta", "Next deadline"),
    ("SAZBA ČESKÉ SRÁŽKOVÉ DANĚ", "CZECH WITHHOLDING TAX RATE"),
    ("Sazba české srážkové daně", "Czech withholding tax rate"),
    ("Česká srážková daň", "Czech withholding tax"),
    ("česká srážková daň", "Czech withholding tax"),
    ("Vnitrostátní sazba", "Domestic rate"),
    ("Smluvní sazba", "Treaty rate"),
    ("Použitý právní základ", "Applied legal basis"),
    ("Při splnění uvedených předpokladů se uplatní osvobození od české srážkové daně podle", "Based on the entered assumptions, the income is exempt from Czech withholding tax under"),
    ("Výchozí vnitrostátní sazba", "Starting domestic rate"),
    ("podle výše uvedeného ustanovení", "under the provision stated above"),
    ("Údaje o transakci", "Transaction details"),
    (">Plátce<", ">Payer<"),
    (">Příjemce<", ">Recipient<"),
    ("Plátce – název neuveden", "Payer – name not provided"),
    ("Příjemce – název neuveden", "Recipient – name not provided"),
    ("Datum platby", "Payment date"),
    ("Hrubá částka", "Gross amount"),
    ("POUŽITÉ PŘEDPOKLADY", "ASSUMPTIONS USED"),
    ("Použité předpoklady", "Assumptions used"),
    ("Následující údaje byly zadány uživatelem a nebyly nezávisle ověřeny; výsledek vychází z jejich správnosti a úplnosti.", "The following facts were entered by the user and were not independently verified; the result depends on their accuracy and completeness."),
    ("Skutečný vlastník příjmu", "Beneficial owner of the income"),
    ("Daňová rezidence pro účely smlouvy", "Tax residence for treaty purposes"),
    ("Vazba příjmu ke stálé provozovně v ČR", "Connection of the income to a Czech permanent establishment"),
    ("Podíl na základním kapitálu plátce", "Ownership in the payer's share capital"),
    ("Podíl na hlasovacích právech", "Voting ownership"),
    ("Přímé držení podílu", "Direct ownership"),
    ("Doba držby podílu", "Holding period"),
    ("Výše úroku odpovídá tržním podmínkám", "Interest amount is at arm's length"),
    ("Předmět licenční platby", "Royalty category"),
    (">Ano<", ">Yes<"),
    (">Ne<", ">No<"),
    (" měsíců", " months"),
    ("VÝPOČET", "CALCULATION"),
    ("Výpočet", "Calculation"),
    ("Daňový základ", "Tax base"),
    ("Srážková daň", "Withholding tax"),
    ("Česká daň k odvodu", "Czech tax payable"),
    ("Čistá částka po srážce", "Net amount after withholding"),
    ("Přepočet měny", "Currency conversion"),
    ("JAK SE STANOVÍ SAZBA", "HOW THE RATE IS DETERMINED"),
    ("Jak se stanoví sazba", "How the rate is determined"),
    ("Od českého pravidla ke konečné sazbě", "From the Czech domestic rule to the final rate"),
    ("Od českého pravidla ke konečnému režimu", "From the Czech domestic rule to the final treatment"),
    ("Zjednodušené schéma logiky srážkové daně", "Simplified withholding tax decision path"),
    ("Česká srážková daň", "Czech withholding tax"),
    ("Podléhá transakce české srážkové dani? Jaký je její výchozí režim?", "Is the transaction subject to Czech withholding tax and what is the starting domestic treatment?"),
    ("Vzniká česká srážková daň? Jaký je její výchozí režim?", "Does Czech withholding tax arise and what is the starting domestic treatment?"),
    ("SZDZ / osvobození", "Treaty / exemption"),
    ("Je použitelné smluvní pravidlo nebo jiné pravidlo, které výchozí český režim omezuje nebo nahrazuje?", "Does a treaty or another rule limit or replace the starting Czech domestic treatment?"),
    ("Podmínky použití", "Conditions for application"),
    ("Jsou splněny podmínky daňové rezidence, skutečného vlastnictví, typu příjmu a další podmínky příslušného pravidla?", "Are the residence, beneficial ownership, income-type and other conditions of the relevant rule satisfied?"),
    ("Je-li relevantní, zohlední se modifikace smlouvy a test hlavního účelu.", "Where relevant, treaty modifications and the principal purpose test are taken into account."),
    ("Konečná sazba", "Final rate"),
    ("PRÁVNÍ ZÁKLAD", "LEGAL BASIS"),
    ("Právní základ", "Legal basis"),
    ("Použité ustanovení a praktické kroky", "Applied provision and practical steps"),
    ("Právní pravidlo rozhodné pro zobrazenou sazbu a informace navazující na posuzovanou transakci.", "The legal rule determining the displayed rate and the information relevant to the transaction assessed."),
    ("POUŽITÉ PRÁVNÍ PRAVIDLO", "APPLIED LEGAL RULE"),
    ("Použité právní pravidlo", "Applied legal rule"),
    ("Oficiální zdroj", "Official source"),
    ("K tomuto zdroji není v reportu k dispozici samostatný výňatek.", "No separate excerpt is available for this source in the report."),
    ("Vazba na tuto transakci:", "Relevance to this transaction:"),
    ("Použitá sazba vychází z těchto zadaných údajů:", "The applied rate is based on the following entered facts:"),
    ("zadaný podíl příjemce", "recipient ownership"),
    ("doba držby", "holding period"),
    ("příjemce uveden jako skutečný vlastník příjmu", "recipient stated to be the beneficial owner of the income"),
    ("Zobrazen je pouze výňatek relevantní pro posuzovanou platbu; úplné znění je dostupné prostřednictvím odkazu na oficiální zdroj.", "Only the excerpt relevant to the payment assessed is shown; the full text is available through the official-source link."),
    ("LHŮTY", "DEADLINES"),
    ("Lhůty", "Deadlines"),
    ("Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP)", "Outbound income notification (Section 38da of the Czech Income Taxes Act)"),
    ("Odvod srážkové daně", "Withholding tax remittance"),
    ("Podává plátce správci daně; připadne-li poslední den lhůty na víkend nebo svátek, posouvá se na nejbližší pracovní den.", "Filed by the payer with the Czech tax authority; if the last day falls on a weekend or public holiday, the deadline moves to the next working day."),
    ("Lhůta pro odvod daně plátcem.", "Deadline for remittance of tax by the payer."),
    ("PODKLADY", "SUPPORTING DOCUMENTATION"),
    ("Podklady", "Supporting documentation"),
    ("Dokumentace vztahující se k této transakci", "Documentation relating to this transaction"),
    ("Potvrzení daňové rezidence příjemce platné pro období výplaty.", "Recipient tax residence certificate valid for the payment period."),
    ("Podklad k postavení příjemce jako skutečného vlastníka příjmu.", "Documentation supporting the recipient's beneficial-owner status."),
    ("Podklad prokazující výši a způsob držby podílu relevantní pro použitou smluvní sazbu.", "Documentation supporting the level and form of ownership relevant to the applied treaty rate."),
    ("Podklad k době držby podílu, pokud je pro použitý režim relevantní.", "Documentation supporting the holding period where relevant to the applied treatment."),
    ("Smluvní a platební dokumentace k posuzované transakci.", "Contract and payment documentation for the transaction assessed."),
    ("OTEVŘENÉ BODY", "OPEN ITEMS"),
    ("Otevřené body", "Open items"),
    ("DALŠÍ PRÁVNÍ ZDROJE", "ADDITIONAL LEGAL SOURCES"),
    ("Další právní zdroje", "Additional legal sources"),
    ("VNITROSTÁTNÍ PRÁVO", "DOMESTIC LAW"),
    ("SMLOUVA", "TREATY"),
    ("čl.", "Article"),
    ("smlouvy mezi Českou republikou a", "of the Double Tax Treaty between the Czech Republic and"),
    ("Smlouva o zamezení dvojího zdanění", "Double Tax Treaty"),
    ("Jak se pravidla vzájemně vztahují", "How the rules interact"),
    ("Česká vnitrostátní úprava stanoví výchozí režim. Je-li použitelná smlouva o zamezení dvojího zdanění a jsou splněny její podmínky, může omezit české právo zdanit. Případné MLI nebo jiné pravidlo proti zneužití se zohlední pouze tehdy, je-li pro danou smlouvu a transakci relevantní.", "Czech domestic law establishes the starting treatment. Where a Double Tax Treaty applies and its conditions are met, it may limit the Czech taxing right. Any applicable MLI or other anti-abuse rule is taken into account only where relevant to the treaty and transaction concerned."),
    ("TaxTreat je informační nástroj. Automatizovaně zobrazuje informace odvozené z uvedených právních zdrojů a z údajů zadaných uživatelem. Neprovádí individuální právní ani daňové posouzení, neposkytuje doporučení ani právní či daňové poradenství a neurčuje, jak má uživatel v konkrétním případě postupovat. Uživatel odpovídá za správnost vstupních údajů a za vlastní posouzení použitelnosti zobrazených informací.", "TaxTreat is an information tool. It automatically presents information derived from the legal sources shown and from facts entered by the user. It does not perform an individual legal or tax assessment, provide legal or tax advice, or determine the user's course of action. The user remains responsible for the accuracy of the input data and for assessing whether the displayed information is applicable."),
    ("zákona č. 586/1992 Sb., o daních z příjmů", "of the Czech Income Taxes Act (Act No. 586/1992 Coll.)"),
    ("zákon č. 586/1992 Sb., o daních z příjmů", "the Czech Income Taxes Act (Act No. 586/1992 Coll.)"),
    ("§ 19 odst. 1 písm. ze), odst. 3, 4, 6, 8 a 11", "Section 19(1)(ze), (3), (4), (6), (8) and (11)"),
    ("§ 36 odst. 1 písm. b) bod 1", "Section 36(1)(b)(1)"),
    ("Osvobození se použije – česká srážková daň se neodvádí.", "Applicable – Czech withholding tax is not due."),
    ("Primárním právním titulem je § 19 ZDP; smluvní režim je pouze doplňkový.", "The domestic exemption under Section 19 is the primary legal basis; treaty treatment is supplementary."),
    ("Vnitrostátní osvobození", "Domestic exemption"),
    ("Osvobození", "Exemption"),
    ("Neuplatňuje se", "Not applicable"),
)


_SK_REPLACEMENTS = (
    ("Česká srážková daň", "Slovenská zrážková daň"),
    ("česká srážková daň", "slovenská zrážková daň"),
    ("Srážková daň", "Zrážková daň"),
    ("srážkové daně", "zrážkovej dane"),
    ("Vazba příjmu ke stálé provozovně v ČR", "Väzba príjmu na stálu prevádzkareň v SR"),
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
    ("Přímé držení podílu", "Priame držanie podielu"),
    ("Doba držby podílu", "Doba držby podielu"),
    ("měsíců", "mesiacov"),
    ("Potvrzení daňové rezidence", "Potvrdenie o daňovej rezidencii"),
    ("Smluvní a platební dokumentace", "Zmluvná a platobná dokumentácia"),
)


def source_country(report: dict[str, Any]) -> str:
    return str((report.get("scope") or {}).get("source_country") or "CZ").upper()


def _report_language(report: dict[str, Any]) -> str:
    return "en" if str(report.get("language") or "").lower() == "en" else "cs"


def _localize_cz_to_en(html: str, report: dict[str, Any]) -> str:
    localized = html
    for old, new in _EN_REPLACEMENTS:
        localized = localized.replace(old, new)

    recipient = str((report.get("scope") or {}).get("recipient_country") or "").upper()
    if recipient:
        localized = re.sub(
            r"Smlouva mezi Českou republikou a .*? o zamezení dvojího zdanění",
            f"Double Tax Treaty between the Czech Republic and {recipient}",
            localized,
        )
        localized = re.sub(
            r"smlouvy mezi Českou republikou a .*? o zamezení dvojího zdanění",
            f"the Double Tax Treaty between the Czech Republic and {recipient}",
            localized,
        )

    localized = localized.replace('lang="cs"', 'lang="en"')
    return localized


def localize_report_html(html: str, report: dict[str, Any]) -> str:
    code = source_country(report)
    report_country_copy(code)

    if code == "CZ":
        if _report_language(report) == "en":
            return _localize_cz_to_en(html, report)
        return html

    if code != "SK":
        raise KeyError(f"No HTML report localization configured for source country: {code}")

    localized = html
    for old, new in _SK_REPLACEMENTS:
        localized = localized.replace(old, new)
    return localized
