from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
INTAKE = BASE / "stage5_remaining80_batch_01_intake.json"
DOSSIER = BASE / "stage5_remaining80_batch_01_legal_chain_dossier.json"
OBSERVATIONS = BASE / "stage5_remaining80_batch_01_language_authority_observations.json"
MANIFEST = ROOT / "data/manifests/source_manifest.json"
OUTPUT = BASE / "stage5_remaining80_batch_01_language_authority_evidence.json"

EXPECTED_COUNTRIES = {"AE", "BE", "BY", "EE", "GR", "HR", "KZ", "MD", "NG", "NL"}
PARSED_MODE = "repository_parsed_signature_clause"
OCR_MODE = "current_official_pdf_ocr_observation"


def load(path: Path) -> Any:
    if not path.is_file():
        raise RuntimeError(f"Required file missing: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def extract_signature_clause(parsed: dict[str, Any], occurrence: int) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []

    for article_index, article in enumerate(parsed.get("articles") or []):
        text = article.get("text")
        if not isinstance(text, str):
            continue

        for match in re.finditer(r"^[ \t]*D[áa]no\b", text, flags=re.MULTILINE):
            tail = text[match.start():]
            end_candidates = [
                marker.start()
                for marker in re.finditer(
                    r"\n(?:Za\s|Na\s+d[uůí]kaz)",
                    tail,
                    flags=re.IGNORECASE,
                )
                if marker.start() > 20
            ]
            excerpt = tail[: min(end_candidates)] if end_candidates else tail
            matches.append(
                {
                    "article_index": article_index,
                    "article_number": article.get("number"),
                    "article_title": article.get("title"),
                    "json_path": f"$.articles[{article_index}].text",
                    "exact_excerpt": excerpt.strip(),
                }
            )

    if occurrence < 1 or occurrence > len(matches):
        raise RuntimeError(
            f"Requested signature occurrence {occurrence}; found {len(matches)}"
        )

    return matches[occurrence - 1]


def build() -> dict[str, Any]:
    intake = load(INTAKE)
    dossier = load(DOSSIER)
    observations = load(OBSERVATIONS)
    manifest = load(MANIFEST)

    intake_by_country = {entry["country"]: entry for entry in intake["entries"]}
    dossier_by_country = {entry["country"]: entry for entry in dossier["entries"]}
    manifest_by_id = {entry["source_id"]: entry for entry in manifest["sources"]}
    observation_by_country = {
        entry["country"]: entry for entry in observations["entries"]
    }

    for label, rows in (
        ("intake", intake_by_country),
        ("dossier", dossier_by_country),
        ("observations", observation_by_country),
    ):
        if set(rows) != EXPECTED_COUNTRIES:
            raise RuntimeError(f"Unexpected {label} country boundary: {sorted(rows)}")

    entries = []

    for country in sorted(EXPECTED_COUNTRIES):
        intake_entry = intake_by_country[country]
        dossier_entry = dossier_by_country[country]
        observation = observation_by_country[country]
        source = dossier_entry["canonical_treaty_source"]
        manifest_source = manifest_by_id[source["source_id"]]
        parsed_path = ROOT / source["parsed_path"]

        if sha256_file(parsed_path) != source["parsed_sha256"]:
            raise RuntimeError(f"Parsed source hash mismatch for {country}")
        if manifest_source["sha256"] != source["artifact_sha256"]:
            raise RuntimeError(f"Manifest artifact hash mismatch for {country}")

        mode = observation["evidence_mode"]
        blockers = ["human_primary_legal_review_required", "independent_approval_required"]

        if mode == PARSED_MODE:
            location = extract_signature_clause(
                load(parsed_path), observation["signature_clause_occurrence"]
            )
            excerpt = location.pop("exact_excerpt")
            evidence_source = {
                "mode": mode,
                "parsed_path": source["parsed_path"],
                "parsed_sha256": source["parsed_sha256"],
                "parsed_hash_valid": True,
                "location": location,
                "archived_artifact_uri": source["artifact_uri"],
                "archived_manifest_sha256": source["artifact_sha256"],
                "archived_artifact_bytes_present": (ROOT / source["artifact_uri"]).is_file(),
                "source_hash_relation": "parsed_candidate_matches_repository_hash",
            }
        elif mode == OCR_MODE:
            excerpt = observation["ocr_excerpt"]
            observed_hash = observation["observed_download_sha256"]
            archived_hash = source["artifact_sha256"]
            if observed_hash == archived_hash:
                raise RuntimeError(f"Expected documented source hash conflict for {country}")
            inventory_urls = {
                item["url"]
                for item in intake_entry["official_instrument_inventory"]["base_instruments"]
            }
            if observation["official_download_url"] not in inventory_urls:
                raise RuntimeError(f"Observed official URL not bound to intake for {country}")
            blockers.append("source_hash_conflict_requires_human_resolution")
            evidence_source = {
                "mode": mode,
                "official_download_url": observation["official_download_url"],
                "observed_download_sha256": observed_hash,
                "archived_artifact_uri": source["artifact_uri"],
                "archived_manifest_sha256": archived_hash,
                "source_hash_relation": "current_official_download_differs_from_archived_manifest",
                "source_hash_conflict": True,
                "location": {"pdf_page": observation["pdf_page"]},
                "extraction_method": observation["ocr_engine"],
            }
        else:
            raise RuntimeError(f"Unsupported evidence mode for {country}: {mode}")

        entries.append(
            {
                "country": country,
                "treaty_pair_id": f"CZ-{country}",
                "source_id": source["source_id"],
                "source_title": source["source_title"],
                "authority_class": source["authority_class"],
                "evidence_source": evidence_source,
                "signature_clause_candidate": {
                    "exact_excerpt": excerpt,
                    "excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
                },
                "candidate_interpretation": {
                    "authentic_languages": observation["authentic_languages_candidate"],
                    "official_english_version": observation["official_english_version_candidate"],
                    "prevailing_language_rule": observation["prevailing_language_rule_candidate"],
                },
                "evidence_status": "candidate_only_needs_human_review",
                "release_gates": {
                    "authentic_languages_verified": False,
                    "official_english_version_assessed": False,
                    "prevailing_language_rule_verified": False,
                    "human_primary_review_complete": False,
                    "independent_approval_complete": False,
                },
                "review_blockers": blockers,
                "verification_status": "needs_review",
                "stage5_terminal_status": "pending",
                "production_releasable": False,
                "fail_closed": True,
            }
        )

    return {
        "schema_version": 1,
        "dataset_release": "stage5-remaining80-batch01-language-authority-evidence-2026-08-09.1",
        "purpose": (
            "Candidate language-authority evidence for human legal review; "
            "not a verified production rule or approval record."
        ),
        "safety_boundary": {
            "candidate_evidence_is_not_verification": True,
            "automatic_promotion_forbidden": True,
            "source_conflicts_fail_closed": True,
        },
        "batch": {
            "countries": sorted(EXPECTED_COUNTRIES),
            "country_count": 10,
            "scope_count": 30,
        },
        "source_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (INTAKE, DOSSIER, OBSERVATIONS, MANIFEST)
        },
        "summary": {
            "candidate_evidence_country_count": 10,
            "repository_parsed_candidate_count": sum(
                entry["evidence_source"]["mode"] == PARSED_MODE for entry in entries
            ),
            "current_official_pdf_ocr_candidate_count": sum(
                entry["evidence_source"]["mode"] == OCR_MODE for entry in entries
            ),
            "source_hash_conflict_country_count": sum(
                entry["evidence_source"].get("source_hash_conflict") is True
                for entry in entries
            ),
            "human_verified_country_count": 0,
            "production_releasable_country_count": 0,
        },
        "entries": entries,
    }


def main() -> None:
    OUTPUT.write_text(
        json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
