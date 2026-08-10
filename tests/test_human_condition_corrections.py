import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
QUEUE = ROOT / "data/legal_reviews/global_cz_outbound/cz_country_qa_queue.json"

def packages():
    return {p["partner_country"]: p for p in json.loads(QUEUE.read_text(encoding="utf-8"))["packages"]}

def scope(p, income):
    return next(s for s in p["income_scopes"] if s["income_type"] == income)

def rates(s):
    return s["candidate_rates"]

def cond_types(s, rate):
    row = next(x for x in s["material_conditions"] if x["rate"] == rate)
    return {c["condition_type"] for c in row["conditions"]}

def cond_values(s, rate, condition_type):
    row = next(x for x in s["material_conditions"] if x["rate"] == rate)
    return {c["value"] for c in row["conditions"] if c["condition_type"] == condition_type}

def test_reviewer_condition_corrections_batch1_v2():
    p = packages()
    assert rates(scope(p["AU"], "dividend")) == [5.0, 15.0]
    assert sorted(rates(scope(p["AU"], "interest"))) == [0.0, 10.0]
    assert "official_foreign_exchange_reserve_investment" in cond_types(scope(p["AU"], "interest"), 0.0)
    assert sorted(rates(scope(p["AL"], "interest"))) == [0.0, 5.0]
    for country in ("AM", "AZ"):
        assert sorted(rates(scope(p[country], "interest"))) == [0.0, 5.0, 10.0]
    assert sorted(rates(scope(p["BD"], "interest"))) == [0.0, 10.0]
    assert sorted(rates(scope(p["BB"], "interest"))) == [0.0, 5.0]
    for country in ("AD", "AM", "BB"):
        s = scope(p[country], "royalty")
        assert all("royalty_category" in cond_types(s, r) for r in s["candidate_rates"])

    assert sorted(rates(scope(p["BW"], "interest"))) == [0.0, 7.5]
    assert "article_11_3_exemption" in cond_types(scope(p["BW"], "interest"), 0.0)

    assert sorted(rates(scope(p["BR"], "interest"))) == [0.0, 10.0, 15.0]
    assert "minimum_term_years" in cond_types(scope(p["BR"], "interest"), 10.0)
    assert "fallback_case" in cond_types(scope(p["BR"], "interest"), 15.0)
    assert "article_11_3a_exemption" in cond_types(scope(p["BR"], "interest"), 0.0)

    assert sorted(rates(scope(p["BR"], "royalty"))) == [15.0, 25.0]
    assert "trademark" in cond_values(scope(p["BR"], "royalty"), 25.0, "royalty_category")

    assert sorted(rates(scope(p["BG"], "interest"))) == [0.0, 10.0]
    assert "article_11_3_exemption" in cond_types(scope(p["BG"], "interest"), 0.0)

def test_no_human_or_release_promotion():
    for package in json.loads(QUEUE.read_text(encoding="utf-8"))["packages"]:
        assert package["human_qa"]["status"] == "pending"
        assert package["release_state"]["production_releasable"] is False
        assert package["release_state"]["verified_scope_count"] == 0
