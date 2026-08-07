import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PATH = ROOT / "data/legal_reviews/global_cz_outbound/all_23_status_instrument_reconciliation.json"

def load():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_reconciliation_is_fail_closed():
    data = load()
    assert data["final_23_pair_count"] == 23
    assert data["fail_closed"] is True

def test_belarus_dividend_and_interest_suspension_detected():
    data = load()
    rows = {
        (row["treaty_pair_id"], row["income_type"]): row
        for row in data["records"]
    }

    for income in ("dividend", "interest"):
        row = rows[("CZ-BY", income)]
        assert row["candidate_status"] == "article_application_suspended"
        assert row["effective_from"] == "2024-06-01"
        assert row["effective_to"] == "2026-12-31"

def test_belarus_royalty_not_suspended():
    data = load()
    row = next(
        row for row in data["records"]
        if row["treaty_pair_id"] == "CZ-BY"
        and row["income_type"] == "royalty"
    )
    assert row["candidate_status"] == "article_not_suspended_by_notice"

def test_status_records_are_not_verified_candidates():
    data = load()
    assert all(
        row["chain_verification_status"] != "verified"
        for row in data["records"]
    )
