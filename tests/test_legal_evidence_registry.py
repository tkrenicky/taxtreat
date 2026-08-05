from __future__ import annotations

import json
from pathlib import Path

from taxtreat.tools.build_legal_evidence_registry import (
    OUTPUT,
    build_legal_evidence_registry,
)


def test_legal_evidence_registry_covers_review_queue() -> None:
    payload = build_legal_evidence_registry()

    assert payload["scope"] == {
        "legal_review_packets": 294,
        "unique_evidence_sources": 380,
        "total_evidence_references": 1551,
    }

    assert len(payload["sources"]) == 380

    source_ids = [
        source["source_id"] for source in payload["sources"]
    ]

    assert len(source_ids) == len(set(source_ids))
    assert source_ids == sorted(source_ids)


def test_existing_treaty_artifacts_are_bound() -> None:
    payload = build_legal_evidence_registry()

    verified = [
        source
        for source in payload["sources"]
        if source["artifact_status"] == "verified"
    ]

    assert len(verified) == 98

    for source in verified:
        assert source["artifact_available"] is True
        assert source["artifact_uri"]
        assert len(source["artifact_sha256"]) == 64
        assert source["official_urls"]


def test_unbound_sources_remain_fail_closed() -> None:
    payload = build_legal_evidence_registry()

    unbound = [
        source
        for source in payload["sources"]
        if source["artifact_status"] == "unbound"
    ]

    assert len(unbound) == 282

    for source in unbound:
        assert source["artifact_available"] is False
        assert source["artifact_uri"] is None
        assert source["artifact_sha256"] is None
        assert source["official_urls"]


def test_registry_file_is_deterministic() -> None:
    first = build_legal_evidence_registry()
    first_text = OUTPUT.read_text(encoding="utf-8")

    second = build_legal_evidence_registry()
    second_text = OUTPUT.read_text(encoding="utf-8")

    assert first == second
    assert first_text == second_text

    stored = json.loads(first_text)
    assert stored == first
