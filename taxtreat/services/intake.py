from __future__ import annotations

from typing import Any, Mapping


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
            ["copyright_literary_artistic_or_scientific", "Autorské dílo"],
            ["software_patent_trademark_design_model_plan_secret_formula_process_knowhow_or_industrial_commercial_scientific_equipment", "Software, patent, ochranná známka nebo know-how"],
            ["industrial_commercial_or_scientific_equipment", "Průmyslové, obchodní nebo vědecké zařízení"],
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


def _question_for_missing_fact(missing: str) -> dict[str, Any]:
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
    questions = _collapse_adviser_items([
        _question_for_missing_fact(missing)
        for missing in analysis.get("missing_facts", [])
    ])

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
