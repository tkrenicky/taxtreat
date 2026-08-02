import csv
import json
from pathlib import Path

import pytest

from taxtreat.tools import benchmark_treaties


def _parsed_payload(*, include_article_10: bool = True) -> dict:
    articles = []
    if include_article_10:
        articles = [
            {"number": 10, "title": "DIVIDENDY", "text": "Dividendy 15 procent."},
            {"number": 11, "title": "ÚROKY", "text": "Úroky."},
            {"number": 12, "title": "LICENČNÍ POPLATKY", "text": "Poplatky."},
        ]
    return {
        "identity_validation": {
            "status": "validated",
            "reason": "counterparty_matched",
        },
        "text_extraction": {"method": "pypdf", "score": 100},
        "source_resolution": {"status": "fallback", "method": "whole_document"},
        "articles": articles,
    }


@pytest.fixture
def benchmark_env(monkeypatch, tmp_path):
    parsed_dir = tmp_path / "data" / "parsed"
    report = tmp_path / "reports" / "benchmark.csv"
    cache = tmp_path / "reports" / "cache.json"
    snapshot_latest = tmp_path / "reports" / "snapshots" / "LATEST"
    source = tmp_path / "data" / "raw" / "source.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"source-v1")

    treaty = {
        "country_cs": "Testland",
        "title": "1/2026 Sb.m.s.",
        "local_path": str(source),
    }

    monkeypatch.setattr(benchmark_treaties, "PARSED_DIR", parsed_dir)
    monkeypatch.setattr(benchmark_treaties, "REPORT", report)
    monkeypatch.setattr(benchmark_treaties, "CACHE", cache)
    monkeypatch.setattr(benchmark_treaties, "SNAPSHOT_LATEST", snapshot_latest)
    monkeypatch.setattr(benchmark_treaties, "PROGRESS_INTERVAL_SECONDS", 3600)
    monkeypatch.setattr(benchmark_treaties, "load_treaties", lambda: [treaty])

    return {
        "parsed_dir": parsed_dir,
        "report": report,
        "cache": cache,
        "source": source,
        "treaty": treaty,
    }


def _successful_parser(calls, *, include_article_10=True):
    def parse(country, title, pdf, output):
        calls.append(country)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(_parsed_payload(include_article_10=include_article_10)),
            encoding="utf-8",
        )

    return parse


def test_second_run_reuses_valid_parsed_cache(monkeypatch, benchmark_env):
    calls = []
    monkeypatch.setattr(
        benchmark_treaties,
        "parse_treaty",
        _successful_parser(calls),
    )

    benchmark_treaties.main()
    benchmark_treaties.main()

    assert calls == ["Testland"]
    with benchmark_env["report"].open(encoding="utf-8-sig", newline="") as file:
        row = next(csv.DictReader(file))
    assert row["cache_status"] == "reused"
    assert row["parsed"] == "True"
    assert row["articles_complete"] == "True"


def test_source_change_invalidates_cache(monkeypatch, benchmark_env):
    calls = []
    monkeypatch.setattr(
        benchmark_treaties,
        "parse_treaty",
        _successful_parser(calls),
    )

    benchmark_treaties.main()
    benchmark_env["source"].write_bytes(b"source-v2")
    benchmark_treaties.main()

    assert calls == ["Testland", "Testland"]


def test_incomplete_result_is_not_retried_forever(monkeypatch, benchmark_env):
    calls = []
    monkeypatch.setattr(
        benchmark_treaties,
        "parse_treaty",
        _successful_parser(calls, include_article_10=False),
    )

    benchmark_treaties.main()
    benchmark_treaties.main()

    assert calls == ["Testland"]
    cache = json.loads(benchmark_env["cache"].read_text(encoding="utf-8"))
    entry = cache["entries"]["testland"]
    assert entry["needs_retry"] is False
    assert entry["row"]["result_status"] == "parsed_only"


def test_report_and_cache_are_written_after_each_country(monkeypatch, benchmark_env):
    observed = []

    def parse(country, title, pdf, output):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(_parsed_payload()), encoding="utf-8")

    original_persist = benchmark_treaties._persist_state

    def recording_persist(**kwargs):
        original_persist(**kwargs)
        observed.append(
            (
                benchmark_env["report"].exists(),
                benchmark_env["cache"].exists(),
            )
        )

    monkeypatch.setattr(benchmark_treaties, "parse_treaty", parse)
    monkeypatch.setattr(benchmark_treaties, "_persist_state", recording_persist)

    benchmark_treaties.main()

    assert observed
    assert observed[-1] == (True, True)


def test_snapshot_bootstrap_retries_only_failed_and_article_incomplete(
    monkeypatch, tmp_path
):
    parsed_dir = tmp_path / "data" / "parsed"
    report = tmp_path / "reports" / "benchmark.csv"
    cache = tmp_path / "reports" / "cache.json"
    snapshot = tmp_path / "reports" / "snapshots" / "20260802_110706"
    latest = snapshot.parent / "LATEST"
    snapshot.mkdir(parents=True)
    latest.write_text(str(snapshot), encoding="utf-8")

    treaties = []
    for country in ("Complete", "Incomplete", "Failed"):
        source = tmp_path / "data" / "raw" / f"{country}.pdf"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(country.encode("utf-8"))
        treaties.append(
            {
                "country_cs": country,
                "title": f"{country}/2026",
                "local_path": str(source),
            }
        )

    archive_root = tmp_path / "archive"
    archived_parsed = archive_root / "data" / "parsed"
    archived_parsed.mkdir(parents=True)
    (archived_parsed / "complete.json").write_text(
        json.dumps(_parsed_payload(include_article_10=True)), encoding="utf-8"
    )
    (archived_parsed / "incomplete.json").write_text(
        json.dumps(_parsed_payload(include_article_10=False)), encoding="utf-8"
    )

    import tarfile

    with tarfile.open(snapshot / "data_parsed.tar.gz", "w:gz") as tar:
        tar.add(archive_root / "data", arcname="data")

    old_fields = [
        "country", "title", "pdf", "parsed_file", "parse_status",
        "identity_status", "identity_reason", "extraction_method",
        "extraction_score", "source_resolution_status",
        "source_resolution_method", "effective_title", "metadata_mismatch",
        "articles_detected", "article_10", "article_11", "article_12",
        "dividend_status", "dividend_rates", "dividend_conditions", "error",
    ]
    rows = [
        {
            "country": "Complete",
            "title": "Complete/2026",
            "pdf": treaties[0]["local_path"],
            "parsed_file": "data/parsed/complete.json",
            "parse_status": "ok",
            "article_10": "True",
            "article_11": "True",
            "article_12": "True",
            "dividend_status": "confirmed",
            "dividend_rates": "15.0",
        },
        {
            "country": "Incomplete",
            "title": "Incomplete/2026",
            "pdf": treaties[1]["local_path"],
            "parsed_file": "data/parsed/incomplete.json",
            "parse_status": "ok",
            "article_10": "False",
            "article_11": "False",
            "article_12": "False",
        },
        {
            "country": "Failed",
            "title": "Failed/2026",
            "pdf": treaties[2]["local_path"],
            "parsed_file": "data/parsed/failed.json",
            "parse_status": "failed",
            "error": "source failed",
        },
    ]
    with (snapshot / "treaty_extraction_benchmark.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=old_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    calls = []

    def parse(country, title, pdf, output):
        calls.append(country)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(_parsed_payload()), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(benchmark_treaties, "PARSED_DIR", parsed_dir)
    monkeypatch.setattr(benchmark_treaties, "REPORT", report)
    monkeypatch.setattr(benchmark_treaties, "CACHE", cache)
    monkeypatch.setattr(benchmark_treaties, "SNAPSHOT_LATEST", latest)
    monkeypatch.setattr(benchmark_treaties, "PROGRESS_INTERVAL_SECONDS", 3600)
    monkeypatch.setattr(benchmark_treaties, "load_treaties", lambda: treaties)
    monkeypatch.setattr(benchmark_treaties, "parse_treaty", parse)
    monkeypatch.setattr(
        benchmark_treaties,
        "_parse_pipeline_fingerprint",
        lambda: "parse-fingerprint",
    )

    benchmark_treaties.main()

    assert calls == ["Incomplete", "Failed"]
    with report.open(encoding="utf-8-sig", newline="") as file:
        final_rows = {row["country"]: row for row in csv.DictReader(file)}
    assert final_rows["Complete"]["cache_status"] == "reused"
    assert final_rows["Incomplete"]["parse_status"] == "ok"
    assert final_rows["Failed"]["parse_status"] == "ok"
