from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(recipient_country: str, income_type: str) -> dict:
    facts = {
        "recipient_entity_type": "company",
        "recipient_is_treaty_resident": True,
        "beneficial_owner": True,
        "permanent_establishment_connection": False,
        "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base": True,
        "claim_not_effectively_connected_to_czech_pe": True,
        "arm_length_amount": True,
        "related_party_status": "unrelated",
    }
    if income_type == "dividend":
        facts.update(
            {
                "ownership_percent": 100,
                "voting_ownership": 100,
                "direct_ownership": True,
                "holding_period_months": 24,
                "holding_period_will_reach_months": 24,
                "statutory_clawback_acknowledged": True,
                "recipient_is_qualifying_company_form": True,
                "recipient_is_tax_resident_in_eligible_jurisdiction": True,
                "recipient_subject_to_qualifying_corporate_tax": True,
                "recipient_has_no_tax_exemption_or_zero_rate_option": True,
                "recipient_is_parent_company": True,
            }
        )
    return {
        "source_country": "CZ",
        "recipient_country": recipient_country,
        "income_type": income_type,
        "transaction_date": "2026-09-02",
        "facts": facts,
        "determinations": {
            "treaty_ppt_passed": True,
            "mli_article_10_third_jurisdiction_pe_test_passed": True,
            "mli_article_12_dependent_agent_pe_status_resolved": True,
            "mli_article_13_specific_activity_pe_status_resolved": True,
            "mli_article_15_closely_related_enterprise_status_resolved": True,
        },
    }


def _question_ids(country: str, income_type: str) -> tuple[set[str], dict]:
    response = client.post("/analysis/intake", json=_payload(country, income_type))
    assert response.status_code == 200, response.text
    body = response.json()
    ids = {str(item.get("question_id")) for item in body.get("intake", {}).get("questions", [])}
    return ids, body


def test_panama_bank_reduced_rate_is_browser_reachable() -> None:
    ids, body = _question_ids("PA", "interest")
    assert "recipient_is_bank" in ids, body


def test_norway_partnership_branch_is_browser_reachable() -> None:
    ids, body = _question_ids("NO", "dividend")
    assert "recipient_is_partnership" in ids, body


def test_sweden_share_capital_branch_is_browser_reachable() -> None:
    ids, body = _question_ids("SE", "dividend")
    assert "recipient_has_share_capital" in ids, body
