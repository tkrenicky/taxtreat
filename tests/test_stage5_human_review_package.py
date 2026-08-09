import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_stage5_human_review_package.py"
LANGUAGE_BUILDER = ROOT / "scripts/build_stage5_language_remediation.py"
INDEX = ROOT / "data/legal_reviews/global_cz_outbound/stage5_human_review_package/index.json"
BLOCKERS = ROOT / "data/legal_reviews/global_cz_outbound/stage5_global_blocker_registry.json"
LANGUAGE = ROOT / "data/legal_reviews/global_cz_outbound/stage5_language_authority_remediation.json"
FINAL23_AGGREGATE_SHA256 = "3140c31835596f00686f9ad99fc2cddaf43c185ab94a73c94bccf993fe159486"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(value)
    return value


def scopes():
    index = load(INDEX)
    return [row for node in index["batch_files"] for row in load(ROOT / node["path"])["scopes"]]


def test_language_remediation_is_reproducible_and_all_23_named_gaps_are_classified():
    data = load(LANGUAGE)
    assert data == module(LANGUAGE_BUILDER, "stage5_language_builder").build()
    assert data["summary"]["country_count"] == 23
    assert data["summary"]["resolved_candidate_evidence_count"] == 23
    assert data["summary"]["ambiguous_count"] == 0
    assert data["summary"]["blocked_count"] == 0
    assert data["summary"]["former_gap_counts"] == {
        "ambiguous_multiple_candidates": 5,
        "source_hash_conflict": 2,
        "unresolved": 16,
    }
    for row in data["entries"]:
        assert row["official_source"]["url"].startswith("https://aplikace.mv.gov.cz/")
        assert len(row["official_source"]["current_download_sha256"]) == 64
        clause = row["signature_clause_candidate"]
        assert hashlib.sha256(clause["machine_transcription"].encode()).hexdigest() == clause["transcription_sha256"]
        assert row["verification_status"] == "needs_review"
        assert row["production_releasable"] is False


def test_complete_package_and_blocker_registry_reconcile_exactly_to_100_and_300():
    builder = module(BUILDER, "stage5_package_builder")
    built = builder.build()
    rows = scopes()
    assert len(rows) == 300
    assert len({row["scope_id"] for row in rows}) == 300
    assert len({row["recipient_country"] for row in rows}) == 100
    assert built["summary"] == load(INDEX)["summary"] == load(BLOCKERS)["summary"]
    assert built["summary"]["partition_counts"] == {
        "genuine_legal_ambiguity_requires_human_determination": 0,
        "mechanically_complete_ready_for_human_review": 270,
        "source_remediation_required": 30,
    }
    assert sum(built["summary"]["partition_counts"].values()) == 300
    blocker_counts = {}
    for row in load(BLOCKERS)["scopes"]:
        for blocker in row["blockers"]:
            blocker_counts[blocker] = blocker_counts.get(blocker, 0) + 1
    assert blocker_counts == {
        "instrument_chain_consolidation_required": 6,
        "language_authority_primary_source_remediation_required": 30,
    }


def test_committed_human_review_batches_match_the_builder():
    built = module(BUILDER, "stage5_package_reproducibility_builder").build()
    index = load(INDEX)
    for offset, node in enumerate(index["batch_files"]):
        expected = {key: value for key, value in built.items() if key != "scopes"}
        expected["batch_id"] = f"stage5-human-review-{offset + 1:02d}"
        expected["scopes"] = built["scopes"][offset * 30:(offset + 1) * 30]
        path = ROOT / node["path"]
        assert load(path) == expected
        assert hashlib.sha256(path.read_bytes()).hexdigest() == node["sha256"]


def test_every_scope_contains_all_review_layers_or_an_explicit_blocker():
    required = {
        "canonical_treaty", "treaty_article", "protocol_overlays",
        "treaty_status_instruments", "mli_evidence", "effective_date_evidence",
        "language_authority_evidence", "domestic_czech_wht_layer",
        "eu_directive_layer", "unresolved_legal_questions", "provenance",
        "candidate_status", "future_human_review_checklist",
    }
    for row in scopes():
        assert required <= row.keys()
        assert row["canonical_treaty"]["authority_class"] == "official"
        assert row["canonical_treaty"]["official_urls"]
        assert row["treaty_article"]["exact_candidate_excerpt"]
        assert row["treaty_article"]["resolution_method"] == "structured_income_heading_and_article_number"
        assert row["effective_date_evidence"]["inventory_entry_into_force_candidate"]
        language = row["language_authority_evidence"]
        assert language["machine_evidence_located"] or language["blockers"]
        protocol = row["protocol_overlays"]
        assert protocol["candidate_effect"].get("candidate_status")
        if protocol["inventory_protocol_listed"]:
            assert any(node["source_type"] == "protocol" for node in protocol["inventory_related_instruments"])
        mli = row["mli_evidence"]
        assert mli["candidate_effect"].get("status")
        assert row["treaty_status_instruments"].get("candidate_status")
        assert row["effective_date_evidence"]["interpretation_status"] == "not_assessed_needs_human_review"


def test_article_numbers_are_treaty_specific_and_no_global_model_sequence_is_used():
    by_scope = {row["scope_id"]: row for row in scopes()}
    assert [by_scope[f"CZ-AE-{income}"]["treaty_article"]["article_number"] for income in ("dividend", "interest", "royalty")] == [11, 12, 13]
    assert [by_scope[f"CZ-NG-{income}"]["treaty_article"]["article_number"] for income in ("dividend", "interest", "royalty")] == [9, 10, 11]
    sequences = {
        tuple(by_scope[f"CZ-{country}-{income}"]["treaty_article"]["article_number"] for income in ("dividend", "interest", "royalty"))
        for country in {row["recipient_country"] for row in by_scope.values()}
    }
    assert (10, 11, 12) in sequences
    assert (11, 12, 13) in sequences
    assert (9, 10, 11) in sequences
    assert len(sequences) >= 3


def test_no_review_approval_verification_or_release_is_fabricated():
    for row in scopes():
        status = row["candidate_status"]
        assert status == {"fail_closed": True, "production_releasable": False, "stage5_terminal_status": "pending", "verification_status": "needs_review"}
        checklist = row["future_human_review_checklist"]
        assert checklist["primary_review_complete"] is False
        assert checklist["independent_approval_complete"] is False
        for key, value in checklist.items():
            if not key.endswith("_complete"):
                assert value is None


def test_frozen_remaining294_and_final23_candidate_bytes_are_unchanged():
    execution = load(ROOT / "data/legal_consolidation/stage5_execution_manifest.json")
    for relative, expected in execution["frozen_remaining_294_hashes"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    digest = hashlib.sha256()
    for path in sorted((ROOT / "data/legal_rule_candidates/final23").glob("*.json")):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    assert digest.hexdigest() == FINAL23_AGGREGATE_SHA256


def test_generated_package_does_not_depend_on_gitignored_raw_artifacts():
    source = BUILDER.read_text(encoding="utf-8")
    assert "data/raw" not in source
    assert all("data/raw" not in node["path"] for node in load(INDEX)["batch_files"])
