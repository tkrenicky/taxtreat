import csv
import json

from taxtreat.tools import benchmark_treaties


def _treaty(country: str = "Testland") -> dict[str, str]:
    return {
        "country_cs": country,
        "title": "1/2026 Sb.m.s.",
        "local_path": "data/raw/treaty/source.pdf",
    }


def test_benchmark_reparses_cached_output_and_reports_identity(monkeypatch, tmp_path):
    parsed_dir = tmp_path / "parsed"
    report = tmp_path / "benchmark.csv"
    parsed_dir.mkdir()
    stale = parsed_dir / "testland.json"
    stale.write_text('{"stale": true}', encoding="utf-8")

    calls = []

    def fake_parse(country, title, pdf, output):
        calls.append((country, title, pdf, output))
        output.write_text(
            json.dumps(
                {
                    "country": country,
                    "identity_validation": {
                        "status": "validated",
                        "reason": "counterparty_matched",
                    },
                    "articles": [],
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(benchmark_treaties, "PARSED_DIR", parsed_dir)
    monkeypatch.setattr(benchmark_treaties, "REPORT", report)
    monkeypatch.setattr(benchmark_treaties, "load_treaties", lambda: [_treaty()])
    monkeypatch.setattr(benchmark_treaties, "parse_treaty", fake_parse)

    benchmark_treaties.main()

    assert len(calls) == 1
    refreshed = json.loads(stale.read_text(encoding="utf-8"))
    assert "stale" not in refreshed
    assert refreshed["identity_validation"]["status"] == "validated"

    with report.open(encoding="utf-8-sig", newline="") as file:
        row = next(csv.DictReader(file))

    assert row["parse_status"] == "ok"
    assert row["identity_status"] == "validated"
    assert row["identity_reason"] == "counterparty_matched"


def test_benchmark_removes_stale_output_when_identity_gate_fails(
    monkeypatch, tmp_path
):
    parsed_dir = tmp_path / "parsed"
    report = tmp_path / "benchmark.csv"
    parsed_dir.mkdir()
    stale = parsed_dir / "testland.json"
    stale.write_text('{"trusted": false}', encoding="utf-8")

    def rejected_parse(country, title, pdf, output):
        raise RuntimeError(
            "Treaty identity rejected: counterparty_not_found "
            "(expected 'Testland')"
        )

    monkeypatch.setattr(benchmark_treaties, "PARSED_DIR", parsed_dir)
    monkeypatch.setattr(benchmark_treaties, "REPORT", report)
    monkeypatch.setattr(benchmark_treaties, "load_treaties", lambda: [_treaty()])
    monkeypatch.setattr(benchmark_treaties, "parse_treaty", rejected_parse)

    benchmark_treaties.main()

    assert not stale.exists()

    with report.open(encoding="utf-8-sig", newline="") as file:
        row = next(csv.DictReader(file))

    assert row["parse_status"] == "failed"
    assert "counterparty_not_found" in row["error"]


def test_failed_identity_is_recorded_in_report(monkeypatch, tmp_path):
    parsed_dir = tmp_path / "parsed"
    report = tmp_path / "benchmark.csv"
    parsed_dir.mkdir()

    def rejected_parse(country, title, pdf, output):
        raise RuntimeError(
            "Treaty identity rejected: counterparty_not_found "
            "(expected 'Testland')"
        )

    monkeypatch.setattr(benchmark_treaties, "PARSED_DIR", parsed_dir)
    monkeypatch.setattr(benchmark_treaties, "REPORT", report)
    monkeypatch.setattr(benchmark_treaties, "load_treaties", lambda: [_treaty()])
    monkeypatch.setattr(benchmark_treaties, "parse_treaty", rejected_parse)

    benchmark_treaties.main()

    with report.open(encoding="utf-8-sig", newline="") as file:
        row = next(csv.DictReader(file))

    assert row["identity_status"] == "rejected"
    assert row["identity_reason"] == "counterparty_not_found"


def test_detector_failure_records_validated_identity():
    result = benchmark_treaties.classify_failed_parse(
        "RuntimeError: Treaty start not found."
    )

    assert result == {
        "identity_status": "validated",
        "identity_reason": "counterparty_matched",
    }


def test_unreadable_source_records_identity_not_run():
    result = benchmark_treaties.classify_failed_parse(
        "pypdf.errors.PdfStreamError: Stream has ended unexpectedly"
    )

    assert result == {
        "identity_status": "not_run",
        "identity_reason": "source_unreadable",
    }
