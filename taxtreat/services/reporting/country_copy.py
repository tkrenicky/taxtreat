from __future__ import annotations

from dataclasses import dataclass

from taxtreat.countries.registry import get_country_config


@dataclass(frozen=True)
class ReportCountryCopy:
    source_country: str
    language: str
    withholding_tax_label: str
    withholding_tax_lower: str
    permanent_establishment_fact_label: str
    domestic_law_reference: str
    treaty_country_prefix: str
    treaty_name_prefix: str
    treaty_sentence_prefix: str
    treaty_short_prefix: str
    official_source_label: str
    payer_missing_label: str
    recipient_missing_label: str
    yes_label: str
    no_label: str
    months_label: str
    transaction_labels: dict[str, str]
    cross_border_payment_label: str
    remittance_deadline_label: str
    remittance_deadline_note: str
    notification_deadline_label: str
    notification_deadline_note: str
    residence_certificate_document: str
    beneficial_owner_document: str
    ownership_document: str
    holding_period_document: str
    transaction_document: str
    flow_domestic_question: str
    flow_treaty_relief_title: str
    flow_treaty_relief_question: str
    flow_conditions_title: str
    flow_conditions_question: str
    flow_mli_title: str
    flow_mli_question: str
    flow_final_rate_title: str


_COPY = {
    "CZ": ReportCountryCopy(
        source_country="CZ",
        language="cs",
        withholding_tax_label="Česká srážková daň",
        withholding_tax_lower="česká srážková daň",
        permanent_establishment_fact_label="Vazba příjmu ke stálé provozovně v ČR",
        domestic_law_reference="zákona č. 586/1992 Sb., o daních z příjmů",
        treaty_country_prefix="Českou republikou",
        treaty_name_prefix="Smlouva mezi",
        treaty_sentence_prefix="smlouvy mezi",
        treaty_short_prefix="ČR",
        official_source_label="Oficiální zdroj",
        payer_missing_label="Plátce – název neuveden",
        recipient_missing_label="Příjemce – název neuveden",
        yes_label="Ano",
        no_label="Ne",
        months_label="měsíců",
        transaction_labels={
            "dividend": "Výplata dividend",
            "interest": "Úroková platba",
            "royalty": "Licenční platba",
        },
        cross_border_payment_label="Přeshraniční platba",
        remittance_deadline_label="Odvod srážkové daně",
        remittance_deadline_note="Lhůta pro odvod daně plátcem.",
        notification_deadline_label="Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP)",
        notification_deadline_note=(
            "Podává plátce správci daně; připadne-li poslední den lhůty na víkend "
            "nebo svátek, posouvá se na nejbližší pracovní den."
        ),
        residence_certificate_document="Potvrzení daňové rezidence příjemce platné pro období výplaty.",
        beneficial_owner_document="Podklad k postavení příjemce jako skutečného vlastníka příjmu.",
        ownership_document="Podklad prokazující výši a způsob držby podílu relevantní pro použitou smluvní sazbu.",
        holding_period_document="Podklad k době držby podílu, pokud je pro použitý režim relevantní.",
        transaction_document="Smluvní a platební dokumentace k posuzované transakci.",
        flow_domestic_question="Podléhá transakce české srážkové dani? Jaký je její výchozí režim?",
        flow_treaty_relief_title="SZDZ / osvobození",
        flow_treaty_relief_question="Je použitelné smluvní pravidlo nebo jiné pravidlo, které výchozí český režim omezuje nebo nahrazuje?",
        flow_conditions_title="Podmínky použití",
        flow_conditions_question="Jsou splněny podmínky daňové rezidence, skutečného vlastnictví, typu příjmu a další podmínky příslušného pravidla?",
        flow_mli_title="MLI / PPT",
        flow_mli_question="Je-li relevantní, zohlední se modifikace smlouvy a test hlavního účelu.",
        flow_final_rate_title="Konečná sazba",
    ),
    "SK": ReportCountryCopy(
        source_country="SK",
        language="sk",
        withholding_tax_label="Slovenská zrážková daň",
        withholding_tax_lower="slovenská zrážková daň",
        permanent_establishment_fact_label="Väzba príjmu na stálu prevádzkareň v SR",
        domestic_law_reference="zákona č. 595/2003 Z. z. o dani z príjmov",
        treaty_country_prefix="Slovenskou republikou",
        treaty_name_prefix="Zmluva medzi",
        treaty_sentence_prefix="zmluvy medzi",
        treaty_short_prefix="SR",
        official_source_label="Oficiálny zdroj",
        payer_missing_label="Platiteľ – názov neuvedený",
        recipient_missing_label="Príjemca – názov neuvedený",
        yes_label="Áno",
        no_label="Nie",
        months_label="mesiacov",
        transaction_labels={
            "dividend": "Výplata dividend",
            "interest": "Úroková platba",
            "royalty": "Licenčný poplatok",
        },
        cross_border_payment_label="Cezhraničná platba",
        remittance_deadline_label="Odvod zrážkovej dane",
        remittance_deadline_note="Lehota na odvod dane platiteľom.",
        notification_deadline_label="Oznámenie o zrazení a odvedení dane (§ 43 ods. 11)",
        notification_deadline_note=(
            "Platiteľ podáva oznámenie a odvádza zrazenú daň najneskôr do "
            "15. dňa nasledujúceho kalendárneho mesiaca."
        ),
        residence_certificate_document="Potvrdenie o daňovej rezidencii príjemcu platné pre obdobie výplaty.",
        beneficial_owner_document="Podklad k postaveniu príjemcu ako skutočného vlastníka príjmu.",
        ownership_document="Podklad preukazujúci výšku a spôsob držby podielu relevantný pre použitú zmluvnú sadzbu.",
        holding_period_document="Podklad k dobe držby podielu, ak je pre použitý režim relevantná.",
        transaction_document="Zmluvná a platobná dokumentácia k posudzovanej transakcii.",
        flow_domestic_question="Podlieha transakcia slovenskej zrážkovej dani? Aký je jej východiskový vnútroštátny režim?",
        flow_treaty_relief_title="Zmluva / vnútroštátne alebo EÚ pravidlo",
        flow_treaty_relief_question="Je použiteľné zmluvné, vnútroštátne alebo EÚ pravidlo, ktoré východiskový slovenský režim obmedzuje alebo nahrádza?",
        flow_conditions_title="Podmienky použitia",
        flow_conditions_question="Sú splnené podmienky daňovej rezidencie, skutočného vlastníctva, typu príjmu a ďalšie podmienky príslušného pravidla?",
        flow_mli_title="MLI / PPT a ďalšie modifikácie",
        flow_mli_question="Ak je MLI relevantné, zohľadnia sa všetky párovo uplatniteľné modifikácie vrátane PPT a prípadných pravidiel ovplyvňujúcich dividendy, nárok na výhodu alebo stálu prevádzkareň.",
        flow_final_rate_title="Výsledný režim / sadzba",
    ),
}


def report_country_copy(source_country: str) -> ReportCountryCopy:
    code = str(source_country or "").upper()
    get_country_config(code)
    try:
        return _COPY[code]
    except KeyError as exc:
        raise KeyError(f"No report copy configured for source country: {code}") from exc
