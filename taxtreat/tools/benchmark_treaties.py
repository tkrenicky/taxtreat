from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import selectors
import signal
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from taxtreat.engine.extractors import dividend_rule
from taxtreat.validation.document_identity import normalize_legal_text

DB = Path("data/processed/taxtreat_cz.sqlite")
PARSED_DIR = Path("data/parsed")
REPORT = Path("reports/treaty_extraction_benchmark.csv")
CACHE = Path("reports/treaty_extraction_cache.json")
SNAPSHOT_LATEST = Path("reports/snapshots/LATEST")
PARSE_TIMEOUT_SECONDS = int(os.getenv("TAXTREAT_PARSE_TIMEOUT_SECONDS", "1200"))
PROGRESS_INTERVAL_SECONDS = float(os.getenv("TAXTREAT_PROGRESS_INTERVAL_SECONDS", "1"))
CACHE_SCHEMA_VERSION = 1

_IDENTITY_REJECTION_RE = re.compile(
    r"Treaty identity rejected:\s*(?P<reason>[a-z_]+)"
)
_OCR_PROGRESS_RE = re.compile(
    r"^OCR\s+.+?:\s*(?P<completed>\d+)/(?P<total>\d+)\s+pages"
)
_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off", ""}

FIELDNAMES = [
    "country",
    "title",
    "pdf",
    "parsed_file",
    "parse_status",
    "parsed",
    "articles_complete",
    "rules_complete",
    "result_status",
    "cache_status",
    "identity_status",
    "identity_reason",
    "extraction_method",
    "extraction_score",
    "source_resolution_status",
    "source_resolution_method",
    "effective_title",
    "metadata_mismatch",
    "articles_detected",
    "article_10",
    "article_11",
    "article_12",
    "article_10_semantic",
    "article_11_semantic",
    "article_12_semantic",
    "dividend_status",
    "dividend_rates",
    "dividend_conditions",
    "duration_seconds",
    "error",
]

_LIVE_PROGRESS: "LiveProgress | None" = None


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"Invalid boolean value for {name}: {raw!r}")


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in _TRUE_VALUES


def _format_duration(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "--:--"
    rounded = int(seconds)
    hours, remainder = divmod(rounded, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class LiveProgress:
    """Single-line progress display refreshed at a bounded interval."""

    def __init__(self, *, total: int, completed: int = 0) -> None:
        self.total = total
        self.completed = completed
        self.current_country = "preparing"
        self.ocr_completed: int | None = None
        self.ocr_total: int | None = None
        self.started_at = time.monotonic()
        self.current_started_at = self.started_at
        self.last_rendered_at = 0.0
        self.run_durations: list[float] = []

    def begin(self, country: str) -> None:
        self.current_country = country
        self.ocr_completed = None
        self.ocr_total = None
        self.current_started_at = time.monotonic()
        self.render(force=True)

    def update_ocr(self, completed: int, total: int) -> None:
        self.ocr_completed = completed
        self.ocr_total = total
        self.render()

    def finish(self) -> float:
        duration = time.monotonic() - self.current_started_at
        self.run_durations.append(duration)
        self.completed += 1
        self.ocr_completed = None
        self.ocr_total = None
        return duration

    def _eta_seconds(self) -> float | None:
        if not self.run_durations:
            return None
        remaining = max(self.total - self.completed, 0)
        return (sum(self.run_durations) / len(self.run_durations)) * remaining

    def render(self, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self.last_rendered_at < PROGRESS_INTERVAL_SECONDS:
            return
        self.last_rendered_at = now
        percent = 100.0 * self.completed / max(self.total, 1)
        phase = "parse"
        if self.ocr_total is not None:
            phase = f"OCR {self.ocr_completed}/{self.ocr_total}"
        line = (
            f"[{self.completed:>3}/{self.total}] {percent:5.1f}% | "
            f"{self.current_country} | {phase} | "
            f"elapsed {_format_duration(now - self.started_at)} | "
            f"ETA {_format_duration(self._eta_seconds())}"
        )
        sys.stderr.write("\r\x1b[2K" + line)
        sys.stderr.flush()

    def log(self, message: str) -> None:
        sys.stderr.write("\r\x1b[2K" + message + "\n")
        sys.stderr.flush()
        self.last_rendered_at = 0.0

    def close(self) -> None:
        self.render(force=True)
        sys.stderr.write("\n")
        sys.stderr.flush()


def load_treaties() -> list[sqlite3.Row]:
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            cd.country_cs,
            d.title,
            d.local_path
        FROM country_documents cd
        JOIN documents d ON d.id = cd.document_id
        WHERE cd.relation = 'treaty'
          AND d.status = 'downloaded'
          AND d.local_path IS NOT NULL
        ORDER BY cd.country_cs
        """
    ).fetchall()

    connection.close()
    return rows


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def parse_treaty(country: str, title: str, pdf: Path, output: Path) -> None:
    """Run the parser while streaming child output into live progress state."""

    command = [
        sys.executable,
        "-u",
        "parse_treaty.py",
        str(pdf),
        "--country",
        country,
        "--title",
        title or "",
        "--output",
        str(output),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        start_new_session=True,
    )
    assert process.stdout is not None

    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    output_lines: list[str] = []
    started = time.monotonic()

    try:
        while True:
            if time.monotonic() - started > PARSE_TIMEOUT_SECONDS:
                _terminate_process(process)
                raise subprocess.TimeoutExpired(
                    command,
                    PARSE_TIMEOUT_SECONDS,
                    output="".join(output_lines),
                )

            events = selector.select(timeout=0.2)
            for key, _ in events:
                line = key.fileobj.readline()
                if not line:
                    continue
                output_lines.append(line)
                match = _OCR_PROGRESS_RE.match(line.strip())
                if match and _LIVE_PROGRESS is not None:
                    _LIVE_PROGRESS.update_ocr(
                        int(match.group("completed")),
                        int(match.group("total")),
                    )

            if _LIVE_PROGRESS is not None:
                _LIVE_PROGRESS.render()

            if process.poll() is not None:
                remaining = process.stdout.read()
                if remaining:
                    output_lines.append(remaining)
                break
    except BaseException:
        _terminate_process(process)
        raise
    finally:
        selector.close()
        process.stdout.close()

    if process.returncode != 0:
        raise RuntimeError(
            "\nSTDOUT / STDERR\n-----------------\n" + "".join(output_lines)
        )


def classify_failed_parse(error: str) -> dict[str, str]:
    """Classify identity stage for failed parser subprocesses."""

    rejection = _IDENTITY_REJECTION_RE.search(error)
    if rejection:
        return {
            "identity_status": "rejected",
            "identity_reason": rejection.group("reason"),
        }

    if "Treaty start not found" in error:
        return {
            "identity_status": "validated",
            "identity_reason": "counterparty_matched",
        }

    if "PdfStreamError" in error or "Stream has ended unexpectedly" in error:
        return {
            "identity_status": "not_run",
            "identity_reason": "source_unreadable",
        }

    if "timed out" in error.lower():
        return {
            "identity_status": "unknown",
            "identity_reason": "parse_timeout",
        }

    return {
        "identity_status": "unknown",
        "identity_reason": "parser_failed",
    }


def _derive_completion_flags(result: dict[str, object]) -> dict[str, object]:
    parsed = result.get("parse_status") == "ok"
    articles_complete = parsed and all(
        _as_bool(result.get(column))
        for column in (
            "article_10",
            "article_11",
            "article_12",
            "article_10_semantic",
            "article_11_semantic",
            "article_12_semantic",
        )
    )
    rates = str(result.get("dividend_rates", "")).strip()
    rules_complete = (
        articles_complete
        and str(result.get("dividend_status", "")) == "confirmed"
        and bool(rates)
    )

    if not parsed:
        status = "failed"
    elif not articles_complete:
        status = "parsed_only"
    elif not rules_complete:
        status = "articles_complete"
    else:
        status = "complete"

    return {
        "parsed": parsed,
        "articles_complete": articles_complete,
        "rules_complete": rules_complete,
        "result_status": status,
    }


def benchmark(parsed_path: Path) -> dict[str, object]:
    data = json.loads(parsed_path.read_text(encoding="utf-8"))
    articles = {
        article.get("number"): article
        for article in data.get("articles", [])
    }

    identity = data.get("identity_validation") or {}
    extraction = data.get("text_extraction") or {}
    source_resolution = data.get("source_resolution") or {}

    def semantic(number: int, markers: tuple[str, ...]) -> bool:
        article = articles.get(number)
        if not article:
            return False
        text = normalize_legal_text(
            f"{article.get('title', '')}\n{article.get('text', '')}"
        )
        return any(marker in text for marker in markers)

    result: dict[str, object] = {
        "identity_status": identity.get("status", "missing"),
        "identity_reason": identity.get("reason", ""),
        "extraction_method": extraction.get("method", ""),
        "extraction_score": extraction.get("score", ""),
        "source_resolution_status": source_resolution.get("status", ""),
        "source_resolution_method": source_resolution.get("method", ""),
        "effective_title": source_resolution.get("effective_title", ""),
        "metadata_mismatch": source_resolution.get("metadata_mismatch", ""),
        "articles_detected": len(articles),
        "article_10": 10 in articles,
        "article_11": 11 in articles,
        "article_12": 12 in articles,
        "article_10_semantic": semantic(10, ("dividend",)),
        "article_11_semantic": semantic(11, ("urok", "interest")),
        "article_12_semantic": semantic(12, ("licenc", "royalt")),
        "dividend_status": "",
        "dividend_rates": "",
        "dividend_conditions": "",
    }

    if 10 in articles:
        rule = dividend_rule(articles[10].get("text", ""))
        result["dividend_status"] = rule.extraction_status
        result["dividend_rates"] = "|".join(
            str(rate.rate) for rate in rule.rates
        )
        result["dividend_conditions"] = "|".join(
            f"{condition.condition_type.value}:{condition.value}"
            for rate in rule.rates
            for condition in rate.conditions
        )

    return result


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_pipeline_fingerprint() -> str:
    candidates = [Path("parse_treaty.py")]
    candidates.extend(sorted(Path("taxtreat/parser").glob("*.py")))
    candidates.append(Path("taxtreat/validation/document_identity.py"))

    digest = hashlib.sha256()
    for path in sorted({path for path in candidates if path.is_file()}):
        digest.update(str(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _ocr_settings() -> dict[str, str]:
    names = (
        "TAXTREAT_OCR",
        "TAXTREAT_OCR_LANG",
        "TAXTREAT_OCR_DPI",
        "TAXTREAT_OCR_WORKERS",
        "TAXTREAT_OCR_MAX_PAGES",
        "TAXTREAT_OCR_BATCH_PAGES",
        "TAXTREAT_OCR_HARD_MAX_PAGES",
        "TAXTREAT_OFFICIAL_SOURCE",
    )
    defaults = {
        "TAXTREAT_OCR": "auto",
        "TAXTREAT_OCR_LANG": "ces+eng",
        "TAXTREAT_OCR_DPI": "160",
        "TAXTREAT_OCR_WORKERS": "2",
        "TAXTREAT_OCR_MAX_PAGES": "20",
        "TAXTREAT_OCR_BATCH_PAGES": "20",
        "TAXTREAT_OCR_HARD_MAX_PAGES": "0",
        "TAXTREAT_OFFICIAL_SOURCE": "auto",
    }
    return {name: os.getenv(name, defaults[name]) for name in names}


def _settings_fingerprint(settings: dict[str, str]) -> str:
    payload = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as file:
        file.write(text)
        temporary = Path(file.name)
    os.replace(temporary, path)


def _write_report(rows: list[dict[str, object]]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        newline="",
        encoding="utf-8-sig",
        dir=REPORT.parent,
        delete=False,
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(file.name)
    os.replace(temporary, REPORT)


def _empty_cache(parse_fingerprint: str, settings: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "parse_pipeline_fingerprint": parse_fingerprint,
        "ocr_settings": settings,
        "entries": {},
    }


def _load_cache(parse_fingerprint: str, settings: dict[str, str]) -> dict[str, Any]:
    if not CACHE.exists():
        return _empty_cache(parse_fingerprint, settings)
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_cache(parse_fingerprint, settings)
    if data.get("schema_version") != CACHE_SCHEMA_VERSION:
        return _empty_cache(parse_fingerprint, settings)
    if not isinstance(data.get("entries"), dict):
        return _empty_cache(parse_fingerprint, settings)
    return data


def _write_cache(cache: dict[str, Any]) -> None:
    cache["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_text(
        CACHE,
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _latest_snapshot_path() -> Path | None:
    if SNAPSHOT_LATEST.exists():
        raw = SNAPSHOT_LATEST.read_text(encoding="utf-8").strip()
        if raw:
            candidate = Path(raw)
            if candidate.is_dir():
                return candidate
    snapshots = SNAPSHOT_LATEST.parent
    if snapshots.is_dir():
        candidates = sorted(
            path for path in snapshots.iterdir()
            if path.is_dir() and (path / "treaty_extraction_benchmark.csv").exists()
        )
        if candidates:
            return candidates[-1]
    return None


def _safe_restore_parsed_archive(archive: Path) -> int:
    restored = 0
    project_root = Path.cwd().resolve()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = Path(member.name)
            if member_path.parts[:2] != ("data", "parsed"):
                continue
            if not member.isfile():
                continue
            target = (project_root / member_path).resolve()
            if project_root not in target.parents:
                raise RuntimeError(f"Unsafe snapshot member: {member.name}")
            source = tar.extractfile(member)
            if source is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source, target.open("wb") as output:
                output.write(source.read())
            restored += 1
    return restored


def _normalize_snapshot_row(raw: dict[str, str]) -> dict[str, object]:
    row: dict[str, object] = dict(raw)
    row.update(_derive_completion_flags(row))
    row.setdefault("cache_status", "snapshot")
    row.setdefault("duration_seconds", "")
    return row


def _bootstrap_from_snapshot(
    cache: dict[str, Any],
    *,
    treaties_by_country: dict[str, dict[str, str]],
    parse_fingerprint: str,
    settings_fingerprint: str,
) -> list[dict[str, object]]:
    if cache["entries"]:
        return []

    snapshot = _latest_snapshot_path()
    if snapshot is None:
        return []
    report = snapshot / "treaty_extraction_benchmark.csv"
    archive = snapshot / "data_parsed.tar.gz"
    if not report.exists():
        return []

    if archive.exists():
        restored = _safe_restore_parsed_archive(archive)
        print(f"Restored {restored} parsed files from {snapshot}", flush=True)

    with report.open(encoding="utf-8-sig", newline="") as file:
        snapshot_rows = list(csv.DictReader(file))

    rows: list[dict[str, object]] = []
    for raw in snapshot_rows:
        country = raw.get("country", "")
        treaty = treaties_by_country.get(country)
        if treaty is None:
            continue
        row = _normalize_snapshot_row(raw)
        parsed_path = Path(str(row.get("parsed_file", "")))
        source_path = Path(treaty["local_path"])
        source_hash = _sha256_file(source_path)
        parsed_hash = ""

        if row.get("parse_status") == "ok" and parsed_path.exists():
            refreshed = benchmark(parsed_path)
            row.update(refreshed)
            row.update(_derive_completion_flags(row))
            parsed_hash = _sha256_file(parsed_path)

        needs_retry = (
            row.get("parse_status") != "ok"
            or not _as_bool(row.get("articles_complete"))
        )
        cache["entries"][slugify(country)] = {
            "country": country,
            "title": treaty["title"],
            "pdf": treaty["local_path"],
            "source_sha256": source_hash,
            "parse_pipeline_fingerprint": parse_fingerprint,
            "settings_fingerprint": settings_fingerprint,
            "parsed_sha256": parsed_hash,
            "needs_retry": needs_retry,
            "row": row,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        rows.append(row)

    _write_cache(cache)
    _write_report(rows)
    return rows


def _entry_matches(
    entry: dict[str, Any] | None,
    *,
    treaty: dict[str, str],
    source_hash: str,
    parse_fingerprint: str,
    settings_fingerprint: str,
) -> bool:
    if not entry:
        return False
    return (
        entry.get("country") == treaty["country_cs"]
        and entry.get("title", "") == treaty["title"]
        and entry.get("pdf") == treaty["local_path"]
        and entry.get("source_sha256") == source_hash
    )


def _refresh_cached_row(entry: dict[str, Any]) -> dict[str, object]:
    row = dict(entry.get("row") or {})
    parsed_path = Path(str(row.get("parsed_file", "")))
    if row.get("parse_status") == "ok":
        if not parsed_path.exists():
            raise FileNotFoundError(parsed_path)
        expected_hash = entry.get("parsed_sha256", "")
        if expected_hash and _sha256_file(parsed_path) != expected_hash:
            raise RuntimeError(f"Cached parsed file hash mismatch: {parsed_path}")
        row.update(benchmark(parsed_path))
    row.update(_derive_completion_flags(row))
    row["cache_status"] = "reused"
    return row


def _result_label(row: dict[str, object]) -> str:
    status = row.get("result_status")
    return {
        "complete": "COMPLETE",
        "articles_complete": "PARTIAL-RULES",
        "parsed_only": "PARTIAL-ARTICLES",
        "failed": "FAILED",
    }.get(str(status), "UNKNOWN")


def _persist_state(
    *,
    rows_by_country: dict[str, dict[str, object]],
    treaty_order: list[str],
    cache: dict[str, Any],
) -> None:
    rows = [rows_by_country[country] for country in treaty_order if country in rows_by_country]
    _write_report(rows)
    _write_cache(cache)


def main() -> None:
    global _LIVE_PROGRESS

    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    treaties = [dict(row) for row in load_treaties()]
    treaty_order = [treaty["country_cs"] for treaty in treaties]
    treaties_by_country = {treaty["country_cs"]: treaty for treaty in treaties}
    parse_fingerprint = _parse_pipeline_fingerprint()
    settings = _ocr_settings()
    settings_fingerprint = _settings_fingerprint(settings)
    cache = _load_cache(parse_fingerprint, settings)

    snapshot_rows = _bootstrap_from_snapshot(
        cache,
        treaties_by_country=treaties_by_country,
        parse_fingerprint=parse_fingerprint,
        settings_fingerprint=settings_fingerprint,
    )
    rows_by_country = {
        str(row["country"]): row
        for row in snapshot_rows
        if row.get("country")
    }

    force = _env_flag("TAXTREAT_BENCHMARK_FORCE", False)
    pending: list[tuple[dict[str, str], str]] = []
    reused = 0

    print("Preparing cache keys...", flush=True)
    for treaty in treaties:
        country = treaty["country_cs"]
        key = slugify(country)
        source_hash = _sha256_file(Path(treaty["local_path"]))
        entry = cache["entries"].get(key)
        matches = _entry_matches(
            entry,
            treaty=treaty,
            source_hash=source_hash,
            parse_fingerprint=parse_fingerprint,
            settings_fingerprint=settings_fingerprint,
        )

        should_run = force or not matches
        if matches and not force:
            try:
                row = _refresh_cached_row(entry)
                should_run = (
                    not _as_bool(row.get("parsed"))
                    or not _as_bool(row.get("articles_complete"))
                )
                if not should_run:
                    rows_by_country[country] = row
                    entry["row"] = row
                    entry["needs_retry"] = False
                    entry["parse_pipeline_fingerprint"] = parse_fingerprint
                    entry["settings_fingerprint"] = settings_fingerprint
                    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                    reused += 1
                    continue
            except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
                should_run = True

        pending.append((treaty, source_hash))

    _persist_state(
        rows_by_country=rows_by_country,
        treaty_order=treaty_order,
        cache=cache,
    )

    print(
        f"Cache: {reused} reused, {len(pending)} queued, {len(treaties)} total",
        flush=True,
    )

    _LIVE_PROGRESS = LiveProgress(total=len(treaties), completed=reused)

    try:
        for treaty, source_hash in pending:
            country = treaty["country_cs"]
            title = treaty["title"] or ""
            pdf = Path(treaty["local_path"])
            parsed_path = PARSED_DIR / f"{slugify(country)}.json"
            key = slugify(country)

            row: dict[str, object] = {
                "country": country,
                "title": title,
                "pdf": str(pdf),
                "parsed_file": str(parsed_path),
                "parse_status": "pending",
                "cache_status": "fresh",
                "error": "",
            }

            _LIVE_PROGRESS.begin(country)
            try:
                parsed_path.unlink(missing_ok=True)
                parse_treaty(country, title, pdf, parsed_path)
                row["parse_status"] = "ok"
                row.update(benchmark(parsed_path))

            except subprocess.TimeoutExpired as exc:
                row["parse_status"] = "failed"
                row["error"] = (
                    f"Parser timed out after {PARSE_TIMEOUT_SECONDS} seconds: {exc}"
                )
                row.update(classify_failed_parse(str(row["error"])))
                parsed_path.unlink(missing_ok=True)

            except Exception as exc:
                row["parse_status"] = "failed"
                row["error"] = str(exc)
                row.update(classify_failed_parse(str(row["error"])))
                parsed_path.unlink(missing_ok=True)

            duration = _LIVE_PROGRESS.finish()
            row["duration_seconds"] = round(duration, 3)
            row.update(_derive_completion_flags(row))
            rows_by_country[country] = row

            cache["entries"][key] = {
                "country": country,
                "title": title,
                "pdf": str(pdf),
                "source_sha256": source_hash,
                "parse_pipeline_fingerprint": parse_fingerprint,
                "settings_fingerprint": settings_fingerprint,
                "parsed_sha256": (
                    _sha256_file(parsed_path)
                    if row["parse_status"] == "ok" and parsed_path.exists()
                    else ""
                ),
                "needs_retry": (
                    not _as_bool(row.get("parsed"))
                    or not _as_bool(row.get("articles_complete"))
                ),
                "row": row,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            _persist_state(
                rows_by_country=rows_by_country,
                treaty_order=treaty_order,
                cache=cache,
            )

            _LIVE_PROGRESS.log(
                f"{_result_label(row):16} {country} "
                f"identity={row.get('identity_status', '')} "
                f"extract={row.get('extraction_method', '')} "
                f"A10={row.get('article_10', '')} "
                f"rates={row.get('dividend_rates', '')} "
                f"({duration:.1f}s)"
            )

    except KeyboardInterrupt:
        _persist_state(
            rows_by_country=rows_by_country,
            treaty_order=treaty_order,
            cache=cache,
        )
        if _LIVE_PROGRESS is not None:
            _LIVE_PROGRESS.log("Interrupted safely; completed results were saved.")
        raise
    finally:
        if _LIVE_PROGRESS is not None:
            _LIVE_PROGRESS.close()
        _LIVE_PROGRESS = None

    rows = [rows_by_country[country] for country in treaty_order if country in rows_by_country]
    parsed = sum(_as_bool(row.get("parsed")) for row in rows)
    articles_complete = sum(_as_bool(row.get("articles_complete")) for row in rows)
    rules_complete = sum(_as_bool(row.get("rules_complete")) for row in rows)
    failed = len(rows) - parsed

    print()
    print(f"Treaties: {len(rows)}")
    print(f"Parsed: {parsed}")
    print(f"Articles complete: {articles_complete}")
    print(f"Rules complete: {rules_complete}")
    print(f"Failed: {failed}")
    print(f"Cache: {CACHE}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
