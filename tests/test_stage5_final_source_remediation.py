import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_stage5_final_source_remediation.py"
OUTPUT = ROOT / "data/legal_reviews/global_cz_outbound/stage5_final10_source_remediation.json"
INDEX = ROOT / "data/legal_reviews/global_cz_outbound/stage5_human_review_package/index.json"
COUNTRIES = {"AT", "BH", "CH", "CL", "CO", "GH", "JP", "LU", "PA", "PL"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def builder():
    spec = importlib.util.spec_from_file_location("final10_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def review_scopes():
    index = load(INDEX)
    return [row for node in index["batch_files"] for row in load(ROOT / node["path"])["scopes"]]


def test_final10_evidence_matches_builder_and_has_exact_boundary():
    data = load(OUTPUT)
    assert data == builder().build()
    assert data["summary"] == {
        "human_verified_count": 0,
        "instrument_chain_candidate_assembled_count": 2,
        "instrument_chain_country_count": 2,
        "language_ambiguous_count": 0,
        "language_blocked_count": 0,
        "language_candidate_resolved_count": 10,
        "language_country_count": 10,
        "production_releasable_count": 0,
    }
    assert {row["country"] for row in data["language_authority_entries"]} == COUNTRIES


def test_language_candidates_are_official_hash_bound_and_not_verified():
    for row in load(OUTPUT)["language_authority_entries"]:
        source = row["official_source"]
        assert source["url"].startswith("https://aplikace.mv.gov.cz/")
        assert len(source["current_download_sha256"]) == 64
        assert len(source["archived_manifest_sha256"]) == 64
        assert source["hash_relation"] == "current_official_bytes_bound_archived_hash_preserved"
        clause = row["signature_clause_candidate"]
        assert hashlib.sha256(clause["machine_transcription"].encode()).hexdigest() == clause["transcription_sha256"]
        assert row["verification_status"] == "needs_review"
        assert row["human_primary_review_complete"] is False
        assert row["independent_approval_complete"] is False
        assert row["production_releasable"] is False
        assert row["fail_closed"] is True


def test_at_ch_instrument_chains_bind_base_protocol_correction_and_mli_primary_evidence():
    rows = {row["country"]: row for row in load(OUTPUT)["instrument_chain_entries"]}
    assert set(rows) == {"AT", "CH"}
    for country, row in rows.items():
        assert row["chain_status"] == "official_primary_instrument_chain_candidate_assembled"
        assert row["base_treaty"]["url"].startswith("https://aplikace.mv.gov.cz/")
        assert row["protocol"]["inventory"]["source_type"] == "protocol"
        assert row["protocol"]["effect_interpretation_status"] == "not_assessed_needs_human_review"
        assert row["correction_status_instrument"]["source_type"] == "correction"
        assert row["mli"]["inventory"]["source_type"] == "mli_synthesised_notice"
        assert row["mli"]["candidate_effect_record"]["verification_status"] == "needs_review"
        assert row["mli"]["matching_and_effect_interpretation_status"] == "candidate_only_needs_human_review"
        assert row["verification_status"] == "needs_review"
        assert row["production_releasable"] is False


def test_all_300_scopes_are_mechanically_ready_but_still_fail_closed():
    rows = review_scopes()
    assert len(rows) == 300
    assert len({row["recipient_country"] for row in rows}) == 100
    for row in rows:
        assert row["blocker_partition"] == "mechanically_complete_ready_for_human_review"
        assert row["source_remediation_blockers"] == []
        assert row["candidate_status"] == {
            "fail_closed": True,
            "production_releasable": False,
            "stage5_terminal_status": "pending",
            "verification_status": "needs_review",
        }
    at_ch = [row for row in rows if row["recipient_country"] in {"AT", "CH"}]
    assert len(at_ch) == 6
    assert all(row["protocol_overlays"]["candidate_effect"]["official_primary_evidence"] for row in at_ch)
    assert all(row["mli_evidence"]["candidate_effect"]["official_primary_evidence"] for row in at_ch)


def test_treaty_specific_article_invariants_remain_intact():
    rows = {row["scope_id"]: row for row in review_scopes()}
    for country, expected in {"AE": (11, 12, 13), "NG": (9, 10, 11)}.items():
        actual = tuple(rows[f"CZ-{country}-{income}"]["treaty_article"]["article_number"] for income in ("dividend", "interest", "royalty"))
        assert actual == expected
