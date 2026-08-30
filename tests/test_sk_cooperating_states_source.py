from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from taxtreat.tools.build_sk_domestic_review_readiness import (
    cooperating_state_status,
    withholding_rate_candidate,
)
from taxtreat.tools.build_sk_prerelease_runtime_manifest import build_summary
from taxtreat.tools.build_sk_treaty_source_review_queue import build_queue
from taxtreat.tools.ingest_sk_cooperating_states import (
    BODY_PATH,
    canonical_code_for_source_name,
    parse_official_body,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "legal_reviews" / "sk_outbound" / "cooperating_states_source_2026.json"
MANIFEST_PATH = ROOT / "data" / "legal_reviews" / "sk_outbound" / "prerelease_runtime_manifest.json"
MATRIX_PATH = ROOT / "data" / "legal_reviews" / "sk_outbound" / "prerelease_decision_matrix_summary.json"


def _source():
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def test_official_2026_source_period_provenance_and_body_hash():
    source = _source()
    official = source["official_list"]
    assert (official["valid_from"], official["valid_to"]) == ("2026-01-01", "2026-12-31")
    assert official["mf_document_id"] == 49561
    assert official["landing_page_url"].startswith("https://www.mfsr.sk/")
    assert official["source_body_path"] == "data/legal_sources/slovak_mf_cooperating_states_2026/49561.pdf"
    assert official["source_body_sha256"] == "43e5a2732ef055bbc7de337b6776d73758894db423ce87197851f1c4a3cdbbaa"
    assert BODY_PATH.is_file()
    assert source["mapping_ambiguities"] == []


def test_representative_official_names_map_and_unknown_fails_closed():
    assert canonical_code_for_source_name("Česká republika") == "CZ"
    assert canonical_code_for_source_name("USA") == "US"
    assert canonical_code_for_source_name("Spojené kráľovstvo Veľkej Británie a Severného Írska") == "GB"
    with pytest.raises(ValueError, match="Unknown or ambiguous"):
        canonical_code_for_source_name("Neznámy štát")


def test_official_body_parses_all_entries_and_all_sk_destinations_reconcile():
    source = _source()
    parsed = parse_official_body(BODY_PATH.read_bytes())
    assert len(parsed) == 138
    assert source["cooperating_state_codes"] == [row["canonical_code"] for row in parsed]
    destinations = {row["recipient_country"] for row in build_queue()["relationships"]}
    assert destinations - set(source["cooperating_state_codes"]) == {"RU"}
    status = cooperating_state_status(
        recipient_country="RU",
        transaction_date=date(2026, 1, 1),
        source=source,
    )
    assert status["status"] == "resolved_from_official_annual_list"
    assert status["is_cooperating_state"] is False
    assert withholding_rate_candidate(
        recipient_country="RU",
        transaction_date=date(2026, 1, 1),
        source=source,
        domestic={"common": {"non_cooperative_state_rate_percent": 35, "standard_withholding_rate_percent": 19}},
    )["domestic_wht_rate_candidate"] == 35


def test_cooperating_list_does_not_supply_treaty_rates():
    source = _source()
    assert "treaty_rate" not in source
    assert "treaty_rates" not in source
    semantic = json.loads((ROOT / "data/legal_reviews/sk_outbound/treaty_semantic_candidates.json").read_text(encoding="utf-8"))
    cz_dividend = next(row for row in semantic["scopes"] if row["recipient_country"] == "CZ" and row["income_type"] == "dividend")
    assert cz_dividend["rate_candidates"]
    assert all("cooperating" not in str(candidate).lower() for candidate in cz_dividend["rate_candidates"])


def test_regenerated_runtime_and_matrix_counts_and_cz_regression():
    manifest_summary = build_summary(json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    assert manifest_summary["cooperating_state_list_ready_scopes"] == 225
    assert matrix["scopes_blocked_by_cooperating_state_list"] == 0
    assert matrix["evaluated_scopes"] == 225
    assert matrix["review_required_scopes"] == 225
    assert matrix["production_released_scopes"] == 0
    assert matrix["fail_closed"] is True
    assert json.loads((ROOT / "data/legal_reviews/sk_outbound/source_country_release_manifest.json").read_text(encoding="utf-8"))["source_country"] == "SK"
