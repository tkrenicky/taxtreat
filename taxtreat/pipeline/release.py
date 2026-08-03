from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from taxtreat.engine.article_classifier import classify_article
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.parser.official_source import official_source_urls


ROOT = Path(__file__).resolve().parents[2]
PARSED_DIR = ROOT / "data" / "parsed"
RULE_DIR = ROOT / "data" / "legal_rules"
GOLDEN_DIR = ROOT / "data" / "golden_cases"
MANIFEST_DIR = ROOT / "data" / "manifests"
REGISTRY_DIR = ROOT / "data" / "registries"
SOURCE_MANIFEST = MANIFEST_DIR / "source_manifest.json"
LEGAL_REGISTRY = REGISTRY_DIR / "legal_scope.json"
RELEASE_MANIFEST = MANIFEST_DIR / "release_manifest.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_source_id(country: str, source_title: str) -> str:
    token = f"CZ|{country}|{source_title}".encode("utf-8")
    return "SRC-" + hashlib.sha256(token).hexdigest()[:16].upper()


def build_source_manifest() -> dict[str, Any]:
    sources = []
    for parsed_path in sorted(PARSED_DIR.glob("*.json")):
        parsed = _read_json(parsed_path)
        raw_path = ROOT / parsed.get("source_path", "")
        artifact_available = raw_path.is_file()
        source_title = parsed.get("source_title") or ""
        resolution_method = (parsed.get("source_resolution") or {}).get("method")
        sources.append(
            {
                "source_id": _stable_source_id(
                    parsed.get("country", parsed_path.stem),
                    source_title,
                ),
                "country": parsed.get("country"),
                "source_title": source_title,
                "parsed_path": str(parsed_path.relative_to(ROOT)),
                "artifact_uri": parsed.get("source_path"),
                "artifact_available": artifact_available,
                "sha256": _sha256(raw_path) if artifact_available else None,
                "official_urls": list(official_source_urls(source_title)),
                "authority_class": "official",
                "extraction_authority_class": (
                    "mirror"
                    if resolution_method == "verified_mirror_html"
                    else "official"
                ),
                "identity_status": (
                    parsed.get("identity_validation") or {}
                ).get("status"),
                "identity_warnings": (
                    parsed.get("identity_validation") or {}
                ).get("warnings", []),
            }
        )

    payload = {"schema_version": 1, "sources": sources}
    _write_json(SOURCE_MANIFEST, payload)
    return payload


def build_legal_registry() -> dict[str, Any]:
    scopes: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in sorted(RULE_DIR.glob("*.json")):
        for rule in load_legal_rules(path):
            key = (rule.source_country, rule.recipient_country, rule.income_type)
            scope = scopes.setdefault(
                key,
                {
                    "source_country": rule.source_country,
                    "recipient_country": rule.recipient_country,
                    "income_type": rule.income_type,
                    "rule_ids": [],
                    "verification_status": "verified",
                },
            )
            scope["rule_ids"].append(rule.rule_id)
            if rule.verification_status != "verified":
                scope["verification_status"] = "needs_review"

    payload = {
        "schema_version": 1,
        "canonical_source": "data/legal_rules/*.json",
        "scopes": sorted(
            scopes.values(),
            key=lambda item: (
                item["source_country"],
                item["recipient_country"],
                item["income_type"],
            ),
        ),
    }
    _write_json(LEGAL_REGISTRY, payload)
    return payload


def _structural_article_count(parsed: dict[str, Any]) -> int:
    found = set()
    for article in parsed.get("articles", []):
        article_type = classify_article(
            article.get("title") or "",
            article.get("text") or "",
        )
        if article_type in {"dividend", "interest", "royalty"}:
            found.add(article_type)
    return len(found)


def build_release_manifest() -> dict[str, Any]:
    source_manifest = (
        _read_json(SOURCE_MANIFEST)
        if SOURCE_MANIFEST.exists()
        else build_source_manifest()
    )
    legal_registry = (
        _read_json(LEGAL_REGISTRY)
        if LEGAL_REGISTRY.exists()
        else build_legal_registry()
    )
    parsed_files = sorted(PARSED_DIR.glob("*.json"))
    parsed_payloads = [_read_json(path) for path in parsed_files]
    relevant_articles = sum(
        _structural_article_count(payload) for payload in parsed_payloads
    )
    sources = source_manifest["sources"]
    scopes = legal_registry["scopes"]
    verified_scopes = [
        scope for scope in scopes if scope["verification_status"] == "verified"
    ]
    source_artifacts_available = sum(
        source["artifact_available"] and bool(source["sha256"])
        for source in sources
    )
    production_ready = bool(
        sources
        and source_artifacts_available == len(sources)
        and verified_scopes
    )
    payload = {
        "schema_version": 1,
        "dataset_version": os.getenv("TAXTREAT_DATASET_VERSION", "unreleased"),
        "git_commit": os.getenv("GITHUB_SHA", "working-tree"),
        "parser": {
            "datasets": len(parsed_files),
            "relevant_articles": relevant_articles,
            "structurally_complete": relevant_articles == len(parsed_files) * 3,
        },
        "sources": {
            "total": len(sources),
            "artifacts_with_hash": source_artifacts_available,
            "auditability": (
                "complete"
                if source_artifacts_available == len(sources)
                else "blocked"
            ),
        },
        "legal": {
            "scopes": len(scopes),
            "verified_scopes": len(verified_scopes),
            "production_coverage_percent": (
                round(len(verified_scopes) / 300 * 100, 2)
            ),
        },
        "golden_cases": len(list(GOLDEN_DIR.glob("*.json"))),
        "production_ready": production_ready,
    }
    canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    _write_json(RELEASE_MANIFEST, payload)
    return payload


def validate_release(*, production: bool = False) -> dict[str, Any]:
    manifest = build_release_manifest()
    errors = []
    if not manifest["parser"]["structurally_complete"]:
        errors.append("Parser datasets do not contain all three income articles.")
    if manifest["parser"]["datasets"] != manifest["sources"]["total"]:
        errors.append("Every parsed dataset must have one source-manifest entry.")
    if production and not manifest["production_ready"]:
        errors.append(
            "Production gate failed: source artifacts/hashes and at least one "
            "fully verified legal scope are required."
        )
    if errors:
        raise RuntimeError("\n".join(errors))
    return manifest
