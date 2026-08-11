import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
QUEUE = ROOT / "data/legal_reviews/global_cz_outbound/cz_country_qa_queue.json"

def packages():
    return {p["partner_country"]: p for p in json.loads(QUEUE.read_text(encoding="utf-8"))["packages"]}

def scope(p, income):
    return next(s for s in p["income_scopes"] if s["income_type"] == income)

def rates(s):
    return sorted(s["candidate_rates"])

def cond_types(s, rate):
    row = next(x for x in s["material_conditions"] if x["rate"] == rate)
    return {c["condition_type"] for c in row["conditions"]}

def test_final_human_review_elevated_corrections():
    p = packages()
    assert rates(scope(p["CL"], "interest")) == [4.0, 15.0]
    assert "detailed_eligibility_review_required" in cond_types(scope(p["CL"], "interest"), 4.0)
    assert rates(scope(p["CL"], "royalty")) == [5.0, 10.0]
    assert rates(scope(p["GB"], "royalty")) == [0.0, 10.0]
    assert rates(scope(p["GR"], "dividend")) == []
    assert rates(scope(p["GR"], "royalty")) == [0.0, 10.0]
    assert rates(scope(p["IT"], "royalty")) == [0.0, 5.0]
    assert rates(scope(p["NG"], "royalty")) == [15.0]
    assert rates(scope(p["RS"], "royalty")) == [5.0, 10.0]
    assert rates(scope(p["RU"], "dividend")) == [10.0]
    assert rates(scope(p["RU"], "interest")) == [0.0]
    assert rates(scope(p["RU"], "royalty")) == [10.0]
    assert rates(scope(p["SG"], "royalty")) == [0.0, 5.0, 10.0]
    assert rates(scope(p["TW"], "interest")) == [0.0, 10.0]
    assert "special_article_11_3_exemption" in cond_types(scope(p["TW"], "interest"), 0.0)
    assert rates(scope(p["UA"], "interest")) == [0.0, 5.0]
    assert rates(scope(p["UZ"], "dividend")) == [5.0, 10.0]

def test_final_human_review_preserves_suspension_and_fail_closed_release():
    p = packages()
    ru = json.dumps(p["RU"], ensure_ascii=False)
    by = json.dumps(p["BY"], ensure_ascii=False)
    assert "article_application_suspended" in ru
    assert "2023-08-11" in ru
    assert "article_application_suspended" in by
    assert "2024-06-01" in by
    assert p["GR"]["czech_domestic_wht"]
    assert p["RU"]["czech_domestic_wht"]
    for package in p.values():
        assert package["human_qa"]["status"] == "pending"
        assert package["release_state"]["production_releasable"] is False
        assert package["release_state"]["verified_scope_count"] == 0

def test_final_human_review_universe_is_101_303():
    p = packages()
    assert len(p) == 101
    assert sum(len(x["income_scopes"]) for x in p.values()) == 303
