from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
STAGE6_RULE_DIR = ROOT / "data" / "legal_rules_stage6"


FACT_GUIDANCE: dict[str, dict[str, Any]] = {
    "beneficial_owner": {
        "prompt": "Ověřte, že příjemce je skutečným vlastníkem příjmu.",
        "why": (
            "Výpočet s tímto předpokladem pracuje automaticky. Pokud neplatí, "
            "je třeba výsledek projednat s daňovým poradcem."
        ),
        "client_answerable": False,
        "documents": [
            "Prohlášení skutečného vlastníka příjmu",
            "Relevantní smlouvy a doklady o toku platby",
        ],
    },
    "recipient_is_treaty_resident": {
        "prompt": "Ověřte daňové rezidentství příjemce ve vybraném státě.",
        "why": (
            "Výpočet vychází ze státu daňové rezidence uvedeného v základním "
            "zadání; rezidentství je vhodné doložit aktuálním potvrzením."
        ),
        "client_answerable": False,
        "documents": ["Aktuální potvrzení o daňovém rezidentství"],
    },
    "permanent_establishment_connection": {
        "prompt": (
            "Upřesněte v základním zadání, zda platba souvisí se stálou "
            "provozovnou příjemce v České republice."
        ),
        "why": "Vazba na stálou provozovnu může změnit daňový režim.",
        "client_answerable": False,
        "documents": [
            "Organizační struktura",
            "Analýza stálé provozovny",
        ],
    },
    "arm_length_amount": {
        "prompt": "U spojených osob ověřte, zda výše platby odpovídá obvyklým podmínkám.",
        "why": "Část platby přesahující obvyklou výši může mít odlišný daňový režim.",
        "client_answerable": False,
        "documents": [
            "Vnitroskupinová smlouva",
            "Dokumentace k převodním cenám",
        ],
    },
    "payment_is_arm_length_amount": {
        "prompt": "U spojených osob ověřte, zda výše platby odpovídá obvyklým podmínkám.",
        "why": "Část platby přesahující obvyklou výši může mít odlišný daňový režim.",
        "client_answerable": False,
        "documents": [
            "Vnitroskupinová smlouva",
            "Dokumentace k převodním cenám",
        ],
    },
    "ownership_percent": {
        "prompt": "Jaký podíl na základním kapitálu českého plátce drží příjemce?",
        "why": "Výše podílu může rozhodnout o použití snížené sazby z dividend.",
        "response_type": "decimal_percent",
        "documents": [
            "Výpis z evidence podílů nebo akcií",
            "Schéma vlastnické struktury",
        ],
    },
    "direct_ownership": {
        "prompt": "Drží příjemce uvedený podíl na českém plátci přímo?",
        "why": "Některá osvobození nebo snížené sazby vyžadují přímé vlastnictví.",
        "documents": ["Výpis z evidence podílů nebo akcií", "Schéma vlastnické struktury"],
    },
    "direct_or_indirect_voting_ownership": {
        "prompt": "Jaký podíl na hlasovacích právech českého plátce příjemce drží?",
        "why": "Smluvní hranice sazby mohou vycházet z podílu na hlasovacích právech.",
        "response_type": "decimal_percent",
        "documents": ["Výpis z evidence podílů nebo akcií", "Schéma vlastnické struktury"],
    },
    "holding_period_months": {
        "prompt": "Od jakého data příjemce drží podíl na českém plátci?",
        "why": "TaxTreat z data nabytí automaticky vypočte dosavadní dobu držby.",
        "response_type": "date",
        "input_path": "derived.acquisition_date",
        "documents": [
            "Doklady o nabytí podílu",
            "Datovaný výpis z evidence podílů nebo akcií",
        ],
    },
    "holding_period_will_reach_months": {
        "prompt": "Ověřte režim pro případ, kdy minimální doba držby uplyne až po výplatě.",
        "why": "Budoucí splnění doby držby a související postup nelze potvrdit pouze z klientského vstupu.",
        "client_answerable": False,
        "advisor_topic": "future_holding_period",
        "documents": ["Doklad o datu nabytí a předpokládané době držby"],
    },
    "recipient_entity_type": {
        "prompt": "Vyberte typ příjemce v základním zadání.",
        "why": "Typ příjemce může ovlivnit dostupný daňový režim.",
        "client_answerable": False,
        "documents": [
            "Výpis z obchodního rejstříku",
            "Zakladatelské dokumenty",
        ],
    },
    "recipient_is_qualifying_company_form": {
        "prompt": "Ověřte, zda právní forma příjemce splňuje podmínky příslušného režimu.",
        "why": "Jde o odborné vyhodnocení právní formy, nikoli o údaj, který má klient právně kvalifikovat.",
        "client_answerable": False,
        "advisor_topic": "recipient_eligibility",
        "documents": [
            "Výpis z obchodního rejstříku",
            "Zakladatelské dokumenty",
        ],
    },
    "recipient_subject_to_qualifying_corporate_tax": {
        "prompt": "Ověřte daňové postavení příjemce pro použití příslušného režimu.",
        "why": "Tuto podmínku je třeba posoudit podle pravidel státu příjemce a jeho konkrétního postavení.",
        "client_answerable": False,
        "advisor_topic": "recipient_eligibility",
        "documents": [
            "Potvrzení o daňovém postavení",
            "Potvrzení o daňovém rezidentství",
        ],
    },
    "royalty_category": {
        "prompt": "Jakého práva nebo majetku se licenční platba týká?",
        "why": "Sazba může záviset na předmětu licence.",
        "response_type": "choice",
        "options": [
            [
                "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
                "Autorské dílo (mimo software, film, TV a rozhlas)",
            ],
            [
                "cinematographic_films_or_broadcast_media",
                "Film, televizní nebo rozhlasové vysílání",
            ],
            ["computer_software", "Počítačový software"],
            [
                "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
                "Patent, ochranná známka, průmyslový vzor, postup nebo know-how",
            ],
            [
                "financial_lease_of_equipment",
                "Finanční leasing průmyslového, obchodního nebo vědeckého zařízení",
            ],
            [
                "operating_lease_or_other_use_of_equipment",
                "Operativní leasing nebo jiné užívání průmyslového, obchodního nebo vědeckého zařízení",
            ],
            ["other", "Jiný předmět licence"],
        ],
        "documents": ["Licenční smlouva", "Popis licencovaných práv"],
    },
    "special_article_11_3_exemption": {
        "prompt": "Ověřte, zda se na úrok vztahuje zvláštní smluvní výjimka.",
        "why": "Použití zvláštní výjimky závisí na konkrétních stranách a dokumentaci financování.",
        "client_answerable": False,
        "documents": ["Úvěrová nebo zápůjční smlouva", "Doklady k uplatňovanému osvobození"],
    },
}

# Treaty-specific facts that can be answered by the user. They are
# presented only when the selected treaty actually needs them.
FACT_GUIDANCE.update({
    "continuous_holding_period_days": {
        "prompt": "Od jakého data příjemce nepřetržitě drží podíl na českém plátci?",
        "why": (
            "TaxTreat z data nabytí automaticky vypočte přesnou dobu "
            "držby ve dnech."
        ),
        "response_type": "date",
        "input_path": "derived.acquisition_date",
        "documents": ["Doklady o nabytí podílu"],
    },
    "holding_period_years": {
        "prompt": "Od jakého data příjemce drží podíl na českém plátci?",
        "why": (
            "TaxTreat z data nabytí automaticky vypočte dobu držby "
            "v celých letech."
        ),
        "response_type": "date",
        "input_path": "derived.acquisition_date",
        "documents": ["Doklady o nabytí podílu"],
    },
    "voting_ownership": {
        "prompt": (
            "Jaký podíl na hlasovacích právech českého plátce "
            "příjemce drží?"
        ),
        "why": (
            "Smluvní hranice může být navázána na hlasovací práva "
            "namísto podílu na základním kapitálu."
        ),
        "response_type": "decimal_percent",
        "documents": ["Schéma vlastnické struktury"],
    },
    "voting_power_control": {
        "prompt": (
            "Jaký podíl hlasovací síly českého plátce příjemce ovládá?"
        ),
        "why": (
            "Příslušná smlouva používá pro sníženou sazbu hranici "
            "hlasovací síly."
        ),
        "response_type": "decimal_percent",
        "documents": ["Schéma vlastnické struktury"],
    },
    "recipient_is_partnership": {
        "prompt": (
            "Je příjemce právně kvalifikován jako partnership "
            "(osobní společnost)?"
        ),
        "why": (
            "U této smlouvy může právní forma partnership ovlivnit "
            "použití dividendového pravidla."
        ),
        "response_type": "boolean",
        "documents": ["Zakladatelské dokumenty příjemce"],
    },
    "canadian_non_resident_owned_investment_corporation_exception": {
        "prompt": (
            "Spadá kanadský příjemce do zvláštní kategorie "
            "non-resident-owned investment corporation?"
        ),
        "why": (
            "Kanadská smlouva obsahuje pro tuto kategorii zvláštní "
            "výjimku z dividendového pravidla."
        ),
        "response_type": "boolean",
        "documents": [
            "Doklady k právnímu a daňovému postavení příjemce"
        ],
    },
    "recipient_has_immediate_entitlement": {
        "prompt": "Má příjemce bezprostřední nárok na licenční příjem?",
        "why": (
            "Příslušná smlouva vyžaduje bezprostřední nárok příjemce "
            "na licenční platbu."
        ),
        "response_type": "boolean",
        "documents": ["Licenční smlouva"],
    },
    "loan_is_noncommercial": {
        "prompt": (
            "Jde o nekomerční úvěr nebo zápůjčku ve smyslu "
            "příslušné smlouvy?"
        ),
        "why": (
            "U této smlouvy může nekomerční charakter financování "
            "vést ke zvláštnímu režimu úroku."
        ),
        "response_type": "boolean",
        "documents": ["Úvěrová nebo zápůjční smlouva"],
    },
    "minimum_term_years": {
        "prompt": (
            "Jaká je sjednaná minimální doba tohoto financování "
            "v letech?"
        ),
        "why": (
            "Příslušná smlouva váže zvláštní sazbu na minimální "
            "dobu financování."
        ),
        "response_type": "number",
        "documents": ["Úvěrová nebo zápůjční smlouva"],
    },
})


# These facts contain a treaty-specific enumerated value rather than
# an ordinary True/False value. The UI asks a human Yes/No question,
# while intake translates Yes to the exact value required by the
# selected country's Stage 6 rule.
RULE_VALUE_BOOLEAN_GUIDANCE: dict[str, dict[str, str]] = {
    "article_11_3_exemption": {
        "prompt": (
            "Splňuje tento úrok zvláštní výjimku podle čl. 11 odst. 3 "
            "příslušné smlouvy?"
        ),
        "why": (
            "Zvolte Ano pouze tehdy, pokud jste ověřili, že konkrétní "
            "financování spadá do zvláštní smluvní kategorie. "
            "TaxTreat tuto výjimku bez výslovné odpovědi nepředpokládá."
        ),
    },
    "article_11_3a_exemption": {
        "prompt": (
            "Splňuje tento úrok zvláštní výjimku podle čl. 11 odst. 3 "
            "písm. a) příslušné smlouvy?"
        ),
        "why": (
            "Zvolte Ano jen při potvrzeném splnění konkrétní smluvní "
            "výjimky; jinak zvolte Ne."
        ),
    },
    "special_article_11_3_exemption": {
        "prompt": (
            "Splňuje tento úrok zvláštní výjimku podle čl. 11 odst. 3 "
            "příslušné smlouvy?"
        ),
        "why": (
            "Zvolte Ano jen tehdy, pokud konkrétní financování odpovídá "
            "přesnému znění smluvní výjimky."
        ),
    },
    "recipient_or_financing": {
        "prompt": (
            "Spadá příjemce nebo způsob financování do zvláštní "
            "kategorie osvobozené podle smlouvy?"
        ),
        "why": (
            "Může jít o veřejné orgány, centrální banku, vybrané "
            "veřejné finanční instituce nebo kvalifikované státem "
            "podporované financování podle konkrétní smlouvy."
        ),
    },
    "recipient_or_loan_provider_or_guarantor": {
        "prompt": (
            "Spadá příjemce, poskytovatel úvěru nebo ručitel do "
            "zvláštní veřejné kategorie podle smlouvy?"
        ),
        "why": (
            "Zvolte Ano pouze při potvrzeném splnění konkrétní "
            "smluvní kategorie."
        ),
    },
    "loan_or_credit_provider": {
        "prompt": "Je poskytovatelem tohoto úvěru nebo zápůjčky banka?",
        "why": (
            "Některé smlouvy stanoví zvláštní sazbu pro úrok "
            "z bankovního financování."
        ),
    },
    "loan_provider": {
        "prompt": (
            "Je poskytovatelem financování smluvní stát nebo jiný "
            "subjekt výslovně uvedený ve smlouvě?"
        ),
        "why": (
            "Zvláštní sazba se použije pouze při splnění konkrétní "
            "kategorie poskytovatele uvedené ve smlouvě."
        ),
    },
    "lender_category": {
        "prompt": (
            "Splňuje věřitel zvláštní kategorii požadovanou smlouvou?"
        ),
        "why": (
            "Zvolte Ano pouze tehdy, pokud jste ověřili postavení "
            "věřitele podle příslušného ustanovení smlouvy."
        ),
    },
    "borrower_category": {
        "prompt": (
            "Splňuje dlužník zvláštní kategorii požadovanou smlouvou?"
        ),
        "why": (
            "Zvolte Ano pouze tehdy, pokud jste ověřili postavení "
            "dlužníka podle příslušného ustanovení smlouvy."
        ),
    },
    "official_foreign_exchange_reserve_investment": {
        "prompt": (
            "Jde o investici oficiálních devizových rezerv provedenou "
            "oprávněnou veřejnou nebo měnovou institucí?"
        ),
        "why": (
            "Tato zvláštní kategorie může podle příslušné smlouvy "
            "vést k osvobození úroku."
        ),
    },
    "purpose": {
        "prompt": (
            "Splňuje financování zvláštní účel výslovně uvedený "
            "v příslušné smlouvě?"
        ),
        "why": (
            "Zvláštní sazba se použije pouze pro účel financování "
            "přesně vymezený danou smlouvou."
        ),
    },
    "qualifying_article_11_2a_case": {
        "prompt": (
            "Spadá tento úrok do zvláštní kategorie podle čl. 11 "
            "odst. 2 písm. a) příslušné smlouvy?"
        ),
        "why": (
            "Může jít například o kvalifikované bankovní, pojistné, "
            "finanční nebo úvěrové financování podle konkrétní smlouvy."
        ),
    },
}


# These are labels of the legal-rule branch itself. They are not
# transaction facts and must never become questions for the user.
DERIVED_TRANSACTION_FACTS = {
    "claim_not_effectively_connected_to_czech_pe": (
        "permanent_establishment_connection"
    ),
    "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base": (
        "permanent_establishment_connection"
    ),
}


RULE_CONTROL_FACTS = {
    "fallback_case",
    "source_state_taxation",
    "general_article_11_2_rate",
}


DETERMINATION_GUIDANCE = {
    "treaty_ppt_passed": {
        "prompt": "Projednejte s daňovým poradcem účel transakce a případné použití testu hlavního účelu.",
        "why": "Tuto podmínku nelze potvrdit pouze ze základních údajů o platbě.",
        "documents": [
            "Memorandum k účelu transakce",
            "Doklady o ekonomické podstatě a obchodním důvodu",
        ],
    },
}

PROFESSIONAL_FACT_GROUPS = {
    "recipient_has_no_tax_exemption_or_zero_rate_option": {
        "topic": "recipient_eligibility",
        "prompt": "Ověřte podmínky příjemce pro použití případného osvobození.",
        "why": "Posuzuje se právní forma, daňové rezidentství, způsob zdanění a vztah příjemce k plátci.",
    },
    "recipient_is_parent_company": {
        "topic": "recipient_eligibility",
        "prompt": "Ověřte podmínky příjemce pro použití případného osvobození.",
        "why": "Posuzuje se právní forma, daňové rezidentství, způsob zdanění a vztah příjemce k plátci.",
    },
    "recipient_is_tax_resident_in_eligible_jurisdiction": {
        "topic": "recipient_eligibility",
        "prompt": "Ověřte podmínky příjemce pro použití případného osvobození.",
        "why": "Posuzuje se právní forma, daňové rezidentství, způsob zdanění a vztah příjemce k plátci.",
    },
    "statutory_clawback_acknowledged": {
        "topic": "future_holding_period",
        "prompt": "Ověřte postup při dodatečném splnění minimální doby držby.",
        "why": "Případný následný nárok a související postup musí být posouzen podle konkrétní transakce.",
    },
    "section_38nb_decision_effective": {
        "topic": "domestic_exemption",
        "prompt": "Ověřte splnění podmínek pro případné vnitrostátní osvobození.",
        "why": "Použití osvobození může vyžadovat další dokumentaci nebo rozhodnutí správce daně.",
    },
    "payment_not_attributable_to_disqualifying_pe": {
        "topic": "domestic_exemption",
        "prompt": "Ověřte splnění podmínek pro případné vnitrostátní osvobození.",
        "why": "Použití osvobození může vyžadovat další dokumentaci nebo rozhodnutí správce daně.",
    },
}

PROFESSIONAL_FACT_GROUPS.update({
    "recipient_country_imposes_royalty_wht_on_nonresidents": {
        "topic": "royalty_treaty_legal_condition",
        "prompt": (
            "Ověřte podmínku zdanění licenčních poplatků "
            "ve státě příjemce."
        ),
        "why": (
            "Jde o právní podmínku smlouvy závislou na daňovém "
            "režimu státu příjemce, nikoli o prostý skutkový údaj klienta."
        ),
    },
    "recipient_taxed_on_royalty_in_residence_state": {
        "topic": "royalty_treaty_legal_condition",
        "prompt": (
            "Ověřte zdanění licenčního příjmu ve státě "
            "rezidence příjemce."
        ),
        "why": (
            "Tato smluvní podmínka vyžaduje právní posouzení "
            "daňového režimu příjemce ve státě rezidence."
        ),
    },
})


REVIEW_REASON_GUIDANCE = {
    "beneficial_owner": (
        "Postavení skutečného vlastníka příjmu",
        "Zadané údaje nepotvrzují podmínku skutečného vlastníka příjmu, "
        "kterou vyžaduje posuzované smluvní pravidlo.",
    ),
    "recipient_is_treaty_resident": (
        "Daňové rezidentství příjemce",
        "Zadané údaje nepotvrzují daňové rezidentství příjemce ve státě, "
        "jehož smlouva má být použita.",
    ),
    "ownership_percent": (
        "Výše podílu na českém plátci",
        "Uvedený podíl nesplňuje hranici nejbližšího posuzovaného pravidla.",
    ),
    "direct_ownership": (
        "Přímé držení podílu",
        "Nejbližší posuzované pravidlo vyžaduje přímé držení podílu.",
    ),
    "direct_or_indirect_voting_ownership": (
        "Podíl na hlasovacích právech",
        "Uvedený podíl na hlasovacích právech nesplňuje hranici "
        "nejbližšího posuzovaného pravidla.",
    ),
    "holding_period_months": (
        "Doba držby podílu",
        "Uvedená doba držby nesplňuje časovou podmínku nejbližšího "
        "posuzovaného pravidla.",
    ),
    "arm_length_amount": (
        "Výše úroku mezi spojenými osobami",
        "Zadané údaje nepotvrzují, že výše úroku odpovídá obvyklým "
        "podmínkám.",
    ),
    "payment_is_arm_length_amount": (
        "Výše platby mezi spojenými osobami",
        "Zadané údaje nepotvrzují, že výše platby odpovídá obvyklým "
        "podmínkám.",
    ),
    "royalty_category": (
        "Předmět licenční platby",
        "Zvolený předmět licence neodpovídá podmínkám nejbližšího "
        "posuzovaného pravidla.",
    ),
    "recipient_is_qualifying_company_form": (
        "Právní forma příjemce pro osvobození",
        "Chybí potvrzení, zda příjemce splňuje podmínku kvalifikované právní formy pro vnitrostátní osvobození dividend.",
    ),
    "recipient_is_tax_resident_in_eligible_jurisdiction": (
        "Jurisdikce příjemce pro osvobození",
        "Je nutné potvrdit, že příjemce je rezidentem jurisdikce způsobilé pro vnitrostátní osvobození dividend.",
    ),
    "recipient_subject_to_qualifying_corporate_tax": (
        "Zdanění příjemce pro osvobození",
        "Chybí potvrzení, že příjemce podléhá kvalifikované dani z příjmů právnických osob ve státě své rezidence.",
    ),
    "recipient_has_no_tax_exemption_or_zero_rate_option": (
        "Daňové osvobození nebo nulová sazba příjemce",
        "Chybí potvrzení, že příjemce není od kvalifikované daně osvobozen ani nepodléhá režimu s nulovou sazbou.",
    ),
    "recipient_is_parent_company": (
        "Postavení mateřské společnosti",
        "Zadané údaje nepotvrzují, že jsou pro osvobození splněny podmínky kvalifikované mateřské společnosti.",
    ),
    "holding_period_will_reach_months": (
        "Budoucí splnění doby držby",
        "Pro tuto větev osvobození chybí potvrzení, že bude dosažena požadovaná minimální doba držby.",
    ),
    "statutory_clawback_acknowledged": (
        "Postup při dodatečném splnění doby držby",
        "Chybí údaj potřebný pro posouzení režimu při dodatečném splnění minimální doby držby.",
    ),
}


def _review_reason_for_fact(
    fact: str,
    request: Mapping[str, Any],
) -> dict[str, str]:
    income_type = str(request.get("income_type") or "")
    if fact == "permanent_establishment_connection":
        subject = {
            "dividend": "účast, ze které jsou dividendy vypláceny,",
            "interest": "pohledávka, ze které úrok plyne,",
            "royalty": "právo nebo majetek, za který licenční poplatek plyne,",
        }.get(income_type, "posuzovaný příjem")
        return {
            "code": fact,
            "title": "Vazba příjmu ke stálé provozovně v České republice",
            "detail": (
                f"Bylo uvedeno, že {subject} se skutečně váže ke stálé "
                "provozovně příjemce v České republice. Smluvní pravidlo "
                "pro tento druh příjmu se proto nepoužije a daňový režim "
                "musí být určen podle pravidel vztahujících se ke stálé "
                "provozovně."
            ),
        }
    title, detail = REVIEW_REASON_GUIDANCE.get(
        fact,
        (
            "Nesplněná podmínka právního pravidla",
            "Nejbližší posuzované pravidlo obsahuje podmínku, kterou "
            "zadané údaje nesplňují.",
        ),
    )
    return {"code": fact, "title": title, "detail": detail}


def build_review_reasons(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Explain why a non-final analysis cannot select a rate."""

    if str(analysis.get("status")) == "FINAL":
        return []

    layer_results = [
        result
        for result in analysis.get("layer_results", [])
        if result.get("outcome") != "applicable"
    ]
    blockers: set[str] = set()
    if layer_results:
        blocker_counts = [
            len(set(result.get("missing_facts", [])))
            + len(set(result.get("failed_conditions", [])))
            for result in layer_results
        ]
        positive_counts = [count for count in blocker_counts if count]
        if positive_counts:
            closest_count = min(positive_counts)
            for result, count in zip(layer_results, blocker_counts):
                if count == closest_count:
                    blockers.update(result.get("missing_facts", []))
                    blockers.update(result.get("failed_conditions", []))

    blockers.update(analysis.get("missing_facts", []))
    blockers.update(analysis.get("failed_conditions", []))
    reasons = [
        _review_reason_for_fact(str(fact).split(":", 1)[-1], request)
        for fact in sorted(blockers)
    ]
    for layer in analysis.get("missing_legal_layers", []):
        if layer == "historical_domestic_dividend_exemption":
            reasons.append(
                {
                    "code": f"missing_legal_layer:{layer}",
                    "title": "Historické vnitrostátní osvobození není pro zadané datum uvolněno",
                    "detail": (
                        "Skutkové údaje mohou být kompletní, ale TaxTreat pro zadané "
                        "historické datum nemá uvolněnou ověřenou vrstvu vnitrostátního "
                        "osvobození dividend. Smluvní výsledek proto nelze prezentovat "
                        "jako konečný právní titul."
                    ),
                }
            )
            continue
        reasons.append(
            {
                "code": f"missing_legal_layer:{layer}",
                "title": "Chybějící právní vrstva",
                "detail": (
                    "Pro uzavření výsledku chybí ověřené pravidlo právní "
                    "vrstvy nezbytné pro tuto transakci."
                ),
            }
        )
    if not reasons:
        reasons.append(
            {
                "code": "no_applicable_rule",
                "title": "Pro zadané údaje nebylo určeno použitelné pravidlo",
                "detail": (
                    "Žádné z ověřených pravidel pro zvolený stát, druh "
                    "příjmu a datum transakce nebylo možné na základě "
                    "zadaných údajů použít."
                ),
            }
        )
    return reasons


def _normalized_income_type(value: Any) -> str:
    income = str(value or "").lower()
    return {
        "dividends": "dividend",
        "royalties": "royalty",
    }.get(income, income)


def _stage6_condition_values(
    request: Mapping[str, Any],
    fact: str,
) -> list[Any]:
    """Return exact condition values used by the selected treaty package."""

    country = str(
        request.get("recipient_country")
        or ""
    ).lower()

    income_type = _normalized_income_type(
        request.get("income_type")
    )

    if not country or not income_type:
        return []

    path = STAGE6_RULE_DIR / f"{country}.json"

    if not path.is_file():
        return []

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    rules = payload.get(
        "rules",
        payload if isinstance(payload, list) else [],
    )

    values: list[Any] = []

    for rule in rules:
        if (
            _normalized_income_type(
                rule.get("income_type")
            )
            != income_type
        ):
            continue

        for condition in rule.get(
            "conditions",
            [],
        ):
            if condition.get("fact") != fact:
                continue

            value = condition.get("value")

            if value not in values:
                values.append(value)

    return values


def _rule_value_boolean_question(
    missing: str,
    name: str,
    request: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    Translate a human Yes/No answer to the exact enum value stored in
    the selected treaty's Stage 6 condition.

    If one country ever contains more than one value for the same fact,
    fail closed and require professional review rather than guessing.
    """

    guidance = RULE_VALUE_BOOLEAN_GUIDANCE.get(
        name
    )

    if guidance is None:
        return None

    # An explicit advisor-only classification in FACT_GUIDANCE is a hard
    # safety boundary. Dynamic enum-to-boolean translation must never turn
    # that legal judgement into a client Yes/No question merely because the
    # selected treaty happens to contain a single encoded value.
    explicit_guidance = FACT_GUIDANCE.get(name, {})
    if explicit_guidance.get("client_answerable") is False:
        return {
            "question_id": missing,
            "input_path": None,
            "category": "professional_review",
            "client_answerable": False,
            "response_type": "professional_review",
            "prompt": explicit_guidance.get(
                "prompt",
                guidance["prompt"],
            ),
            "why": explicit_guidance.get(
                "why",
                guidance["why"],
            ),
            "required_documents": explicit_guidance.get(
                "documents",
                ["Úvěrová nebo zápůjční smlouva"],
            ),
            "advisor_topic": explicit_guidance.get(
                "advisor_topic",
                "interest_treaty_special_condition",
            ),
        }

    values = _stage6_condition_values(
        request,
        name,
    )

    if len(values) != 1:
        return {
            "question_id": missing,
            "input_path": None,
            "category": "professional_review",
            "client_answerable": False,
            "response_type": "professional_review",
            "prompt": guidance["prompt"],
            "why": (
                "Pro zvolenou smlouvu existuje více možných právních "
                "variant této podmínky; je nutné odborné posouzení."
            ),
            "required_documents": [
                "Úvěrová nebo zápůjční smlouva"
            ],
            "advisor_topic": (
                "interest_treaty_special_condition"
            ),
        }

    return {
        "question_id": missing,
        "input_path": f"facts.{name}",
        "category": "transaction_fact",
        "client_answerable": True,
        "response_type": "boolean_rule_value",
        "prompt": guidance["prompt"],
        "why": guidance["why"],
        "required_documents": [
            "Úvěrová nebo zápůjční smlouva"
        ],
        "true_value": values[0],
        "false_value": "__not_applicable__",
    }


def _collapse_duplicate_input_questions(
    questions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Do not ask for acquisition date twice when one treaty uses months
    and another condition in the same path uses days or years.
    """

    collapsed: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for question in questions:
        input_path = question.get(
            "input_path"
        )

        if (
            question.get("client_answerable")
            and input_path
        ):
            key = (
                "client",
                input_path,
            )
        else:
            key = (
                "question",
                question.get("question_id"),
            )

        if key in seen:
            continue

        seen.add(key)
        collapsed.append(question)

    return collapsed


def _question_for_missing_fact(
    missing: str,
    request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = request or {}
    prefix = None
    name = missing
    if ":" in missing:
        prefix, name = missing.split(":", 1)

    if prefix == "legal_fact":
        return {
            "question_id": missing,
            "input_path": None,
            "category": "legal_evidence",
            "client_answerable": False,
            "response_type": "professional_review",
            "prompt": "Ověřte příslušnou podmínku podle dostupných podkladů.",
            "why": (
                "Podmínku nelze potvrdit pouze z klientského vstupu; projednejte "
                "ji s daňovým poradcem."
            ),
            "required_documents": [],
        }

    if prefix == "determination":
        guidance = DETERMINATION_GUIDANCE.get(name, {})
        return {
            "question_id": missing,
            "input_path": f"determinations.{name}",
            "category": "legal_determination",
            "client_answerable": False,
            "response_type": "reviewed_boolean",
            "prompt": guidance.get(
                "prompt",
                "Ověřte příslušnou podmínku s daňovým poradcem.",
            ),
            "why": guidance.get(
                "why",
                "Podmínku nelze potvrdit pouze ze zadaných údajů.",
            ),
            "required_documents": guidance.get("documents", []),
        }

    if name in DERIVED_TRANSACTION_FACTS:
        return {
            "question_id": missing,
            "input_path": None,
            "category": "derived_fact",
            "client_answerable": False,
            "response_type": "derived_fact",
            "prompt": (
                "Tento údaj se automaticky odvozuje z vazby příjmu "
                "ke stálé provozovně v České republice."
            ),
            "why": (
                "Uživatel jej nemá zadávat samostatně; TaxTreat jej "
                "odvozuje z již zadaného údaje o stálé provozovně."
            ),
            "required_documents": [],
            "derived_from": DERIVED_TRANSACTION_FACTS[name],
        }

    if name in RULE_CONTROL_FACTS:
        return {
            "question_id": missing,
            "input_path": None,
            "category": "rule_control",
            "client_answerable": False,
            "response_type": "internal_rule_control",
            "prompt": "Interní řídicí podmínka právního pravidla.",
            "why": (
                "Tato položka se uživateli nezadává; "
                "vyhodnocuje ji pravidlový engine."
            ),
            "required_documents": [],
        }

    dynamic = _rule_value_boolean_question(
        missing,
        name,
        request,
    )

    if dynamic is not None:
        return dynamic

    guidance = FACT_GUIDANCE.get(name)
    if guidance is None:
        professional = PROFESSIONAL_FACT_GROUPS.get(name, {})
        return {
            "question_id": missing,
            "input_path": None,
            "category": "professional_review",
            "client_answerable": False,
            "response_type": "professional_review",
            "prompt": professional.get(
                "prompt",
                "Ověřte další podmínku použití sazby s daňovým poradcem.",
            ),
            "why": professional.get(
                "why",
                "Interní podmínky pravidla se klientovi nezobrazují jako technické otázky.",
            ),
            "required_documents": [],
            "advisor_topic": professional.get("topic", "other_condition"),
        }

    client_answerable = guidance.get("client_answerable", True)
    return {
        "question_id": missing,
        "input_path": guidance.get("input_path", f"facts.{name}") if client_answerable else None,
        "category": "transaction_fact" if client_answerable else "professional_review",
        "client_answerable": client_answerable,
        "response_type": guidance.get("response_type", "boolean") if client_answerable else "professional_review",
        "prompt": guidance["prompt"],
        "why": guidance["why"],
        "required_documents": guidance.get("documents", []),
        "options": guidance.get("options", []),
        "advisor_topic": guidance.get("advisor_topic"),
    }


def _collapse_adviser_items(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collapsed: list[dict[str, Any]] = []
    adviser_by_topic: dict[str, dict[str, Any]] = {}
    for question in questions:
        topic = question.get("advisor_topic")
        if question["client_answerable"] or not topic:
            collapsed.append(question)
            continue
        existing = adviser_by_topic.get(topic)
        if existing is None:
            adviser_by_topic[topic] = question
            collapsed.append(question)
            continue
        existing["required_documents"] = sorted(
            set(existing["required_documents"])
            | set(question["required_documents"])
        )
    return collapsed


def build_intake_plan(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> dict[str, Any]:
    questions = _collapse_duplicate_input_questions(
        _collapse_adviser_items([
            _question_for_missing_fact(
                missing,
                request,
            )
            for missing in analysis.get(
                "missing_facts",
                [],
            )
        ])
    )

    calculation = analysis.get("withholding_tax_calculation")
    if (
        isinstance(calculation, Mapping)
        and calculation.get("status") == "NOT_CALCULATED"
        and calculation.get("reason")
        not in {None, "final_rate_unavailable"}
    ):
        questions.append(
            {
                "question_id": "transaction_amount.exchange_rate_evidence",
                "input_path": "transaction_amount",
                "category": "exchange_rate_evidence",
                "client_answerable": True,
                "response_type": "structured_cnb_rate",
                "prompt": (
                    "Automatický kurz ČNB se nepodařilo načíst. Doplňte kurz "
                    "v CZK za jednu jednotku zvolené měny."
                ),
                "why": (
                    "Použijte kurz ČNB pro rozhodné datum uvedené výše. Datum "
                    "ani odkaz na kurzovní lístek není třeba zadávat znovu."
                ),
                "required_documents": [
                    "Doklad o úhradě nebo zaúčtování",
                ],
            }
        )

    supplied_amount = request.get("transaction_amount")
    optional_inputs = []
    if supplied_amount is None:
        optional_inputs.append(
            {
                "input_path": "transaction_amount",
                "prompt": (
                    "Doplňte hrubou částku a měnu pro výpočet daně v CZK "
                    "po určení finální sazby."
                ),
            }
        )

    status = str(analysis.get("status"))
    if status == "OUT_OF_SCOPE":
        intake_status = "OUT_OF_SCOPE"
    elif questions:
        intake_status = "ACTION_REQUIRED"
    elif status == "FINAL":
        intake_status = "COMPLETE"
    else:
        intake_status = "PROFESSIONAL_REVIEW_REQUIRED"

    documents = sorted(
        {
            document
            for question in questions
            for document in question["required_documents"]
        }
    )
    return {
        "schema_version": 1,
        "status": intake_status,
        "analysis_status": status,
        "questions": questions,
        "required_documents": documents,
        "optional_inputs": optional_inputs,
        "review_reasons": build_review_reasons(request, analysis),
        "semantics": {
            "client_facts_are_not_legal_approval": True,
            "unanswered_items_remain_unresolved": True,
            "legal_determinations_require_review": True,
        },
    }
