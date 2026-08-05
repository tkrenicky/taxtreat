from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from taxtreat.engine.article_classifier import classify_article
from taxtreat.engine.legal_facts import load_legal_facts
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.engine.legal_sources import (
    load_legal_sources,
    validate_evidence_references,
)
from taxtreat.parser.official_source import official_source_urls
from taxtreat.registry.legal_scope import expected_legal_scopes


ROOT = Path(__file__).resolve().parents[2]
PARSED_DIR = ROOT / "data" / "parsed"
RULE_DIR = ROOT / "data" / "legal_rules"
LEGAL_SOURCE_DIR = ROOT / "data" / "legal_sources"
LEGAL_FACT_DIR = ROOT / "data" / "legal_facts"
GOLDEN_DIR = ROOT / "data" / "golden_cases"
LEGAL_CONSOLIDATION_DIR = ROOT / "data" / "legal_consolidation"
MF_INVENTORY = LEGAL_CONSOLIDATION_DIR / "mf_inventory.json"
BASE_CANDIDATES = (
    LEGAL_CONSOLIDATION_DIR / "remaining_294_base_candidates.json"
)
MLI_EFFECTS = LEGAL_CONSOLIDATION_DIR / "mli_wht_effects.json"
PROTOCOL_EFFECTS = LEGAL_CONSOLIDATION_DIR / "protocol_effect_candidates.json"
DOMESTIC_EU_CANDIDATES = (
    LEGAL_CONSOLIDATION_DIR / "cz_domestic_eu_candidates.json"
)
INSTRUMENT_CHAINS = (
    LEGAL_CONSOLIDATION_DIR / "remaining_294_instrument_chains.json"
)
BLOCKER_RESOLUTIONS = LEGAL_CONSOLIDATION_DIR / "blocker_resolutions.json"
LEGAL_REVIEW_DIR = ROOT / "data" / "legal_reviews"
REVIEW_QUEUE = LEGAL_REVIEW_DIR / "remaining_294_review_queue.json"
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
    existing_sources: dict[str, dict[str, Any]] = {}

    if SOURCE_MANIFEST.is_file():
        existing_payload = _read_json(SOURCE_MANIFEST)
        existing_sources = {
            source["source_id"]: source
            for source in existing_payload.get("sources", [])
            if source.get("source_id")
        }

    sources = []

    for parsed_path in sorted(PARSED_DIR.glob("*.json")):
        parsed = _read_json(parsed_path)
        source_title = parsed.get("source_title") or ""
        source_id = _stable_source_id(
            parsed.get("country", parsed_path.stem),
            source_title,
        )

        raw_path = ROOT / parsed.get("source_path", "")
        raw_available = raw_path.is_file()
        existing_source = existing_sources.get(source_id, {})

        existing_sha256 = existing_source.get("sha256")
        existing_artifact_uri = existing_source.get("artifact_uri")

        committed_binding_available = bool(
            existing_source.get("artifact_available")
            and existing_artifact_uri
            and isinstance(existing_sha256, str)
            and len(existing_sha256) == 64
        )

        artifact_available = bool(
            raw_available or committed_binding_available
        )
        artifact_uri = (
            parsed.get("source_path")
            if raw_available
            else existing_artifact_uri
            if committed_binding_available
            else None
        )
        artifact_sha256 = (
            _sha256(raw_path)
            if raw_available
            else existing_sha256
            if committed_binding_available
            else None
        )

        resolution_method = (
            parsed.get("source_resolution") or {}
        ).get("method")

        sources.append(
            {
                "source_id": source_id,
                "country": parsed.get("country"),
                "source_title": source_title,
                "parsed_path": str(parsed_path.relative_to(ROOT)),
                "artifact_uri": artifact_uri,
                "artifact_available": artifact_available,
                "sha256": artifact_sha256,
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
    inventory = _read_json(MF_INVENTORY)
    inventory_by_code = {
        row["iso2"]: row for row in inventory.get("partners", [])
    }
    if len(inventory_by_code) != 100:
        raise ValueError("Official MF instrument inventory must cover 100 partners.")
    base_candidates_payload = _read_json(BASE_CANDIDATES)
    base_candidates = {
        (row["recipient_country"], row["income_type"]): row
        for row in base_candidates_payload.get("scopes", [])
    }
    if len(base_candidates) != 294:
        raise ValueError("Base-treaty candidate registry must cover 294 scopes.")
    mli_effects_payload = _read_json(MLI_EFFECTS)
    mli_effects = {
        row["recipient_country"]: row
        for row in mli_effects_payload.get("effects", [])
    }
    if len(mli_effects) != 62:
        raise ValueError("Official MLI WHT effect registry must cover 62 partners.")
    blocker_resolutions_payload = _read_json(BLOCKER_RESOLUTIONS)
    mli_resolutions = {
        row["recipient_country"]: row
        for row in blocker_resolutions_payload.get("mli_resolutions", [])
    }
    if len(mli_resolutions) != 9:
        raise ValueError("MLI blocker resolutions must cover 9 partners.")
    protocol_effects_payload = _read_json(PROTOCOL_EFFECTS)
    protocol_effects = {
        (row["recipient_country"], row["income_type"]): row
        for row in protocol_effects_payload.get("scopes", [])
    }
    if len(protocol_effects) != 33:
        raise ValueError("Protocol-effect candidate registry must cover 33 scopes.")
    domestic_eu_payload = _read_json(DOMESTIC_EU_CANDIDATES)
    domestic_eu_candidates = {
        (row["recipient_country"], row["income_type"]): row
        for row in domestic_eu_payload.get("scopes", [])
    }
    if len(domestic_eu_candidates) != 300:
        raise ValueError(
            "Czech domestic/EU candidate registry must cover 300 scopes."
        )
    instrument_chains_payload = _read_json(INSTRUMENT_CHAINS)
    instrument_chains = {
        (row["recipient_country"], row["income_type"]): row
        for row in instrument_chains_payload.get("scopes", [])
    }
    if len(instrument_chains) != 294:
        raise ValueError(
            "Instrument-chain candidate registry must cover 294 scopes."
        )
    review_queue_payload = _read_json(REVIEW_QUEUE)
    review_packets = {
        (row["recipient_country"], row["income_type"]): row
        for row in review_queue_payload.get("packets", [])
    }
    if len(review_packets) != 294:
        raise ValueError("Legal-review queue must cover 294 scopes.")
    if set(review_packets) != set(instrument_chains):
        raise ValueError(
            "Legal-review queue does not match the instrument-chain scopes."
        )
    for key, packet in review_packets.items():
        if packet["candidate_sha256"] != instrument_chains[key][
            "candidate_sha256"
        ]:
            raise ValueError(
                f"Legal-review packet {packet['packet_id']} has a stale candidate hash."
            )
    legal_sources = {}
    for source_path in sorted(LEGAL_SOURCE_DIR.glob("*.json")):
        legal_sources.update(load_legal_sources(source_path))
    for fact_path in sorted(LEGAL_FACT_DIR.glob("*.json")):
        for fact in load_legal_facts(fact_path):
            unknown_sources = validate_evidence_references(
                [fact.source_id, *fact.evidence_source_ids],
                legal_sources,
            )
            if unknown_sources:
                raise ValueError(
                    f"Legal fact {fact.fact_id} references unknown sources: "
                    + ", ".join(unknown_sources)
                )
            if fact.verification_status == "needs_review" and not fact.is_review_ready:
                raise ValueError(
                    f"Legal fact {fact.fact_id} is not review-ready."
                )
    scopes: dict[tuple[str, str, str], dict[str, Any]] = {}
    for expected in expected_legal_scopes():
        key = (
            expected["source_country"],
            expected["recipient_country"],
            expected["income_type"],
        )
        parsed_path = PARSED_DIR / expected["parsed_file"]
        if not parsed_path.is_file():
            raise ValueError(
                "Treaty-partner registry references a missing parsed dataset: "
                f"{expected['parsed_file']}"
            )
        parsed = _read_json(parsed_path)
        if parsed.get("country") != expected["recipient_country_name"]:
            raise ValueError(
                "Treaty-partner name does not match its parsed dataset: "
                f"{expected['recipient_country']}"
            )
        scopes[key] = {
            "source_country": expected["source_country"],
            "recipient_country": expected["recipient_country"],
            "recipient_country_name": expected["recipient_country_name"],
            "income_type": expected["income_type"],
            "parsed_path": str(parsed_path.relative_to(ROOT)),
            "base_treaty_source_id": _stable_source_id(
                parsed.get("country", parsed_path.stem),
                parsed.get("source_title") or "",
            ),
            "rule_ids": [],
            "verification_status": "verified",
            "review_ready": True,
            "legal_layers": [],
            "missing_legal_layers": [],
            "dataset_releases": [],
            "scope_status": "pending_consolidation",
            "instrument_inventory_status": inventory_by_code[
                expected["recipient_country"]
            ]["inventory_status"],
            "base_candidate_status": (
                "pilot_consolidated"
                if expected["recipient_country"] in {"AT", "CH"}
                else base_candidates[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["candidate_status"]
            ),
            "base_candidate_rates": (
                []
                if expected["recipient_country"] in {"AT", "CH"}
                else sorted(
                    {
                        candidate["rate"]
                        for candidate in base_candidates[
                            (
                                expected["recipient_country"],
                                expected["income_type"],
                            )
                        ]["rate_candidates"]
                    }
                )
            ),
            "base_candidate_rate_cap_status": (
                "pilot_consolidated"
                if expected["recipient_country"] in {"AT", "CH"}
                else base_candidates[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ].get("treaty_rate_cap_status", "unresolved")
            ),
            "preconsolidation_risk_flags": (
                []
                if expected["recipient_country"] in {"AT", "CH"}
                else base_candidates[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["risk_flags"]
            ),
            "mli_wht_effect_candidate_from": (
                (
                    mli_effects.get(expected["recipient_country"])
                    or mli_resolutions.get(expected["recipient_country"])
                    or {}
                ).get("effective_from")
            ),
            "mli_resolution_status": mli_resolutions.get(
                expected["recipient_country"], {}
            ).get("resolution_status"),
            "protocol_candidate_status": (
                "pilot_consolidated"
                if expected["recipient_country"] in {"AT", "CH"}
                else protocol_effects.get(
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    ),
                    {},
                ).get("candidate_status", "not_listed")
            ),
            "protocol_effect_kind": protocol_effects.get(
                (
                    expected["recipient_country"],
                    expected["income_type"],
                ),
                {},
            ).get("effect_kind"),
            "protocol_candidate_rates": sorted(
                {
                    row["rate"]
                    for row in protocol_effects.get(
                        (
                            expected["recipient_country"],
                            expected["income_type"],
                        ),
                        {},
                    ).get("protocol_rate_candidates", [])
                }
            ),
            "protocol_candidate_effective_from": protocol_effects.get(
                (
                    expected["recipient_country"],
                    expected["income_type"],
                ),
                {},
            ).get("protocol_candidate_effective_from"),
            "post_protocol_status_source_id": protocol_effects.get(
                (
                    expected["recipient_country"],
                    expected["income_type"],
                ),
                {},
            ).get("later_status_source_id"),
            "domestic_candidate_status": domestic_eu_candidates[
                (
                    expected["recipient_country"],
                    expected["income_type"],
                )
            ]["candidate_status"],
            "domestic_candidate_effective_from": domestic_eu_candidates[
                (
                    expected["recipient_country"],
                    expected["income_type"],
                )
            ]["domestic_rate_candidate"]["effective_from"],
            "domestic_candidate_rates": sorted(
                {
                    domestic_eu_candidates[
                        (
                            expected["recipient_country"],
                            expected["income_type"],
                        )
                    ]["domestic_rate_candidate"]["standard_rate"],
                    domestic_eu_candidates[
                        (
                            expected["recipient_country"],
                            expected["income_type"],
                        )
                    ]["domestic_rate_candidate"]["protective_rate"],
                }
            ),
            "eu_relief_candidate_status": domestic_eu_candidates[
                (
                    expected["recipient_country"],
                    expected["income_type"],
                )
            ]["relief_candidate_status"],
            "eu_relief_candidate_rate": (
                domestic_eu_candidates[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["relief_candidate"] or {}
            ).get("rate"),
            "eu_relief_candidate_regime": (
                domestic_eu_candidates[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["relief_candidate"] or {}
            ).get("regime"),
            "candidate_chain_status": (
                "pilot_consolidated"
                if expected["recipient_country"] in {"AT", "CH"}
                else instrument_chains[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["chain_status"]
            ),
            "candidate_chain_complete": (
                True
                if expected["recipient_country"] in {"AT", "CH"}
                else instrument_chains[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["candidate_chain_complete"]
            ),
            "candidate_chain_blockers": (
                []
                if expected["recipient_country"] in {"AT", "CH"}
                else instrument_chains[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["hard_blockers"]
            ),
            "candidate_chain_review_tasks": (
                ["independent_legal_review"]
                if expected["recipient_country"] in {"AT", "CH"}
                else instrument_chains[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["legal_review_tasks"]
            ),
            "treaty_status_candidate_status": (
                "not_listed"
                if expected["recipient_country"] in {"AT", "CH"}
                else instrument_chains[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["treaty_status_instrument"]["candidate_status"]
            ),
            "treaty_status_candidate_source_id": (
                None
                if expected["recipient_country"] in {"AT", "CH"}
                else instrument_chains[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["treaty_status_instrument"]["source_id"]
            ),
            "candidate_review_packet_id": (
                None
                if expected["recipient_country"] in {"AT", "CH"}
                else review_packets[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["packet_id"]
            ),
            "candidate_review_packet_status": (
                "pilot_rule_review_ready"
                if expected["recipient_country"] in {"AT", "CH"}
                else review_packets[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["packet_status"]
            ),
            "candidate_review_approval_eligible": (
                False
                if expected["recipient_country"] in {"AT", "CH"}
                else review_packets[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["approval_eligible"]
            ),
            "candidate_review_promotable": (
                False
                if expected["recipient_country"] in {"AT", "CH"}
                else review_packets[
                    (
                        expected["recipient_country"],
                        expected["income_type"],
                    )
                ]["promotable_to_active_rules"]
            ),
        }

    for path in sorted(RULE_DIR.glob("*.json")):
        for rule in load_legal_rules(path):
            unknown_sources = validate_evidence_references(
                [rule.source_id, *rule.evidence_source_ids],
                legal_sources,
            )
            if unknown_sources:
                raise ValueError(
                    f"Rule {rule.rule_id} references unknown legal sources: "
                    + ", ".join(unknown_sources)
                )
            key = (rule.source_country, rule.recipient_country, rule.income_type)
            if key not in scopes:
                raise ValueError(
                    "Legal rule references a country-income scope outside "
                    f"the canonical Czech treaty registry: {key!r}"
                )
            scope = scopes[key]
            scope["rule_ids"].append(rule.rule_id)
            scope["legal_layers"].append(rule.legal_layer)
            if rule.dataset_release:
                scope["dataset_releases"].append(rule.dataset_release)
            if rule.verification_status != "verified":
                scope["verification_status"] = "needs_review"
            if rule.verification_status not in {"verified", "needs_review"}:
                scope["review_ready"] = False

    for scope in scopes.values():
        scope["legal_layers"] = sorted(set(scope["legal_layers"]))
        scope["dataset_releases"] = sorted(set(scope["dataset_releases"]))
        required_layers = {"domestic", "mli", "eu_relief"}
        missing_layers = sorted(
            required_layers.difference(scope["legal_layers"])
        )
        if not {"treaty", "protocol"}.intersection(scope["legal_layers"]):
            missing_layers.append("treaty_or_protocol")
        scope["missing_legal_layers"] = missing_layers
        if missing_layers:
            scope["review_ready"] = False
        if len(scope["dataset_releases"]) != 1:
            scope["review_ready"] = False
        if not scope["rule_ids"]:
            scope["verification_status"] = "needs_review"
            scope["review_ready"] = False
        scope["scope_status"] = (
            "verified"
            if scope["verification_status"] == "verified"
            and scope["review_ready"]
            else "review_ready"
            if scope["review_ready"]
            else "pending_consolidation"
        )

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
    source_manifest = build_source_manifest()
    legal_registry = build_legal_registry()
    parsed_files = sorted(PARSED_DIR.glob("*.json"))
    parsed_payloads = [_read_json(path) for path in parsed_files]
    relevant_articles = sum(
        _structural_article_count(payload) for payload in parsed_payloads
    )
    sources = source_manifest["sources"]
    scopes = legal_registry["scopes"]
    verified_scopes = [
        scope for scope in scopes if scope["scope_status"] == "verified"
    ]
    review_ready_scopes = [scope for scope in scopes if scope["review_ready"]]
    pending_scopes = [
        scope
        for scope in scopes
        if scope["scope_status"] == "pending_consolidation"
    ]
    inventory = _read_json(MF_INVENTORY)
    base_candidates = _read_json(BASE_CANDIDATES)["scopes"]
    mli_effects = _read_json(MLI_EFFECTS)["effects"]
    blocker_resolutions = _read_json(BLOCKER_RESOLUTIONS)
    protocol_effects = _read_json(PROTOCOL_EFFECTS)
    domestic_eu_candidates = _read_json(DOMESTIC_EU_CANDIDATES)
    instrument_chains = _read_json(INSTRUMENT_CHAINS)
    review_queue = _read_json(REVIEW_QUEUE)
    base_candidate_scopes_with_rates = sum(
        bool(scope["rate_candidates"]) for scope in base_candidates
    )
    base_candidate_no_cap_scopes = sum(
        scope.get("treaty_rate_cap_status") == "no_numeric_cap"
        for scope in base_candidates
    )
    supplemental_mli_effects = [
        row
        for row in blocker_resolutions["mli_resolutions"]
        if row["resolution_status"] == "wht_effect_candidate_available"
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
            "review_ready_scopes": len(review_ready_scopes),
            "pending_consolidation_scopes": len(pending_scopes),
            "instrument_inventory_partners": len(inventory["partners"]),
            "base_candidate_scopes": len(base_candidates),
            "base_candidate_scopes_with_rates": base_candidate_scopes_with_rates,
            "base_candidate_scopes_without_rates": (
                len(base_candidates) - base_candidate_scopes_with_rates
            ),
            "base_candidate_no_numeric_cap_scopes": (
                base_candidate_no_cap_scopes
            ),
            "base_candidate_unresolved_scopes": (
                len(base_candidates)
                - base_candidate_scopes_with_rates
                - base_candidate_no_cap_scopes
            ),
            "mli_wht_effect_candidate_partners": (
                len(mli_effects) + len(supplemental_mli_effects)
            ),
            "remaining_mli_wht_effect_candidate_partners": sum(
                effect["recipient_country"] not in {"AT", "CH"}
                for effect in mli_effects
            ) + len(supplemental_mli_effects),
            "mli_no_current_effect_determinations": (
                blocker_resolutions["summary"][
                    "mli_no_current_effect_determinations"
                ]
            ),
            "status_instrument_candidate_partners": (
                blocker_resolutions["summary"]["status_instruments"]
            ),
            "resolved_instrument_chain_blocker_scopes": (
                blocker_resolutions["summary"]["resolved_scopes"]
            ),
            "protocol_effect_candidate_documents": len(
                protocol_effects["documents"]
            ),
            "protocol_effect_candidate_partners": len(
                {
                    scope["recipient_country"]
                    for scope in protocol_effects["scopes"]
                }
            ),
            "protocol_effect_candidate_scopes": len(
                protocol_effects["scopes"]
            ),
            "domestic_candidate_scopes": len(
                domestic_eu_candidates["scopes"]
            ),
            "remaining_domestic_candidate_scopes": sum(
                scope["recipient_country"] not in {"AT", "CH"}
                for scope in domestic_eu_candidates["scopes"]
            ),
            "eu_relief_candidate_partners": len(
                {
                    scope["recipient_country"]
                    for scope in domestic_eu_candidates["scopes"]
                    if scope["relief_candidate"] is not None
                }
            ),
            "eu_relief_candidate_scopes": sum(
                scope["relief_candidate"] is not None
                for scope in domestic_eu_candidates["scopes"]
            ),
            "remaining_eu_relief_candidate_scopes": sum(
                scope["relief_candidate"] is not None
                and scope["recipient_country"] not in {"AT", "CH"}
                for scope in domestic_eu_candidates["scopes"]
            ),
            "instrument_chain_candidate_scopes": instrument_chains[
                "summary"
            ]["total_scopes"],
            "instrument_chain_assembled_scopes": instrument_chains[
                "summary"
            ]["candidate_chain_assembled_scopes"],
            "instrument_chain_blocked_scopes": instrument_chains[
                "summary"
            ]["candidate_chain_blocked_scopes"],
            "instrument_chain_blocked_partners": instrument_chains[
                "summary"
            ]["blocked_partners"],
            "candidate_review_packets": review_queue["summary"][
                "total_packets"
            ],
            "candidate_review_awaiting_primary": review_queue["summary"][
                "awaiting_primary_review"
            ],
            "candidate_review_awaiting_independent_approval": review_queue[
                "summary"
            ]["awaiting_independent_approval"],
            "candidate_review_independently_approved": review_queue[
                "summary"
            ]["independently_approved"],
            "candidate_review_approval_eligible": review_queue["summary"][
                "approval_eligible_packets"
            ],
            "candidate_review_promotable": review_queue["summary"][
                "promotable_packets"
            ],
            "production_coverage_percent": (
                round(len(verified_scopes) / len(scopes) * 100, 2)
                if scopes
                else 0.0
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
    if manifest["legal"]["scopes"] != manifest["parser"]["datasets"] * 3:
        errors.append(
            "Every parsed treaty partner must have three registered legal scopes."
        )
    if production and not manifest["production_ready"]:
        errors.append(
            "Production gate failed: source artifacts/hashes and at least one "
            "fully verified legal scope are required."
        )
    if errors:
        raise RuntimeError("\n".join(errors))
    return manifest
