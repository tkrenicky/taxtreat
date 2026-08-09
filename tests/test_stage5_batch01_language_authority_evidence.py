import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_language_authority_evidence.json"
)
BUILDER = ROOT / "scripts/build_stage5_batch01_language_authority_evidence.py"
EXPECTED_COUNTRIES = {"AE", "BE", "BY", "EE", "GR", "HR", "KZ", "MD", "NG", "NL"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generated_evidence_matches_builder():
    spec = importlib.util.spec_from_file_location("language_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert load(EVIDENCE) == module.build()


def test_batch01_candidate_language_evidence_has_exact_coverage():
    data = load(EVIDENCE)
    assert set(data["batch"]["countries"]) == EXPECTED_COUNTRIES
    assert data["batch"]["country_count"] == 10
    assert data["batch"]["scope_count"] == 30
    assert {entry["country"] for entry in data["entries"]} == EXPECTED_COUNTRIES
    assert len(data["entries"]) == 10


def test_candidate_interpretations_are_treaty_specific():
    rows = {entry["country"]: entry for entry in load(EVIDENCE)["entries"]}
    expected = {
        "AE": (["Czech", "Arabic", "English"], "english_prevails_all_text_divergences"),
        "BE": (["English"], "sole_english"),
        "BY": (["Czech", "Belarusian", "English"], "english_prevails_all_text_divergences"),
        "EE": (["English"], "sole_english"),
        "GR": (["English"], "sole_english"),
        "HR": (["Czech", "Croatian", "English"], "english_prevails_czech_croatian_divergence"),
        "KZ": (["Czech", "Kazakh", "English", "Russian"], "english_prevails_all_text_divergences"),
        "MD": (["Czech", "Moldovan", "English"], "english_prevails_all_text_divergences"),
        "NG": (["English"], "sole_english"),
        "NL": (["Czech", "Dutch", "English"], "english_prevails_czech_dutch_divergence"),
    }
    for country, (languages, rule) in expected.items():
        candidate = rows[country]["candidate_interpretation"]
        assert candidate["authentic_languages"] == languages
        assert candidate["official_english_version"] is True
        assert candidate["prevailing_language_rule"] == rule


def test_signature_extraction_does_not_match_incidental_lowercase_dano():
    rows = {entry["country"]: entry for entry in load(EVIDENCE)["entries"]}
    ng_excerpt = rows["NG"]["signature_clause_candidate"]["exact_excerpt"]
    assert ng_excerpt.startswith("Dáno v Lagosu")
    assert "v anglickém jazyce" in ng_excerpt


def test_exact_excerpts_and_all_source_datasets_are_hash_bound():
    data = load(EVIDENCE)
    for relative, expected_hash in data["source_hashes"].items():
        assert sha256(ROOT / relative) == expected_hash
    for entry in data["entries"]:
        clause = entry["signature_clause_candidate"]
        assert hashlib.sha256(clause["exact_excerpt"].encode("utf-8")).hexdigest() == clause["excerpt_sha256"]
        assert clause["exact_excerpt"]


def test_repository_parsed_candidates_match_their_own_treaty_source():
    data = load(EVIDENCE)
    parsed_rows = [
        entry
        for entry in data["entries"]
        if entry["evidence_source"]["mode"] == "repository_parsed_signature_clause"
    ]
    assert len(parsed_rows) == 8
    for entry in parsed_rows:
        source = entry["evidence_source"]
        assert sha256(ROOT / source["parsed_path"]) == source["parsed_sha256"]
        assert source["parsed_hash_valid"] is True
        assert source["source_hash_relation"] == "parsed_candidate_matches_repository_hash"
        assert source["location"]["json_path"].startswith("$.articles[")


def test_gr_and_nl_current_official_hashes_are_bound_and_historic_hashes_preserved():
    data = load(EVIDENCE)
    conflicts = {
        entry["country"]: entry
        for entry in data["entries"]
        if entry["country"] in {"GR", "NL"}
    }
    assert set(conflicts) == {"GR", "NL"}
    for entry in conflicts.values():
        source = entry["evidence_source"]
        assert source["observed_download_sha256"] != source["archived_manifest_sha256"]
        assert source["source_hash_relation"] == "current_official_candidate_hash_bound_historic_manifest_hash_preserved"
        assert source["historic_hash_difference_documented"] is True
        assert source["source_hash_conflict"] is False
        assert "source_hash_conflict_requires_human_resolution" not in entry["review_blockers"]
        assert entry["production_releasable"] is False


def test_no_candidate_is_misrepresented_as_verified_or_releasable():
    data = load(EVIDENCE)
    assert data["summary"]["human_verified_country_count"] == 0
    assert data["summary"]["production_releasable_country_count"] == 0
    assert data["summary"]["source_hash_conflict_country_count"] == 0
    assert data["summary"]["historic_hash_difference_documented_country_count"] == 2
    for entry in data["entries"]:
        assert entry["evidence_status"] == "candidate_only_needs_human_review"
        assert entry["verification_status"] == "needs_review"
        assert entry["stage5_terminal_status"] == "pending"
        assert entry["production_releasable"] is False
        assert entry["fail_closed"] is True
        assert not any(entry["release_gates"].values())
