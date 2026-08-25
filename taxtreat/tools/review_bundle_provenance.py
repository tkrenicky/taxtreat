from __future__ import annotations

import hashlib
import json
from typing import Any


OPTIONAL_INPUT_NAMES = (
    "royalty_audit",
    "language_evidence",
    "article_reconciliation",
)


def canonical_json_bytes(payload: Any) -> bytes:
    """Return deterministic JSON bytes for review-bundle provenance hashing."""
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def payload_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _country(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""
    return str(payload.get("source_country") or "").strip().upper()


def _partner_set(payload: dict[str, Any] | None) -> set[str] | None:
    if not payload:
        return None
    rows = payload.get("partners")
    if not isinstance(rows, list):
        return None
    return {
        str(row.get("partner_label") or "").strip()
        for row in rows
        if str(row.get("partner_label") or "").strip()
    }


def _queue_partner_set(review_queue: dict[str, Any]) -> set[str]:
    scopes = review_queue.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("Review queue scopes must be a list")
    partners = {
        str(row.get("partner_label") or "").strip()
        for row in scopes
        if str(row.get("partner_label") or "").strip()
    }
    if not partners:
        raise ValueError("Review queue contains no treaty partners")
    return partners


def build_review_bundle_provenance(
    *,
    review_queue: dict[str, Any],
    article_inventory: dict[str, Any],
    royalty_audit: dict[str, Any] | None = None,
    language_evidence: dict[str, Any] | None = None,
    article_reconciliation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind one human-review bundle to the exact machine inputs used to build it.

    The digest is an integrity/version identity only. It is not legal approval.
    """
    source_country = _country(review_queue)
    article_country = _country(article_inventory)
    if not source_country or article_country != source_country:
        raise ValueError(
            f"Review provenance source-country mismatch: {source_country!r} vs {article_country!r}"
        )

    queue_partners = _queue_partner_set(review_queue)
    article_partners = _partner_set(article_inventory)
    if article_partners is not None and article_partners != queue_partners:
        raise ValueError("Review queue/article inventory treaty-partner universe mismatch")

    optional_inputs = {
        "royalty_audit": royalty_audit,
        "language_evidence": language_evidence,
        "article_reconciliation": article_reconciliation,
    }
    for name, payload in optional_inputs.items():
        if payload is None:
            continue
        payload_country = _country(payload)
        if payload_country and payload_country != source_country:
            raise ValueError(f"{name} source-country mismatch: {payload_country!r} vs {source_country!r}")
        partners = _partner_set(payload)
        if partners is not None and partners != queue_partners:
            raise ValueError(f"{name} treaty-partner universe mismatch")

    payloads: dict[str, dict[str, Any]] = {
        "review_queue": review_queue,
        "article_inventory": article_inventory,
    }
    payloads.update({name: payload for name, payload in optional_inputs.items() if payload is not None})
    input_digests = {
        name: payload_sha256(payload)
        for name, payload in sorted(payloads.items())
    }
    bundle_material = {
        "schema_version": 1,
        "source_country": source_country,
        "input_digests": input_digests,
    }
    bundle_digest = payload_sha256(bundle_material)
    return {
        **bundle_material,
        "review_bundle_id": f"sha256:{bundle_digest}",
        "policy": {
            "identity_only_not_legal_approval": True,
            "all_machine_inputs_are_bound": True,
            "cross_run_input_mixing_rejected": True,
        },
    }
