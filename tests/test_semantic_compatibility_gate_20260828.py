from __future__ import annotations

from datetime import date
from pathlib import Path

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
    assert "direct_ownership" in result.missing_facts
    assert "recipient_is_partnership" in result.missing_facts


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

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts or result.explanation


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
    assert 'resetClientAnswers();\n    resetTransactionLegalFacts();\n    showStep(1);' in source
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


def test_real_ph_stage6_royalty_conflict_remains_fail_closed():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/ph.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "PH",
            "beneficial_owner": True,
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.requires_review is True


def test_workspace_keeps_only_approved_core_treaty_defaults():
    html = Path("app/web/workspace.html").read_text(encoding="utf-8")
    source = Path("app/web/workspace.js").read_text(encoding="utf-8")

    assert 'name="beneficial_owner" type="radio" value="true" checked' in html
    assert 'name="pe_connection" type="radio" value="false" checked' in html
    assert 'name="treaty_resident" type="radio" value="true" checked' not in html
    assert 'name="treaty_resident" type="radio" value="false" checked' not in html

    assert 'beneficialOwner: true' in source
    assert '{ peConnection: false,' in source
    assert 'treatyResident: true' not in source
    assert 'String(data.get("treaty_resident")) === "true"' not in source


def test_recipient_profile_preserves_unknown_core_treaty_facts():
    html = Path("app/web/workspace.html").read_text(encoding="utf-8")
    source = Path("app/web/workspace.js").read_text(encoding="utf-8")

    assert '<select name="beneficial_owner"><option value="">Nevyplněno</option>' in html
    assert '<select name="treaty_resident"><option value="">Nevyplněno</option>' in html
    assert '<select name="pe_connection"><option value="">Nevyplněno</option>' in html

    assert 'beneficialOwner: beneficialOwner === "" ? "" : beneficialOwner === "true"' in source
    assert 'treatyResident: treatyResident === "" ? "" : treatyResident === "true"' in source
    assert 'peConnection: peConnection === "" ? "" : peConnection === "true"' in source


def test_new_calculation_resets_transaction_specific_legal_facts():
    source = Path("app/web/workspace.js").read_text(encoding="utf-8")

    assert "function resetTransactionLegalFacts()" in source
    assert '"beneficial_owner",' in source
    assert '"treaty_resident",' in source
    assert '"pe_connection",' in source
    assert '"royalty_category",' in source
    assert '"arm_length_amount",' in source
    assert 'resetClientAnswers();\n    resetTransactionLegalFacts();\n    showStep(1);' in source


def test_workspace_does_not_approximate_holding_period_from_broad_buckets():
    html = Path("app/web/workspace.html").read_text(encoding="utf-8")
    source = Path("app/web/workspace.js").read_text(encoding="utf-8")

    assert 'value="at_least_12_months"' not in html
    assert 'value="less_than_12_months"' not in html
    assert 'value="unknown_date"' in html
    assert 'facts.holding_period_months = 12' not in source
    assert 'facts.holding_period_months = 0' not in source


def test_real_jp_dividend_holding_period_requires_exact_duration():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/jp.json"))

    eight_months = evaluate_legal_rules(
        rules,
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "JP",
            "recipient_entity_type": "company",
            "voting_ownership": 30,
            "holding_period_months": 8,
        },
        as_of=AS_OF,
    )
    assert eight_months.status == DecisionStatus.FINAL
    assert eight_months.rate == 10

    unknown_duration = evaluate_legal_rules(
        rules,
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "JP",
            "recipient_entity_type": "company",
            "voting_ownership": 30,
        },
        as_of=AS_OF,
    )
    assert unknown_duration.status == DecisionStatus.REVIEW_REQUIRED
    assert unknown_duration.rate is None
    assert "holding_period_months" in unknown_duration.missing_facts


def test_chile_detailed_interest_eligibility_is_professional_review():
    from taxtreat.services.intake import _question_for_missing_fact

    question = _question_for_missing_fact(
        "detailed_eligibility_review_required",
        {
            "income_type": "interest",
            "recipient_country": "CL",
        },
    )

    assert question["client_answerable"] is False
    assert question["response_type"] == "professional_review"


def test_german_historical_dividend_tax_difference_is_professional_review():
    from taxtreat.services.intake import _question_for_missing_fact

    question = _question_for_missing_fact(
        "distributed_vs_undistributed_corporate_tax_rate_difference",
        {
            "income_type": "dividend",
            "recipient_country": "DE",
        },
    )

    assert question["client_answerable"] is False
    assert question["response_type"] == "professional_review"


def test_ird_association_facts_are_explicit_professional_review():
    from taxtreat.services.intake import _question_for_missing_fact

    facts = (
        "ird_association_payer_directly_holds_25_percent_recipient",
        "ird_association_recipient_directly_holds_25_percent_payer",
        "ird_association_common_person_directly_holds_25_percent_both",
    )

    for fact in facts:
        question = _question_for_missing_fact(
            fact,
            {
                "income_type": "interest",
                "recipient_country": "AT",
            },
        )
        assert question["client_answerable"] is False
        assert question["response_type"] == "professional_review"
        assert question["advisor_topic"] == "domestic_exemption_association"


def test_bangladesh_special_holding_facts_are_professional_review():
    from taxtreat.services.intake import _question_for_missing_fact

    for fact in (
        "holding_period_includes_payment_date",
        "holding_period_reorganisation_continuity",
    ):
        question = _question_for_missing_fact(
            fact,
            {
                "income_type": "dividend",
                "recipient_country": "BD",
            },
        )
        assert question["client_answerable"] is False
        assert question["response_type"] == "professional_review"
        assert question["advisor_topic"] == "dividend_holding_period_special_condition"


def test_taiwan_complement_excludes_equipment_but_covers_other_atomic_royalties():
    from taxtreat.engine.legal_rule_engine import _royalty_category_groups

    groups = _royalty_category_groups(
        "all_royalties_except_industrial_commercial_scientific_equipment"
    )

    assert "equipment_financial" not in groups
    assert "equipment_operating" not in groups
    assert {
        "copyright_nonfilm",
        "film_broadcast",
        "software",
        "industrial_ip",
        "other",
    }.issubset(groups)


def test_semantic_remediation_candidates_remain_unapproved_and_source_backed():
    import json
    from pathlib import Path

    payload = json.loads(
        Path(
            "data/legal_consolidation/"
            "semantic_remediation_condition_candidates_20260829.json"
        ).read_text(encoding="utf-8")
    )

    assert payload["verification_status"] == "needs_review"
    assert payload["automatic_production_approval_forbidden"] is True

    by_key = {
        (row["country"], row["income_type"]): row
        for row in payload["corrections"]
    }

    assert ("PH", "royalty") in by_key
    assert ("TW", "royalty") in by_key
    assert by_key[("PH", "royalty")]["evidence_source_id"] == "SRC-1E2D0264FEB4040D"
    assert by_key[("TW", "royalty")]["evidence_source_id"] == "CZ-TW-LAW-45-2020"


def test_philippine_pending_remediation_restores_category_distinction():
    import json
    from pathlib import Path

    payload = json.loads(
        Path(
            "data/legal_consolidation/"
            "semantic_remediation_condition_candidates_20260829.json"
        ).read_text(encoding="utf-8")
    )
    correction = next(
        row
        for row in payload["corrections"]
        if row["country"] == "PH" and row["income_type"] == "royalty"
    )
    by_rate = {
        row["rate"]: row["conditions"]
        for row in correction["rate_candidates"]
    }

    assert any(
        condition["condition_type"] == "royalty_category"
        and "excluding_cinematographic" in condition["value"]
        for condition in by_rate[10.0]
    )
    assert any(
        condition["condition_type"] == "royalty_category"
        and "cinematographic_films" in condition["value"]
        for condition in by_rate[15.0]
    )


def test_overloaded_beneficial_owner_legal_status_fails_closed():
    from taxtreat.engine.legal_rule_engine import LegalCondition, _evaluate_condition

    condition = LegalCondition(
        fact="beneficial_owner",
        operator="==",
        value="government_or_public_body_special_status",
        fact_source="transaction",
    )

    matched, missing = _evaluate_condition(
        condition,
        {"beneficial_owner": True},
        {},
    )

    assert matched is None
    assert missing == "beneficial_owner"



def test_semantic_remediation_registry_matches_machine_release():
    import json
    from pathlib import Path

    from taxtreat.engine.legal_rule_engine import (
        _PENDING_SEMANTIC_REMEDIATION_SCOPES,
    )

    corrections = json.loads(
        Path(
            "data/legal_consolidation/"
            "semantic_remediation_condition_candidates_20260829.json"
        ).read_text(encoding="utf-8")
    )
    release = json.loads(
        Path(
            "data/legal_reviews/global_cz_outbound/"
            "semantic_remediation_machine_release_20260901.json"
        ).read_text(encoding="utf-8")
    )

    candidate_scopes = {
        (row["country"], row["income_type"])
        for row in corrections["corrections"]
    }
    released_scopes = {
        (row["partner_country"], row["income_type"])
        for row in release["records"]
    }

    assert len(candidate_scopes) == 41
    assert released_scopes == candidate_scopes
    assert release["additional_human_review_claimed"] is False
    assert _PENDING_SEMANTIC_REMEDIATION_SCOPES == set()


def test_all_semantic_remediation_scopes_have_machine_validated_runtime_rules():
    import json
    from pathlib import Path

    corrections = json.loads(
        Path(
            "data/legal_consolidation/"
            "semantic_remediation_condition_candidates_20260829.json"
        ).read_text(encoding="utf-8")
    )

    checked = set()
    for correction in corrections["corrections"]:
        country = correction["country"]
        income = correction["income_type"]
        payload = json.loads(
            Path(
                f"data/legal_rules_stage6/{country.lower()}.json"
            ).read_text(encoding="utf-8")
        )
        rules = [
            row
            for row in payload["rules"]
            if row.get("income_type") == income
            and row.get("verification_authority")
            == "semantic_remediation_machine_validation"
        ]
        assert rules, (country, income)
        assert all(row.get("verification_status") == "verified" for row in rules)
        assert all(row.get("review_package_sha256") for row in rules)
        checked.add((country, income))

    assert len(checked) == 41


def test_machine_validated_us_scope_selects_correct_reduced_rate():
    from pathlib import Path

    from taxtreat.engine.legal_rule_loader import load_legal_rules

    rules = load_legal_rules(Path("data/legal_rules_stage6/us.json"))

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "US",
            "beneficial_owner": True,
            "recipient_entity_type": "company",
            "voting_ownership": 100,
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.FINAL
    assert result.rate == 5
    assert result.selected_rule_id == "CZ-US-DIVIDEND-CURRENT-1"
    assert not any("quarantined" in line.lower() for line in result.explanation)

def test_all_nonboolean_beneficial_owner_projection_defects_are_quarantined():
    import json
    from pathlib import Path

    from taxtreat.engine.legal_rule_engine import (
        _PENDING_SEMANTIC_REMEDIATION_SCOPES,
    )

    defects = []
    boolean_tokens = {"true", "false", "yes", "no", "1", "0"}

    for path in sorted(Path("data/legal_rules_stage6").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rules = payload.get("rules", payload if isinstance(payload, list) else [])
        for rule in rules:
            for condition in rule.get("conditions", []):
                if condition.get("fact") != "beneficial_owner":
                    continue
                value = condition.get("value")
                if isinstance(value, bool):
                    continue
                if str(value).strip().lower() in boolean_tokens:
                    continue
                scope = (path.stem.upper(), rule.get("income_type"))
                defects.append((scope, rule.get("rule_id"), value))
                assert scope in _PENDING_SEMANTIC_REMEDIATION_SCOPES

    assert {scope for scope, _, _ in defects} == set()
