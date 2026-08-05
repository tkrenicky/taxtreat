from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

REVIEW_QUEUE = DATA_DIR / "legal_reviews" / "remaining_294_review_queue.json"
SOURCE_MANIFEST = DATA_DIR / "manifests" / "source_manifest.json"
ARTIFACT_MANIFEST = (
    DATA_DIR / "manifests" / "legal_evidence_artifacts.json"
)
OUTPUT = DATA_DIR / "registries" / "legal_evidence_sources.json"

URL_KEYS = {
    "url",
    "source_url",
    "official_url",
    "official_source_url",
}

URL_LIST_KEYS = {
    "urls",
    "official_urls",
    "official_source_urls",
}

METADATA_KEYS = {
    "authority",
    "authority_class",
    "label",
    "title",
    "source_title",
    "source_type",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _required_source_usage() -> Counter[str]:
    queue = _read_json(REVIEW_QUEUE)

    usage: Counter[str] = Counter()

    for packet in queue.get("packets", []):
        usage.update(packet.get("evidence_source_ids", []))

    if len(queue.get("packets", [])) != 294:
        raise ValueError("Legal-review queue must contain 294 packets.")

    return usage


def _direct_urls(record: dict[str, Any]) -> set[str]:
    urls: set[str] = set()

    for key in URL_KEYS:
        value = record.get(key)

        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.add(value)

    for key in URL_LIST_KEYS:
        value = record.get(key)

        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.startswith(
                    ("http://", "https://")
                ):
                    urls.add(item)

    return urls


def _scan_json_records(
    value: Any,
    *,
    required_ids: set[str],
    source_records: dict[str, dict[str, Any]],
    origin: str,
) -> None:
    if isinstance(value, dict):
        direct_ids = {
            item
            for item in value.values()
            if isinstance(item, str) and item in required_ids
        }

        for source_id in direct_ids:
            record = source_records[source_id]

            record["registry_origins"].add(origin)
            record["official_urls"].update(_direct_urls(value))

            for key in METADATA_KEYS:
                metadata_value = value.get(key)

                if (
                    metadata_value is not None
                    and key not in record["metadata"]
                ):
                    record["metadata"][key] = metadata_value

        for nested in value.values():
            _scan_json_records(
                nested,
                required_ids=required_ids,
                source_records=source_records,
                origin=origin,
            )

    elif isinstance(value, list):
        for nested in value:
            _scan_json_records(
                nested,
                required_ids=required_ids,
                source_records=source_records,
                origin=origin,
            )


def _load_treaty_manifest() -> dict[str, dict[str, Any]]:
    manifest = _read_json(SOURCE_MANIFEST)

    return {
        source["source_id"]: source
        for source in manifest.get("sources", [])
    }


def _load_existing_verified_artifacts() -> dict[str, dict[str, Any]]:
    """Load stable artifact bindings committed to the repository.

    The source manifest is rebuilt by the release pipeline and reflects
    whether ignored raw files exist in the current checkout. The artifact
    manifest preserves the previously verified bindings needed for
    deterministic clean-install and CI results.
    """
    manifest = _read_json(ARTIFACT_MANIFEST)

    return {
        artifact["source_id"]: artifact
        for artifact in manifest.get("artifacts", [])
        if artifact.get("status") == "existing_verified_artifact"
    }


def build_legal_evidence_registry() -> dict[str, Any]:
    usage = _required_source_usage()
    required_ids = set(usage)

    source_records: dict[str, dict[str, Any]] = {
        source_id: {
            "official_urls": set(),
            "registry_origins": set(),
            "metadata": {},
        }
        for source_id in required_ids
    }

    excluded_paths = {
        REVIEW_QUEUE,
        OUTPUT,
        DATA_DIR / "manifests" / "legal_evidence_artifacts.json",
        DATA_DIR
        / "legal_reviews"
        / "remaining_294_evidence_readiness.json",
    }

    for path in sorted(DATA_DIR.rglob("*.json")):
        if path in excluded_paths:
            continue

        try:
            payload = _read_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        _scan_json_records(
            payload,
            required_ids=required_ids,
            source_records=source_records,
            origin=str(path.relative_to(ROOT)),
        )

    treaty_manifest = _load_treaty_manifest()
    verified_artifacts = _load_existing_verified_artifacts()
    sources = []

    for source_id in sorted(required_ids):
        collected = source_records[source_id]
        treaty_source = treaty_manifest.get(source_id)

        artifact_uri = None
        artifact_sha256 = None
        artifact_available = False
        artifact_status = "unbound"

        if treaty_source:
            collected["official_urls"].update(
                treaty_source.get("official_urls", [])
            )
            collected["registry_origins"].add(
                str(SOURCE_MANIFEST.relative_to(ROOT))
            )

        verified_artifact = verified_artifacts.get(source_id)

        if verified_artifact:
            collected["official_urls"].update(
                verified_artifact.get("official_urls", [])
            )
            collected["registry_origins"].add(
                str(ARTIFACT_MANIFEST.relative_to(ROOT))
            )

            artifact_uri = verified_artifact.get("artifact_uri")
            artifact_sha256 = verified_artifact.get("sha256")
            artifact_available = bool(
                artifact_uri
                and artifact_sha256
            )

        elif treaty_source:
            artifact_uri = treaty_source.get("artifact_uri")
            artifact_sha256 = treaty_source.get("sha256")
            artifact_available = bool(
                treaty_source.get("artifact_available")
                and artifact_uri
                and artifact_sha256
            )

        if artifact_available:
            artifact_status = "verified"

        official_urls = sorted(collected["official_urls"])

        if not official_urls:
            artifact_status = "missing_official_url"

        sources.append(
            {
                "source_id": source_id,
                "usage_count": usage[source_id],
                "official_urls": official_urls,
                "metadata": collected["metadata"],
                "registry_origins": sorted(
                    collected["registry_origins"]
                ),
                "artifact_uri": artifact_uri,
                "artifact_sha256": artifact_sha256,
                "artifact_available": artifact_available,
                "artifact_status": artifact_status,
            }
        )

    status_counts = Counter(
        source["artifact_status"] for source in sources
    )

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-evidence-source-registry-2026-08-05.1"
        ),
        "scope": {
            "legal_review_packets": 294,
            "unique_evidence_sources": len(sources),
            "total_evidence_references": sum(usage.values()),
        },
        "summary": {
            "verified_sources": status_counts["verified"],
            "unbound_sources": status_counts["unbound"],
            "sources_missing_official_url": status_counts[
                "missing_official_url"
            ],
        },
        "sources": sources,
    }

    if len(sources) != 380:
        raise ValueError(
            f"Expected 380 unique evidence sources, found {len(sources)}."
        )

    _write_json(OUTPUT, payload)
    return payload


def main() -> None:
    payload = build_legal_evidence_registry()

    print("Legal evidence registry created.")
    print(
        "Unique evidence sources:",
        payload["scope"]["unique_evidence_sources"],
    )
    print(
        "Total evidence references:",
        payload["scope"]["total_evidence_references"],
    )
    print(
        "Already verified:",
        payload["summary"]["verified_sources"],
    )
    print(
        "Awaiting artifact binding:",
        payload["summary"]["unbound_sources"],
    )
    print(
        "Missing official URL:",
        payload["summary"]["sources_missing_official_url"],
    )
    print("Registry:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
