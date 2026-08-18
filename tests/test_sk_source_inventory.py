import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_sk_primary_source_inventory_contract():
    inventory = _load("data/legal_reviews/sk_outbound/source_inventory.json")

    assert inventory["source_country"] == "SK"
    assert inventory["status"] == "discovery_only_not_released"
    assert inventory["scope"]["treaty_partner_count"] == 75
    assert inventory["scope"]["treaty_scope_count"] == 225
    assert inventory["scope"]["mli_modified_relationship_count"] == 46

    source_ids = {
        source["source_id"]
        for source in inventory["primary_sources"]
    }
    assert source_ids == {
        "SK-MF-DTT-LIST",
        "SK-MF-MLI-STATUS",
        "SK-SLOVLEX-ZDP-595-2003",
    }


def test_sk_domestic_seed_cannot_be_mistaken_for_runtime_release():
    seed = _load("data/legal_reviews/sk_outbound/domestic_wht_seed.json")

    assert seed["source_country"] == "SK"
    assert seed["status"] == "needs_consolidation_not_released"
    assert seed["law"]["effective_version_from"] == "2026-01-01"
    assert seed["law"]["effective_version_to"] == "2026-12-30"

    for income_type in ("dividend", "interest", "royalty"):
        assert seed["income_types"][income_type]["status"] == "not_released"

    serialized = json.dumps(seed, ensure_ascii=False)
    assert '"rate"' not in serialized
    assert '"final_rate"' not in serialized


def test_sk_domestic_candidates_are_structured_but_not_released():
    candidate = _load(
        "data/legal_reviews/sk_outbound/domestic_wht_candidates.json"
    )

    assert candidate["source_country"] == "SK"
    assert candidate["status"] == "candidate_not_released"
    assert candidate["recipient_scope"] == "corporate_recipient_model_seed"

    common = candidate["common"]
    assert common["standard_withholding_rate_percent"] == 19
    assert common["non_cooperative_state_rate_percent"] == 35
    assert common["runtime_status"] == "not_released"

    dividend = candidate["income_types"]["dividend"]
    assert dividend["non_cooperative_recipient_exception"]["rate_percent"] == 35

    interest = candidate["income_types"]["interest"]
    royalty = candidate["income_types"]["royalty"]
    for item in (interest, royalty):
        assert item["standard_rate_percent"] == 19
        assert item["non_cooperative_state_rate_percent"] == 35
        assert item["eu_relief"]["conditions"]["direct_capital_percent_min"] == 25
        assert item["eu_relief"]["conditions"]["holding_period_months_min"] == 24
        assert item["eu_relief"]["conditions"]["holding_period_can_complete_after_payment"] is True
        assert item["runtime_status"] == "not_released"

    assert len(candidate["release_blockers"]) >= 6
