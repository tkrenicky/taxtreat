import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_stage5_remaining70_candidate_evidence.py"
EVIDENCE_DIR = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining70_candidate_evidence"
)
INDEX = EVIDENCE_DIR / "index.json"
COVERAGE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_candidate_coverage_registry.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_builder():
    spec = importlib.util.spec_from_file_location("remaining70_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_evidence():
    index = load(INDEX)
    entries = [
        entry
        for batch_file in index["batch_files"]
        for entry in load(ROOT / batch_file["path"])["entries"]
    ]
    return index | {"entries": entries}


def test_generated_remaining70_evidence_and_coverage_match_builder():
    module = load_builder()
    evidence = module.build()
    payloads = module.build_batch_payloads(evidence)
    index = module.build_index(evidence, payloads)
    assert load(INDEX) == index
    for relative, payload in payloads.items():
        assert load(ROOT / relative) == payload
    assert load(COVERAGE) == module.build_coverage(evidence, payloads, index)


def test_remaining70_has_exact_large_batch_boundary_and_210_scopes():
    data = load_evidence()
    assert data["batch_boundary"]["country_count"] == 70
    assert data["batch_boundary"]["scope_count"] == 210
    assert len(data["batch_boundary"]["included_batch_ids"]) == 7
    assert data["batch_boundary"]["excluded_completed_batch_id"] == "stage5_remaining80_batch_01"
    assert len(data["entries"]) == 70
    scopes = [scope for entry in data["entries"] for scope in entry["scopes"]]
    assert len(scopes) == 210
    assert len({scope["scope_id"] for scope in scopes}) == 210


def test_every_remaining70_source_and_treaty_heading_article_is_resolved():
    data = load_evidence()
    assert data["summary"]["source_resolution_counts"] == {"resolved": 70}
    assert data["summary"]["treaty_heading_resolved_article_count"] == 210
    assert data["summary"]["treaty_heading_unresolved_article_count"] == 0
    for entry in data["entries"]:
        assert entry["canonical_treaty_source_resolution"]["status"] == "resolved"
        for income, article in entry["article_evidence"].items():
            assert article["income_type"] == income
            assert article["resolved"] is True
            assert article["resolution_status"] == "resolved"
            assert article["evidence_count"] == 1
            assert article["evidence"][0]["resolution_method"] == "structured_income_heading_and_article_number"


def test_extended_and_treaty_specific_headings_are_supported_without_number_assumption():
    rows = {entry["country"]: entry for entry in load_evidence()["entries"]}
    for country in ("BD", "IN", "LK", "PK", "RW", "VE"):
        assert rows[country]["article_evidence"]["royalty"]["article_number"] == 12
    assert rows["SA"]["article_evidence"]["interest"]["article_number"] == 11
    assert rows["SA"]["article_evidence"]["interest"]["evidence"][0]["heading"] == "PŘÍJMY Z POHLEDÁVEK"


def test_all_210_frozen_references_are_present_and_no_hash_was_changed():
    data = load_evidence()
    assert data["summary"]["frozen_candidate_chain_reference_count"] == 210
    assert data["summary"]["article_number_conflict_count"] == 0
    assert data["article_number_conflicts"] == []
    for relative, expected in data["source_hashes"].items():
        assert sha256(ROOT / relative) == expected
    for entry in data["entries"]:
        for scope in entry["scopes"]:
            reference = scope["frozen_candidate_chain_reference"]
            assert reference is not None
            assert reference["reference_only"] is True
            assert reference["verification_status"] == "needs_review"


def test_missing_clean_checkout_raw_bytes_remain_fail_closed():
    data = load_evidence()
    for entry in data["entries"]:
        source = entry["canonical_treaty_source_resolution"]["source"]
        artifact = ROOT / source["artifact_uri"]
        if artifact.is_file():
            assert source["artifact_hash_valid"] is True
            assert sha256(artifact) == source["archived_manifest_sha256"]
        else:
            assert source["artifact_bytes_present"] is False
            assert source["artifact_hash_valid"] is False
            assert source["artifact_hash_relation"] == "not_comparable"
            assert "archived_artifact_bytes_unavailable_fresh_official_extraction_required" in entry["review_blockers"]


def test_signature_clause_candidates_are_evidence_not_interpretation():
    data = load_evidence()
    counts = data["summary"]["signature_clause_status_counts"]
    assert sum(counts.values()) == 70
    assert counts["single_candidate_needs_review"] == 49
    assert counts["ambiguous_multiple_candidates"] == 5
    assert counts["unresolved"] == 16
    for entry in data["entries"]:
        language = entry["signature_clause_evidence"]
        assert language["interpretation_status"] == "not_assessed_needs_human_review"
        for candidate in language["candidates"]:
            assert hashlib.sha256(candidate["exact_excerpt"].encode("utf-8")).hexdigest() == candidate["excerpt_sha256"]


def test_coverage_registry_has_candidate_references_for_all_300_scopes_only():
    data = load(COVERAGE)
    assert data["coverage"] == {
        "candidate_evidence_present_scope_count": 300,
        "country_count": 100,
        "human_primary_review_complete_scope_count": 0,
        "independent_approval_complete_scope_count": 0,
        "production_releasable_scope_count": 0,
        "scope_count": 300,
        "terminal_status_counts": {"blocked": 0, "pending": 300, "verified": 0},
        "verification_status_counts": {"needs_review": 300},
    }
    assert len(data["scopes"]) == 300
    assert len({scope["scope_id"] for scope in data["scopes"]}) == 300
    for scope in data["scopes"]:
        assert scope["candidate_coverage_status"] == "candidate_evidence_present_needs_review"
        assert scope["verification_status"] == "needs_review"
        assert scope["production_releasable"] is False
        assert scope["human_primary_review_complete"] is False
        assert scope["independent_approval_complete"] is False
        assert scope["fail_closed"] is True
