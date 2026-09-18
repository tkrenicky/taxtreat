import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADJUDICATION = ROOT / "data" / "legal_reviews" / "at_outbound" / "wht_secondary_source_adjudication_2026.json"
ADDENDUM = ROOT / "data" / "legal_reviews" / "at_outbound" / "wht_secondary_source_scope_addendum_2026.json"


def _claims():
    data = json.loads(ADJUDICATION.read_text(encoding="utf-8"))
    return data, {row["claim_id"]: row for row in data["claims"]}


def test_at_wht_adjudication_is_primary_source_controlled_and_fail_closed():
    data, claims = _claims()
    assert data["status"] == "independent_primary_source_adjudication_not_released"
    assert data["policy"]["secondary_source_never_controls_over_current_primary_law"] is True
    assert data["policy"]["substantive_entitlement_collection_at_payment_and_refund_are_separate"] is True
    assert data["summary"]["claim_count"] == 13
    assert data["summary"]["production_release_allowed"] is False
    assert len(claims) == 13


def test_at_corporate_interest_secondary_source_is_explicitly_corrected_to_current_section_98():
    _, claims = _claims()
    claim = claims["AT-WHT-INT-CORPORATE-98"]
    assert claim["adjudication"] == "corrected_current_law"
    assert "not received by natural persons" in claim["current_rule"]
    assert "four-part declaration" in claim["current_rule"]
    assert any("Paragraf=98" in url for url in claim["primary_sources"])


def test_at_royalty_net_expense_secondary_source_is_materially_corrected():
    _, claims = _claims()
    claim = claims["AT-WHT-ROY-NET-EXPENSES"]
    assert claim["adjudication"] == "materially_corrected_current_law"
    assert "EUR 2,463" in claim["current_rule"]
    assert "23% from 2024" in claim["current_rule"]
    assert "net-after-admissible-expenses" in claim["current_rule"]
    assert "20% gross route and 23% corporate net route" in claim["decision_impact"]


def test_at_swiss_article9_and_faster_dates_are_locked_in_evidence_ledger():
    _, claims = _claims()
    swiss = claims["AT-WHT-CH-ARTICLE9"]
    assert "renumbered Article 9" in swiss["current_rule"]
    assert "25%" in swiss["current_rule"]
    assert "two-year" in swiss["current_rule"]
    assert "More favourable DTT" in swiss["current_rule"]

    faster = claims["AT-WHT-FASTER"]
    assert faster["adjudication"] == "verified_future_only"
    assert "31 December 2028" in faster["current_rule"]
    assert "1 January 2030" in faster["current_rule"]
    assert "must not alter a 2026 AT result" in faster["decision_impact"]


def test_at_scope_addendum_keeps_residual_income_categories_out_of_runtime_and_pe_in_decision_dimensions():
    data = json.loads(ADDENDUM.read_text(encoding="utf-8"))
    items = {row["item_id"]: row for row in data["items"]}
    assert data["status"] == "scope_addendum_not_released"
    assert items["AT-WHT-ROY-PE-ASSESSMENT"]["classification"] == "in_scope_decision_dimension"
    assert "must never synthesize 0%" in items["AT-WHT-ROY-PE-ASSESSMENT"]["decision_rule"]
    for item_id in (
        "AT-WHT-SILENT-PARTNERSHIP",
        "AT-WHT-TECHNICAL-CONSULTING",
        "AT-WHT-SUPERVISORY-BOARD",
        "AT-WHT-REAL-ESTATE-GAINS",
    ):
        assert items[item_id]["classification"].startswith("out_of_current_product_scope")
    assert data["policy"]["out_of_scope_claims_do_not_create_new_transaction_types"] is True
