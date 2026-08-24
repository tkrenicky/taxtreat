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
    treaty_join_word: str
    treaty_generic_name: str
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
        treaty_join_word="státem",
        treaty_generic_name="Smlouva o zamezení dvojího zdanění",
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
        treaty_join_word="štátom",
        treaty_generic_name="Zmluva o zamedzení dvojitého zdanenia",
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


def _generic_report_copy(source_country: str) -> ReportCountryCopy:
    config = get_country_config(source_country)
    code = config.code
    domestic_reference = config.domestic_law_label or "applicable domestic tax law"
    return ReportCountryCopy(
        source_country=code,
        language="en",
        withholding_tax_label=f"{code} withholding tax",
        withholding_tax_lower=f"{code} withholding tax",
        permanent_establishment_fact_label=f"Income attributable to a permanent establishment in {code}",
        domestic_law_reference=domestic_reference,
        treaty_country_prefix=code,
        treaty_name_prefix="Tax treaty between",
        treaty_sentence_prefix="tax treaty between",
        treaty_short_prefix=code,
        treaty_join_word="and",
        treaty_generic_name="Double taxation treaty",
        official_source_label="Official source",
        payer_missing_label="Payer – name not provided",
        recipient_missing_label="Recipient – name not provided",
        yes_label="Yes",
        no_label="No",
        months_label="months",
        transaction_labels={
            "dividend": "Dividend payment",
            "interest": "Interest payment",
            "royalty": "Royalty payment",
        },
        cross_border_payment_label="Cross-border payment",
        remittance_deadline_label="Withholding tax remittance",
        remittance_deadline_note="Deadline for remittance by the payer.",
        notification_deadline_label="Withholding tax notification",
        notification_deadline_note="Country-specific filing requirements must be confirmed before production release.",
        residence_certificate_document="Recipient tax residence certificate valid for the payment period.",
        beneficial_owner_document="Evidence supporting the recipient's beneficial-owner status.",
        ownership_document="Evidence supporting the ownership percentage and holding structure relevant to treaty relief.",
        holding_period_document="Evidence supporting the holding period where relevant.",
        transaction_document="Contractual and payment documentation for the transaction.",
        flow_domestic_question=f"Is the transaction subject to {code} withholding tax and what is the domestic starting position?",
        flow_treaty_relief_title="Treaty / domestic relief",
        flow_treaty_relief_question="Does an applicable treaty or domestic rule limit or replace the domestic starting position?",
        flow_conditions_title="Conditions",
        flow_conditions_question="Are the residence, beneficial ownership, income classification and other applicable conditions satisfied?",
        flow_mli_title="MLI / anti-abuse",
        flow_mli_question="Where relevant, apply pair-specific MLI modifications and treaty anti-abuse conditions.",
        flow_final_rate_title="Final treatment / rate",
    )


def report_country_copy(source_country: str) -> ReportCountryCopy:
    code = str(source_country or "").upper()
    get_country_config(code)
    return _COPY.get(code) or _generic_report_copy(code)
