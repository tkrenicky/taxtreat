from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


@dataclass(frozen=True)
class CachedOfficialSource:
    listed_url: str
    final_url: str
    content_type: str
    content: bytes
    sha256: str
    fetched_at: str
    namespace: str


def _url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_cached_source(
    listed_url: str,
    *,
    cache_root: Path,
    namespace: str,
    max_age_seconds: int,
    now: datetime | None = None,
) -> CachedOfficialSource | None:
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")
    if not namespace.strip():
        raise ValueError("cache namespace must be non-empty")

    root = cache_root / namespace
    key = _url_key(listed_url)
    meta_path = root / f"{key}.json"
    body_path = root / f"{key}.bin"
    if not meta_path.is_file() or not body_path.is_file():
        return None

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("listed_url") != listed_url or meta.get("namespace") != namespace:
            return None
        fetched_at = _parse_time(str(meta["fetched_at"]))
        reference = (now or _now()).astimezone(timezone.utc)
        age = (reference - fetched_at).total_seconds()
        if age < 0 or age > max_age_seconds:
            return None
        content = body_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != meta.get("sha256") or len(content) != int(meta.get("byte_size") or -1):
            return None
        final_url = str(meta.get("final_url") or "")
        if urlsplit(final_url).scheme != "https":
            return None
        return CachedOfficialSource(
            listed_url=listed_url,
            final_url=final_url,
            content_type=str(meta.get("content_type") or ""),
            content=content,
            sha256=digest,
            fetched_at=str(meta["fetched_at"]),
            namespace=namespace,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def store_cached_source(
    listed_url: str,
    *,
    final_url: str,
    content_type: str,
    content: bytes,
    cache_root: Path,
    namespace: str,
    fetched_at: datetime | None = None,
) -> dict[str, Any]:
    if not namespace.strip():
        raise ValueError("cache namespace must be non-empty")
    if urlsplit(listed_url).scheme != "https" or urlsplit(final_url).scheme != "https":
        raise ValueError("official source cache accepts HTTPS URLs only")
    if not content:
        raise ValueError("official source cache cannot store empty content")

    root = cache_root / namespace
    root.mkdir(parents=True, exist_ok=True)
    key = _url_key(listed_url)
    meta_path = root / f"{key}.json"
    body_path = root / f"{key}.bin"
    digest = hashlib.sha256(content).hexdigest()
    timestamp = (fetched_at or _now()).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    body_path.write_bytes(content)
    meta = {
        "schema_version": 1,
        "namespace": namespace,
        "listed_url": listed_url,
        "final_url": final_url,
        "content_type": content_type,
        "byte_size": len(content),
        "sha256": digest,
        "fetched_at": timestamp,
        "cache_is_transport_optimization_not_legal_evidence": True,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta
