from __future__ import annotations

from datetime import date

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalCondition,
    LegalRule,
    evaluate_legal_rules,
)


AS_OF = date(2026, 8, 28)


def _rule(
    rule_id: str,
    *,
    income_type: str,
    rate: float,
    priority: int,
    conditions: list[LegalCondition] | None = None,
    legal_layer: str = "treaty",
) -> LegalRule:
    return LegalRule(
        rule_id=rule_id,
        income_type=income_type,
        source_country="CZ",
        recipient_country="XX",
        legal_instrument="test treaty",
        legal_layer=legal_layer,
        article=10 if income_type == "dividend" else 12,
        rate=rate,
        priority=priority,
        conditions=conditions or [],
        verification_status="verified",
    )


def test_coarse_company_type_cannot_force_general_dividend_fallback():
    rules = [
        _rule(
            "special",
            income_type="dividend",
            rate=5,
            priority=100,
            conditions=[
                LegalCondition(
                    fact="recipient_entity_type",
                    operator="==",
                    value="company_other_than_partnership",
                ),
                LegalCondition(
                    fact="ownership_percent",
                    operator=">=",
                    value=20,
                ),
            ],
        ),
        _rule(
            "fallback",
            income_type="dividend",
            rate=15,
            priority=200,
            conditions=[
                LegalCondition(
                    fact="fallback_case",
                    operator="==",
                    value="all_other_cases",
                )
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "XX",
            "recipient_entity_type": "company",
            "ownership_percent": 100,
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == ["recipient_entity_type"]


def test_broad_royalty_value_matching_two_rates_fails_closed():
    rules = [
        _rule(
            "financial",
            income_type="royalty",
            rate=1,
            priority=100,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="financial_lease_of_equipment",
                )
            ],
        ),
        _rule(
            "operating",
            income_type="royalty",
            rate=5,
            priority=110,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="operating_lease_of_equipment_or_computer_software",
                )
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "XX",
            "royalty_category": "industrial_commercial_or_scientific_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == ["royalty_category"]


def test_atomic_royalty_value_selects_one_branch():
    rules = [
        _rule(
            "financial",
            income_type="royalty",
            rate=1,
            priority=100,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="financial_lease_of_equipment",
                )
            ],
        ),
        _rule(
            "operating",
            income_type="royalty",
            rate=5,
            priority=110,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="operating_lease_of_equipment_or_computer_software",
                )
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "XX",
            "royalty_category": "financial_lease_of_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.FINAL
    assert result.rate == 1
    assert result.selected_rule_id == "financial"


def test_advisor_only_rule_value_fact_stays_professional_review():
    from taxtreat.services.intake import _question_for_missing_fact

    question = _question_for_missing_fact(
        "special_article_11_3_exemption",
        {
            "source_country": "CZ",
            "recipient_country": "TW",
            "income_type": "interest",
            "transaction_date": "2026-08-28",
            "facts": {},
            "determinations": {},
        },
    )

    assert question["client_answerable"] is False
    assert question["response_type"] == "professional_review"
    assert question["input_path"] is None
    assert question["category"] == "professional_review"


def test_real_au_stage6_company_input_does_not_silently_select_15_percent():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/au.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "AU",
            "recipient_entity_type": "company",
            "ownership_percent": 100,
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert "recipient_entity_type" in result.missing_facts


def test_real_fi_stage6_broad_equipment_input_does_not_silently_select_1_percent():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/fi.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "FI",
            "beneficial_owner": True,
            "royalty_category": "industrial_commercial_or_scientific_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == ["royalty_category"]


def test_real_fi_stage6_atomic_financial_lease_selects_1_percent_treaty_rule():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/fi.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "FI",
            "beneficial_owner": True,
            "royalty_category": "financial_lease_of_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.FINAL
    assert result.rate == 1
    assert result.selected_rule_id == "CZ-FI-ROYALTY-CURRENT-2"


def test_simple_bank_enum_remains_client_answerable():
    from taxtreat.services.intake import _question_for_missing_fact

    question = _question_for_missing_fact(
        "loan_or_credit_provider",
        {
            "source_country": "CZ",
            "recipient_country": "AM",
            "income_type": "interest",
            "transaction_date": "2026-08-28",
            "facts": {},
            "determinations": {},
        },
    )

    assert question["client_answerable"] is True
    assert question["response_type"] == "boolean_rule_value"
    assert question["true_value"] == "bank"


def test_composite_interest_exemption_enum_requires_professional_review():
    from taxtreat.services.intake import _question_for_missing_fact

    question = _question_for_missing_fact(
        "article_11_3_exemption",
        {
            "source_country": "CZ",
            "recipient_country": "BE",
            "income_type": "interest",
            "transaction_date": "2026-08-28",
            "facts": {},
            "determinations": {},
        },
    )

    assert question["client_answerable"] is False
    assert question["response_type"] == "professional_review"
    assert question["input_path"] is None
    assert question["advisor_topic"] == "interest_treaty_special_condition"


def test_workspace_does_not_infer_voting_rights_from_capital_ownership():
    source = Path("app/web/workspace.js").read_text(encoding="utf-8")

    assert (
        "relationship.votingOwnershipPercent || relationship.ownershipPercent"
        not in source
    )
    assert (
        "voting_ownership_percent.value = form.elements.ownership_percent.value"
        not in source
    )


def test_workspace_resets_treaty_specific_answers_between_calculations():
    source = Path("app/web/workspace.js").read_text(encoding="utf-8")

    assert "function resetClientAnswers()" in source
    assert "clientAnswers.facts = {}" in source
    assert "clientAnswers.acquisitionDate = null" in source
    assert "clientAnswers.exchangeRate = null" in source
    assert 'resetClientAnswers();\n    showStep(1);' in source
    assert 'function renderTransactionFacts() {\n    resetClientAnswers();' in source


def _stage6_royalty_rules():
    import json

    for path in sorted(Path("data/legal_rules_stage6").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rules = payload.get("rules", []) if isinstance(payload, dict) else payload
        for rule in rules:
            if (
                rule.get("income_type") == "royalty"
                and rule.get("legal_layer") in {"treaty", "protocol", "mli"}
            ):
                yield path.stem.upper(), rule


def test_every_stage6_treaty_royalty_category_is_semantically_parseable():
    from taxtreat.engine.legal_rule_engine import _royalty_category_groups

    unparseable = []

    for country, rule in _stage6_royalty_rules():
        for condition in rule.get("conditions", []):
            if (
                condition.get("fact") == "royalty_category"
                and condition.get("operator") == "=="
            ):
                value = condition.get("value")
                if not _royalty_category_groups(value):
                    unparseable.append(
                        (country, rule.get("rule_id"), value)
                    )

    assert unparseable == []


def test_atomic_royalty_ui_does_not_collapse_distinct_rates_under_same_other_conditions():
    from taxtreat.engine.legal_rule_engine import _royalty_categories_match

    atomic_values = (
        "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
        "cinematographic_films_or_broadcast_media",
        "computer_software",
        "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
        "financial_lease_of_equipment",
        "operating_lease_or_other_use_of_equipment",
        "other",
    )
    control_facts = {
        "fallback_case",
        "source_state_taxation",
        "general_article_11_2_rate",
    }

    by_country = {}
    for country, rule in _stage6_royalty_rules():
        by_country.setdefault(country, []).append(rule)

    conflicts = []

    for country, rules in sorted(by_country.items()):
        for atomic in atomic_values:
            matched = []
            for rule in rules:
                category_conditions = [
                    condition
                    for condition in rule.get("conditions", [])
                    if (
                        condition.get("fact") == "royalty_category"
                        and condition.get("operator") == "=="
                    )
                ]
                if not category_conditions:
                    continue
                if not any(
                    _royalty_categories_match(
                        atomic,
                        condition.get("value"),
                    )
                    for condition in category_conditions
                ):
                    continue

                other_signature = tuple(
                    sorted(
                        (
                            condition.get("fact"),
                            condition.get("operator"),
                            repr(condition.get("value")),
                        )
                        for condition in rule.get("conditions", [])
                        if (
                            condition.get("fact") != "royalty_category"
                            and condition.get("fact") not in control_facts
                        )
                    )
                )
                matched.append(
                    (
                        other_signature,
                        rule.get("rate"),
                        rule.get("tax_treatment"),
                        rule.get("rule_id"),
                    )
                )

            grouped = {}
            for signature, rate, treatment, rule_id in matched:
                grouped.setdefault(signature, []).append(
                    (rate, treatment, rule_id)
                )

            for signature, outcomes in grouped.items():
                distinct = {
                    (rate, treatment)
                    for rate, treatment, _rule_id in outcomes
                }
                if len(distinct) > 1:
                    conflicts.append(
                        (
                            country,
                            atomic,
                            signature,
                            tuple(outcomes),
                        )
                    )

    assert conflicts == []


def test_spanish_all_other_royalty_branch_is_true_complement():
    from taxtreat.engine.legal_rule_engine import _royalty_category_groups

    groups = _royalty_category_groups("all_other_article_12_royalties")

    assert "copyright_nonfilm" not in groups
    assert {
        "film_broadcast",
        "software",
        "industrial_ip",
        "equipment_financial",
        "equipment_operating",
        "other",
    }.issubset(groups)


def test_real_gb_stage6_software_gap_fails_closed():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/gb.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "GB",
            "beneficial_owner": True,
            "royalty_category": "computer_software",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == ["royalty_category"]
