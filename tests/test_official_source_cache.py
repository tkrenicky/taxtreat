from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from taxtreat.tools.official_source_cache import load_cached_source, store_cached_source


def test_official_source_cache_roundtrip_and_hash_validation(tmp_path: Path):
    now = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
    url = "https://ris.bka.gv.at/example"
    content = b"official treaty text"
    meta = store_cached_source(
        url,
        final_url="https://ris.bka.gv.at/final",
        content_type="text/html",
        content=content,
        cache_root=tmp_path,
        namespace="AT-2026-08-25",
        fetched_at=now,
    )
    assert meta["cache_is_transport_optimization_not_legal_evidence"] is True
    cached = load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="AT-2026-08-25",
        max_age_seconds=3600,
        now=now + timedelta(minutes=30),
    )
    assert cached is not None
    assert cached.content == content
    assert cached.sha256 == meta["sha256"]

    body = next((tmp_path / "AT-2026-08-25").glob("*.bin"))
    body.write_bytes(b"tampered")
    assert load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="AT-2026-08-25",
        max_age_seconds=3600,
        now=now + timedelta(minutes=30),
    ) is None


def test_official_source_cache_expires_is_namespaced_and_rejects_future_timestamp(tmp_path: Path):
    now = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
    url = "https://bmf.gv.at/treaty"
    store_cached_source(
        url,
        final_url=url,
        content_type="application/pdf",
        content=b"pdf-bytes",
        cache_root=tmp_path,
        namespace="snapshot-a",
        fetched_at=now,
    )
    assert load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="snapshot-b",
        max_age_seconds=86400,
        now=now,
    ) is None
    assert load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="snapshot-a",
        max_age_seconds=60,
        now=now + timedelta(minutes=2),
    ) is None
    assert load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="snapshot-a",
        max_age_seconds=86400,
        now=now - timedelta(seconds=1),
    ) is None


def test_official_source_cache_accepts_naive_iso_timestamp_as_utc(tmp_path: Path):
    now = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
    url = "https://ris.bka.gv.at/naive"
    store_cached_source(
        url,
        final_url=url,
        content_type="text/html",
        content=b"body",
        cache_root=tmp_path,
        namespace="naive",
        fetched_at=now,
    )
    meta = next((tmp_path / "naive").glob("*.json"))
    payload = json.loads(meta.read_text(encoding="utf-8"))
    payload["fetched_at"] = "2026-08-25T08:00:00"
    meta.write_text(json.dumps(payload), encoding="utf-8")
    assert load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="naive",
        max_age_seconds=60,
        now=now,
    ) is not None


def test_official_source_cache_returns_none_for_missing_or_malformed_metadata(tmp_path: Path):
    url = "https://ris.bka.gv.at/missing"
    assert load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="missing",
        max_age_seconds=60,
    ) is None

    store_cached_source(
        url,
        final_url=url,
        content_type="text/html",
        content=b"body",
        cache_root=tmp_path,
        namespace="broken",
    )
    meta = next((tmp_path / "broken").glob("*.json"))
    meta.write_text("{bad-json", encoding="utf-8")
    assert load_cached_source(
        url,
        cache_root=tmp_path,
        namespace="broken",
        max_age_seconds=60,
    ) is None


def test_official_source_cache_rejects_identity_mismatch_invalid_final_url_and_size_metadata(tmp_path: Path):
    url = "https://ris.bka.gv.at/example-2"
    store_cached_source(
        url,
        final_url=url,
        content_type="text/html",
        content=b"body",
        cache_root=tmp_path,
        namespace="checks",
    )
    meta_path = next((tmp_path / "checks").glob("*.json"))
    original = json.loads(meta_path.read_text(encoding="utf-8"))

    for patch in (
        {"listed_url": "https://ris.bka.gv.at/other"},
        {"namespace": "other"},
        {"final_url": "http://ris.bka.gv.at/example-2"},
        {"byte_size": 999},
        {"fetched_at": "not-a-date"},
    ):
        payload = dict(original)
        payload.update(patch)
        meta_path.write_text(json.dumps(payload), encoding="utf-8")
        assert load_cached_source(
            url,
            cache_root=tmp_path,
            namespace="checks",
            max_age_seconds=86400,
        ) is None


def test_official_source_cache_rejects_invalid_configuration_and_empty_content(tmp_path: Path):
    with pytest.raises(ValueError, match="non-negative"):
        load_cached_source(
            "https://ris.bka.gv.at/source",
            cache_root=tmp_path,
            namespace="test",
            max_age_seconds=-1,
        )
    with pytest.raises(ValueError, match="namespace"):
        load_cached_source(
            "https://ris.bka.gv.at/source",
            cache_root=tmp_path,
            namespace="",
            max_age_seconds=1,
        )
    with pytest.raises(ValueError, match="namespace"):
        store_cached_source(
            "https://ris.bka.gv.at/source",
            final_url="https://ris.bka.gv.at/source",
            content_type="text/plain",
            content=b"x",
            cache_root=tmp_path,
            namespace="",
        )
    with pytest.raises(ValueError, match="empty content"):
        store_cached_source(
            "https://ris.bka.gv.at/source",
            final_url="https://ris.bka.gv.at/source",
            content_type="text/plain",
            content=b"",
            cache_root=tmp_path,
            namespace="test",
        )


def test_official_source_cache_rejects_non_https(tmp_path: Path):
    with pytest.raises(ValueError, match="HTTPS"):
        store_cached_source(
            "http://example.com/source",
            final_url="http://example.com/source",
            content_type="text/plain",
            content=b"x",
            cache_root=tmp_path,
            namespace="test",
        )
