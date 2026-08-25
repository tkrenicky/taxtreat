from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def test_official_source_cache_expires_and_is_namespaced(tmp_path: Path):
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


def test_official_source_cache_rejects_empty_namespace_and_non_https(tmp_path: Path):
    try:
        store_cached_source(
            "http://example.com/source",
            final_url="http://example.com/source",
            content_type="text/plain",
            content=b"x",
            cache_root=tmp_path,
            namespace="test",
        )
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("Expected non-HTTPS cache write to fail")
