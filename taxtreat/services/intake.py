from __future__ import annotations

from typing import Any, Mapping


FACT_GUIDANCE: dict[str, dict[str, Any]] = {
    "beneficial_owner": {
        "prompt": "Je příjemce skutečným vlastníkem příjmu?",
        "why": "Uplatnění smlouvy obvykle závisí na postavení skutečného vlastníka příjmu.",
        "documents": [
            "Prohlášení skutečného vlastníka příjmu",
            "Relevantní smlouvy a doklady o toku platby",
        ],
    },
    "recipient_is_treaty_resident": {
        "prompt": "Je příjemce daňovým rezidentem pro účely smlouvy?",
        "why": "Použití smlouvy vyžaduje doložené daňové rezidentství.",
        "documents": ["Aktuální potvrzení o daňovém rezidentství"],
    },
    "permanent_establishment_connection": {
        "prompt": (
            "Souvisí právo nebo majetek se stálou provozovnou "
            "v České republice?"
        ),
        "why": "Vazba na stálou provozovnu může změnit daňový režim.",
        "documents": [
            "Organizační struktura",
            "Analýza stálé provozovny",
        ],
    },
    "arm_length_amount": {
        "prompt": "Odpovídá celá výše platby principu tržního odstupu?",
        "why": "Smluvní limit se může vztahovat pouze na částku odpovídající principu tržního odstupu.",
        "documents": [
            "Vnitroskupinová smlouva",
            "Dokumentace k převodním cenám",
        ],
    },
    "payment_is_arm_length_amount": {
        "prompt": "Je platba omezena na částku odpovídající principu tržního odstupu?",
        "why": "Nadlimitní část mezi spojenými osobami může mít odlišný daňový režim.",
        "documents": [
            "Vnitroskupinová smlouva",
            "Dokumentace k převodním cenám",
        ],
    },
    "ownership_percent": {
        "prompt": "Jaký procentní podíl příjemce drží?",
        "why": "Výše podílu může rozhodnout o použití snížené sazby z dividend.",
        "response_type": "decimal_percent",
        "documents": [
            "Výpis z evidence podílů nebo akcií",
            "Schéma vlastnické struktury",
        ],
    },
    "direct_ownership": {
        "prompt": "Je kvalifikovaný podíl držen přímo?",
        "why": "Některá osvobození nebo snížené sazby vyžadují přímé vlastnictví.",
        "documents": ["Výpis z evidence podílů nebo akcií", "Schéma vlastnické struktury"],
    },
    "direct_or_indirect_voting_ownership": {
        "prompt": "Jaký přímý nebo nepřímý podíl na hlasovacích právech příjemce drží?",
        "why": "Smluvní hranice sazby mohou vycházet z podílu na hlasovacích právech.",
        "response_type": "decimal_percent",
        "documents": ["Výpis z evidence podílů nebo akcií", "Schéma vlastnické struktury"],
    },
    "holding_period_months": {
        "prompt": "Kolik celých měsíců je podíl držen?",
        "why": "Může být vyžadována minimální doba držby.",
        "response_type": "integer",
        "documents": [
            "Doklady o nabytí podílu",
            "Datovaný výpis z evidence podílů nebo akcií",
        ],
    },
    "holding_period_will_reach_months": {
        "prompt": "Bude požadovaná doba držby splněna?",
        "why": "Některé zvýhodnění může záviset na následném splnění doby držby.",
        "documents": ["Doklad o datu nabytí a předpokládané době držby"],
    },
    "recipient_entity_type": {
        "prompt": "Jaká je právní forma a daňová klasifikace příjemce?",
        "why": "Právní forma může rozhodnout o nároku na osvobození nebo sníženou sazbu.",
        "response_type": "text",
        "documents": [
            "Výpis z obchodního rejstříku",
            "Zakladatelské dokumenty",
        ],
    },
    "recipient_is_qualifying_company_form": {
        "prompt": "Má příjemce kvalifikovanou právní formu společnosti?",
        "why": "Režim EU vyžaduje způsobilou právní formu.",
        "documents": [
            "Výpis z obchodního rejstříku",
            "Zakladatelské dokumenty",
        ],
    },
    "recipient_subject_to_qualifying_corporate_tax": {
        "prompt": (
            "Podléhá příjemce kvalifikované dani z příjmů právnických osob bez "
            "možnosti volitelného osvobození?"
        ),
        "why": "Režim EU vyžaduje kvalifikované postavení daňového subjektu.",
        "documents": [
            "Potvrzení o daňovém postavení",
            "Potvrzení o daňovém rezidentství",
        ],
    },
    "royalty_category": {
        "prompt": "Která právní kategorie nejlépe vystihuje licenční poplatek?",
        "why": "Různé kategorie licenčních poplatků mohou podléhat odlišným ustanovením.",
        "response_type": "text",
        "documents": ["Licenční smlouva", "Popis licencovaných práv"],
    },
    "special_article_11_3_exemption": {
        "prompt": "Uplatní se zvláštní osvobození úroků podle čl. 11 odst. 3?",
        "why": "Zvláštní smluvní osvobození může nahradit obecnou sazbu.",
        "documents": ["Úvěrová nebo zápůjční smlouva", "Doklady k uplatňovanému osvobození"],
    },
}

DETERMINATION_GUIDANCE = {
    "treaty_ppt_passed": {
        "prompt": "Byl odborně posouzen a splněn test hlavního účelu podle smlouvy?",
        "why": "Test hlavního účelu je právní závěr; nelze jej dovodit pouze z tvrzení klienta.",
        "documents": [
            "Memorandum k účelu transakce",
            "Doklady o ekonomické podstatě a obchodním důvodu",
        ],
    },
}


def _humanize(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


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
            "prompt": f"Ověřte právní skutečnost: {_humanize(name)}.",
            "why": (
                "Tato položka musí vycházet z ověřeného právního podkladu nebo "
                "odborného posouzení, nikoli pouze z tvrzení klienta."
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
                f"Bylo odborně posouzeno: {_humanize(name).lower()}?",
            ),
            "why": guidance.get(
                "why",
                "Jde o výslovný právní závěr, nikoli o automaticky dovozenou skutečnost.",
            ),
            "required_documents": guidance.get("documents", []),
        }

    guidance = FACT_GUIDANCE.get(name, {})
    return {
        "question_id": missing,
        "input_path": f"facts.{name}",
        "category": "transaction_fact",
        "client_answerable": True,
        "response_type": guidance.get("response_type", "boolean"),
        "prompt": guidance.get(
            "prompt",
            f"Doplňte prosím: {_humanize(name)}.",
        ),
        "why": guidance.get(
            "why",
            "Uvolněné pravidlo vyžaduje tuto skutkovou informaci o transakci.",
        ),
        "required_documents": guidance.get("documents", []),
    }


def build_intake_plan(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> dict[str, Any]:
    questions = [
        _question_for_missing_fact(missing)
        for missing in analysis.get("missing_facts", [])
    ]

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
                    "Doplňte datum úhrady, datum zaúčtování a doložený kurz ČNB "
                    "pro dřívější z těchto dat."
                ),
                "why": (
                    "Daň z částky v cizí měně musí být přepočtena na CZK "
                    "pomocí příslušného doloženého kurzu."
                ),
                "required_documents": [
                    "Odkaz na zdroj kurzu ČNB",
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
        "semantics": {
            "client_facts_are_not_legal_approval": True,
            "unanswered_items_remain_unresolved": True,
            "legal_determinations_require_review": True,
        },
    }
