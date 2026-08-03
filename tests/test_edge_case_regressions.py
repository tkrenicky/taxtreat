from __future__ import annotations

import csv
import json
import subprocess
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from taxtreat.engine import decision_engine
from taxtreat.engine.domestic_law_engine import DomesticLawEngine
from taxtreat.engine.models import ConditionType
from taxtreat.engine.rule_extractor import extract_dividend_rules
from taxtreat.generator import generate_all_cases
from taxtreat.parser import article_selection, extractor, official_source, publication
from taxtreat.pipeline import build_database, run_pipeline
from taxtreat.registry import cz_registry
from taxtreat.tools import benchmark_treaties, fetch_official_sources, validate_knowledge_base
from taxtreat.validation import confidence_engine, document_identity, quality_gate


class _Headers:
    def __init__(self, content_type: str | None = None, *, mapping: bool = False):
        self.content_type = content_type
        self.mapping = mapping

    def get_content_type(self):
        if self.mapping:
            raise AssertionError("mapping header has no MIME helper")
        return self.content_type

    def get(self, key, default=""):
        return self.content_type or default


class _Response:
    def __init__(self, payload: bytes, content_type: str | None = "text/html", *, headers=True):
        self.payload = payload
        self.headers = _Headers(content_type) if headers else None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def _complete_text(country="Rwanda", rate="10"):
    return (
        f"Smlouva mezi Českou republikou a {country} o zamezení dvojímu zdanění.\n"
        "Článek 1\nOSOBY\nText.\n"
        f"Článek 10\nDIVIDENDY\nDaň nepřesáhne {rate} procent.\n"
        "Článek 11\nÚROKY\nText.\n"
        "Článek 12\nLICENČNÍ POPLATKY\nText.\n"
        "Článek 13\nZISKY ZE ZCIZENÍ MAJETKU\nText."
    )


def test_small_uncovered_engine_branches():
    condition = SimpleNamespace(
        condition_type=ConditionType.minimum_ownership,
        operator=">=",
        value=10,
        unit="percent",
    )
    assert decision_engine._evaluate_condition(condition, {"ownership": "bad"}) == (False, None, True)

    condition.condition_type = ConditionType.minimum_holding_period
    condition.value = 1
    condition.unit = "year"
    assert decision_engine._evaluate_condition(condition, {}) == (False, "holding_months", False)
    assert decision_engine._evaluate_condition(condition, {"holding_months": "bad"}) == (False, None, True)
    condition.operator = "contains"
    assert decision_engine._evaluate_condition(condition, {"holding_months": 12}) == (False, None, True)

    extracted = extract_dividend_rules("DIVIDENDY 15 procent; nejméně 25 procent kapitálu")
    assert extracted["rates"] == [15, 25]
    assert extracted["minimum_ownership_percent"] == 25


def test_domestic_date_branches():
    engine = DomesticLawEngine()
    future = SimpleNamespace(effective_date=date(2030, 1, 1), conditions=[], rate=10)
    current = SimpleNamespace(effective_date=date(2020, 1, 1), conditions=[], rate=15)
    rule = SimpleNamespace(rates=[future, current], effective_date=None, rate=None, article=1)
    result = engine.evaluate(rule, {}, effective_date=date(2025, 1, 1))
    assert result.rate == 15
    assert engine._applies_to_date(future, date(2025, 1, 1)) is False


def test_misc_validation_branches(monkeypatch, tmp_path):
    assert article_selection.article_type({"title": "DIVIDENDY", "text": "x"}) == "dividend"
    assert article_selection._embedded_heading("Článek xx\n\n", "dividend") is None
    payload = [{"number": "bad", "title": "x", "text": "x"}, {"number": 10, "title": "DIVIDENDY", "text": "x"}]
    assert [a.number for a in article_selection.articles_from_payload(payload)] == [10]
    assert publication._effective_title(9, "without reference") == "9"

    registry = tmp_path / "registry.json"
    registry.write_text('[{"iso2":"DE","country":"Germany"}]', encoding="utf-8")
    monkeypatch.setattr(cz_registry, "REGISTRY", registry)
    assert len(cz_registry.generate_scope()) == 3

    low = confidence_engine.calculate_confidence({"parser_warnings": ["x"]})
    assert low["confidence"] == 0 and low["manual_review"] is True
    errors = quality_gate.validate_record({"confidence": 10, "manual_review": False})
    assert "Confidence below threshold but manual_review=False" in errors

    assert document_identity.publication_reference(None) is None
    assert document_identity.publication_reference("not a reference") is None


def test_generate_all_cases_and_pipeline_helpers(monkeypatch, tmp_path, capsys):
    with pytest.raises(FileNotFoundError):
        generate_all_cases.load_partners(tmp_path / "missing.sqlite")
    with pytest.raises(RuntimeError):
        generate_all_cases.write_csv([], tmp_path / "x.csv")

    rows = [{"payer": "CZ", "recipient_country_cs": "Test", "recipient_iso2": "", "income_type": "dividend", "status": "PENDING", "confidence": 0, "manual_review": True}]
    output = tmp_path / "out" / "cases.csv"
    generate_all_cases.write_csv(rows, output)
    assert output.exists() and "recipient_country_cs" in output.read_text(encoding="utf-8-sig")
    monkeypatch.setattr(generate_all_cases, "generate", lambda: rows)
    monkeypatch.setattr(generate_all_cases, "write_csv", lambda value: None)
    monkeypatch.setattr(generate_all_cases, "OUTPUT", output)
    generate_all_cases.main()
    assert "Treaty partners: 1" in capsys.readouterr().out

    build_calls = []
    monkeypatch.setattr(
        build_database,
        "build_source_manifest",
        lambda: build_calls.append("sources"),
    )
    monkeypatch.setattr(
        build_database,
        "build_legal_registry",
        lambda: build_calls.append("registry"),
    )
    monkeypatch.setattr(
        build_database,
        "build_release_manifest",
        lambda: build_calls.append("release"),
    )
    build_database.main()
    assert build_calls == ["sources", "registry", "release"]
    assert "Canonical manifests exported" in capsys.readouterr().out

    calls = []
    monkeypatch.setattr(
        run_pipeline,
        "STEPS",
        [("one", lambda: calls.append("one")), ("two", lambda: calls.append("two"))],
    )
    monkeypatch.setattr(
        run_pipeline,
        "validate_release",
        lambda **kwargs: calls.append(kwargs),
    )
    run_pipeline.main([])
    assert calls == ["one", "two", {"production": False}]
    assert "finished successfully" in capsys.readouterr().out

    monkeypatch.setattr(
        run_pipeline,
        "STEPS",
        [("broken", lambda: (_ for _ in ()).throw(RuntimeError("boom")))],
    )
    with pytest.raises(SystemExit) as exc:
        run_pipeline.main([])
    assert exc.value.code == 1


def test_validate_knowledge_base_all_paths(monkeypatch, tmp_path, capsys):
    invalid_root = tmp_path / "invalid.yaml"
    invalid_root.write_text("- x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_knowledge_base.load_yaml(invalid_root)

    invalid = tmp_path / "bad.yaml"
    invalid.write_text(
        "income_type: other\nstatus: bad\npayer_country: cze\nrecipient_country: 1\n"
        "domestic_law: []\ntreaty: []\ndocumentation: x\nsources: x\n",
        encoding="utf-8",
    )
    errors = validate_knowledge_base.validate_file(invalid)
    assert len(errors) >= 8

    root = tmp_path / "kb"
    monkeypatch.setattr(validate_knowledge_base, "ROOT", root)
    assert validate_knowledge_base.main() == 1
    root.mkdir()
    valid = root / "valid.yaml"
    valid.write_text(
        "id: x\npayer_country: CZ\nrecipient_country: DE\nincome_type: dividends\n"
        "domestic_law: {standard_rate: 15, legal_reference: law}\n"
        "treaty: {applicable: true}\ndocumentation: []\nsources: []\nstatus: verified\n",
        encoding="utf-8",
    )
    assert validate_knowledge_base.main() == 0
    invalid.replace(root / "bad.yaml")
    assert validate_knowledge_base.main() == 1
    assert "FAIL" in capsys.readouterr().out


def test_fetch_official_sources_success_failure_and_rejection(monkeypatch, tmp_path, capsys):
    dataset = tmp_path / "dataset.csv"
    archive = tmp_path / "archive"
    manifest = tmp_path / "manifest.json"
    dataset.write_text(
        "official_treaty_source,official_domestic_source\n"
        "https://mfcr.cz/a.pdf,https://evil.example/x\n"
        "https://mfcr.cz/fail,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fetch_official_sources, "DATASET", dataset)
    monkeypatch.setattr(fetch_official_sources, "ARCHIVE", archive)
    monkeypatch.setattr(fetch_official_sources, "MANIFEST", manifest)
    monkeypatch.setattr(fetch_official_sources.time, "sleep", lambda _: None)
    def fake_download(url):
        if url.endswith("fail"):
            raise OSError("boom")
        return b"pdf"
    original_download = fetch_official_sources.download
    monkeypatch.setattr(fetch_official_sources, "download", fake_download)
    with pytest.raises(SystemExit) as exc:
        fetch_official_sources.main()
    assert exc.value.code == 1
    records = json.loads(manifest.read_text())
    assert {r["status"] for r in records} == {"downloaded", "failed", "rejected"}
    assert "Official URLs found: 3" in capsys.readouterr().out

    monkeypatch.setattr(fetch_official_sources, "DATASET", tmp_path / "missing.csv")
    with pytest.raises(SystemExit):
        fetch_official_sources.main()

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b"ok"
    monkeypatch.setattr(fetch_official_sources, "urlopen", lambda request, timeout: Response())
    assert original_download("https://mfcr.cz/x") == b"ok"


def test_official_source_low_level_helpers():
    assert official_source.official_source_urls(None) == ()
    assert official_source.official_download_urls(None) == ()
    assert official_source.verified_mirror_urls(None) == ()
    assert official_source._content_type(SimpleNamespace(headers=None)) == ""
    assert official_source._content_type(SimpleNamespace(headers={"Content-Type": "Application/JSON; charset=utf-8"})) == "application/json"
    html = b"<html><body><script>x</script><main>short</main><article>" + b"Treaty " * 100 + b"</article></body></html>"
    text = official_source._html_to_text(html)
    assert "Treaty" in text and "<script>" not in text and "x" not in text
    nested = b'{"a":"one","b":["two",{"c":"three"}]}'
    assert official_source._json_to_text(nested) == "one\ntwo\nthree"
    assert official_source._structured_to_text(nested, url="x", content_type="application/json") == "one\ntwo\nthree"
    assert official_source._structured_to_text(b"{bad", url="x.json", content_type="") is None


def test_official_source_link_and_mirror_error_paths(monkeypatch):
    payload = b'''<html><body><a>none</a><a href="https://evil.example/x.pdf">bad</a>
    <a href="/file.pdf">Download PDF</a><script>"https:\\/\\/e-sbirka.gov.cz\\/download\\/other.pdf"</script></body></html>'''
    urls = official_source._linked_document_urls(payload, "https://e-sbirka.gov.cz/sb/1")
    assert urls[0].endswith("/file.pdf") and any("other.pdf" in u for u in urls)

    errors = []
    monkeypatch.setattr(official_source, "_linked_document_urls", lambda *a: ("https://e-sbirka.gov.cz/a.pdf", "https://e-sbirka.gov.cz/b.pdf", "https://e-sbirka.gov.cz/c.pdf"))
    responses = iter([
        OSError("network"),
        _Response(b"not pdf", "text/plain"),
        _Response(b"%PDF fake", "application/pdf"),
    ])
    def fake_open(*a, **k):
        item = next(responses)
        if isinstance(item, Exception): raise item
        return item
    monkeypatch.setattr(official_source, "urlopen", fake_open)
    monkeypatch.setattr(extractor, "extract_document", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bad pdf")))
    assert official_source._extract_linked_pdf(b"x", url="https://e-sbirka.gov.cz/x", timeout=1, expected_country="Rwanda", source_title="1/2020 Sb.", errors=errors) is None
    assert any("network" in e for e in errors) and any("bad pdf" in e for e in errors)

    assert official_source._fetch_verified_mirror(None, expected_country=None, timeout=1, errors=[]) is None
    mirror_errors = []
    monkeypatch.setattr(official_source, "verified_mirror_urls", lambda _: ("https://www.zakonyprolidi.cz/cs/2024-1",) * 4)
    mirror_responses = iter([
        OSError("down"),
        _Response(b"x", "application/pdf"),
        _Response(b"<html><body>challenge</body></html>"),
        _Response(b"<html><body>1/2024 Sb. incomplete</body></html>"),
    ])
    def mirror_open(*a, **k):
        item = next(mirror_responses)
        if isinstance(item, Exception): raise item
        return item
    monkeypatch.setattr(official_source, "urlopen", mirror_open)
    monkeypatch.setattr(official_source, "_complete_treaty_pages", lambda *a, **k: False)
    assert official_source._fetch_verified_mirror("1/2024 Sb.", expected_country="X", timeout=1, errors=mirror_errors) is None
    assert len(mirror_errors) == 4


def test_fetch_official_document_branches(monkeypatch):
    monkeypatch.setenv("TAXTREAT_OFFICIAL_SOURCE", "off")
    with pytest.raises(official_source.OfficialSourceError):
        official_source.fetch_official_document("1/2020 Sb.")
    monkeypatch.setenv("TAXTREAT_OFFICIAL_SOURCE", "auto")
    with pytest.raises(official_source.OfficialSourceError):
        official_source.fetch_official_document("no ref")

    monkeypatch.setattr(official_source, "official_download_urls", lambda _: ("https://e-sbirka.gov.cz/a",))
    monkeypatch.setattr(official_source, "official_source_urls", lambda _: ())
    monkeypatch.setattr(official_source, "_fetch_verified_mirror", lambda *a, **k: None)

    # Direct PDF accepted.
    monkeypatch.setattr(official_source, "urlopen", lambda *a, **k: _Response(b"%PDF fake", "application/pdf"))
    monkeypatch.setattr(extractor, "extract_document", lambda *a, **k: extractor.ExtractionResult([_complete_text()], "ocr", 1))
    monkeypatch.setattr(official_source, "_complete_treaty_pages", lambda *a, **k: True)
    result = official_source.fetch_official_document("1/2020 Sb.", expected_country="Rwanda")
    assert result.pages

    # PDF extraction error falls through to final error.
    monkeypatch.setattr(extractor, "extract_document", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bad")))
    with pytest.raises(official_source.OfficialSourceError) as exc:
        official_source.fetch_official_document("1/2020 Sb.")
    assert "bad" in str(exc.value)

    # Unsupported content type.
    monkeypatch.setattr(official_source, "urlopen", lambda *a, **k: _Response(b"binary", "image/png"))
    with pytest.raises(official_source.OfficialSourceError) as exc:
        official_source.fetch_official_document("1/2020 Sb.")
    assert "unsupported content type" in str(exc.value)

    # Complete HTML accepted and short HTML reaches linked/final error path.
    monkeypatch.setattr(official_source, "urlopen", lambda *a, **k: _Response((_complete_text()*30).encode(), "text/html"))
    monkeypatch.setattr(official_source, "_complete_treaty_pages", lambda *a, **k: True)
    assert official_source.fetch_official_document("1/2020 Sb.").url.endswith("/a")

    monkeypatch.setattr(official_source, "urlopen", lambda *a, **k: _Response(b"<html>short</html>", "text/html"))
    monkeypatch.setattr(official_source, "_complete_treaty_pages", lambda *a, **k: False)
    monkeypatch.setattr(official_source, "_extract_linked_pdf", lambda *a, **k: None)
    with pytest.raises(official_source.OfficialSourceError) as exc:
        official_source.fetch_official_document("1/2020 Sb.")
    assert "did not expose" in str(exc.value)


def test_extractor_backend_and_ocr_helpers(monkeypatch, tmp_path):
    monkeypatch.setattr(
        extractor.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="one\ftwo"),
    )
    assert extractor._extract_with_pdftotext(tmp_path / "x.pdf") == ["one", "two"]
    assert extractor._ocr_image(tmp_path / "x.png", "eng") == "one\ftwo"

    html = tmp_path / "x.html"
    html.write_text("<html><script>bad</script><style>x</style><body>good</body></html>")
    assert "good" in extractor._extract_html(html)[0]
    assert "bad" not in extractor._extract_html(html)[0]

    monkeypatch.setenv("TAXTREAT_OCR", "always")
    assert extractor._should_ocr(extractor.ExtractionAttempt("x", 0, 0, 0)) is True
    assert extractor._numeric_image_sort_key(Path("page-0012.png"))[0] == 12
    assert extractor._numeric_image_sort_key(Path("plain.png"))[0] == 0

    monkeypatch.setattr(
        extractor.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="Title: x\nPages: 12\n"),
    )
    assert extractor._pdf_page_count(tmp_path / "x.pdf") == 12


def test_extractor_ocr_page_and_failure_paths(monkeypatch, tmp_path):
    workdir = tmp_path / "work"
    workdir.mkdir()

    def render_ok(command, **kwargs):
        prefix = Path(command[-1])
        prefix.with_suffix(".png").write_bytes(b"image")
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(extractor.subprocess, "run", render_ok)
    monkeypatch.setattr(extractor, "_ocr_image", lambda path, language: "OCR")
    assert extractor._ocr_pdf_page(tmp_path / "x.pdf", 1, dpi=100, language="eng", workdir=workdir) == "OCR"

    monkeypatch.setattr(extractor.subprocess, "run", lambda *a, **k: SimpleNamespace())
    with pytest.raises(RuntimeError, match="produced no image"):
        extractor._ocr_pdf_page(tmp_path / "x.pdf", 2, dpi=100, language="eng", workdir=workdir)

    monkeypatch.setattr(extractor.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="not installed"):
        extractor._extract_with_ocr(tmp_path / "x.pdf")

    monkeypatch.setattr(extractor.shutil, "which", lambda name: "/bin/tool")
    monkeypatch.setattr(extractor, "_pdf_page_count", lambda path: 0)
    with pytest.raises(RuntimeError, match="positive PDF page count"):
        extractor._extract_with_ocr(tmp_path / "x.pdf")


def test_extract_document_failure_and_legacy_ocr_paths(monkeypatch, tmp_path):
    html = tmp_path / "bad.html"
    html.write_text("x")
    monkeypatch.setattr(extractor, "_extract_html", lambda path: (_ for _ in ()).throw(ValueError("bad html")))
    result = extractor.extract_document(html)
    assert result.method == "failed" and "bad html" in result.attempts[0].error

    pdf = tmp_path / "x.pdf"
    monkeypatch.setattr(extractor, "_extract_with_pypdf", lambda path: (_ for _ in ()).throw(ValueError("bad")))
    monkeypatch.setattr(extractor, "_extract_with_pdftotext", lambda path: (_ for _ in ()).throw(ValueError("bad")))
    assert extractor.extract_document(pdf).method == "failed"

    pages = ["Článek 1\nX"]
    monkeypatch.setattr(extractor, "_extract_with_pypdf", lambda path: pages)
    monkeypatch.setattr(extractor, "_extract_with_pdftotext", lambda path: (_ for _ in ()).throw(ValueError("bad")))
    monkeypatch.setattr(extractor, "_should_ocr", lambda attempt: True)
    calls = []
    def legacy_ocr(path, **kwargs):
        calls.append(kwargs)
        if kwargs:
            raise TypeError("unexpected keyword argument 'expected_country'")
        return ["Článek 1\nX\nČlánek 10\nDIVIDENDY\nČlánek 11\nÚROKY\nČlánek 12\nLICENČNÍ POPLATKY"]
    monkeypatch.setattr(extractor, "_extract_with_ocr", legacy_ocr)
    assert "ocr" in extractor.extract_document(pdf, expected_country="X").method
    assert calls == [{"expected_country": "X", "source_title": None}, {}]

    def wrong_type(path, **kwargs):
        raise TypeError("real bug")
    monkeypatch.setattr(extractor, "_extract_with_ocr", wrong_type)
    result = extractor.extract_document(pdf)
    assert any("real bug" in (attempt.error or "") for attempt in result.attempts)


def test_official_source_remaining_rejection_paths(monkeypatch):
    errors = []
    monkeypatch.setattr(official_source, "_linked_document_urls", lambda *a: ("https://e-sbirka.gov.cz/x.pdf",))
    monkeypatch.setattr(official_source, "urlopen", lambda *a, **k: _Response(b"%PDF fake", "application/pdf"))
    monkeypatch.setattr(extractor, "extract_document", lambda *a, **k: extractor.ExtractionResult(["incomplete"], "ocr", 1))
    monkeypatch.setattr(official_source, "_complete_treaty_pages", lambda *a, **k: False)
    assert official_source._extract_linked_pdf(b"x", url="https://e-sbirka.gov.cz", timeout=1, expected_country="X", source_title="1/2020 Sb.", errors=errors) is None
    assert "complete treaty sequence" in errors[-1]

    mirror_errors = []
    monkeypatch.setattr(official_source, "verified_mirror_urls", lambda _: ("https://www.zakonyprolidi.cz/not-the-reference",))
    monkeypatch.setattr(official_source, "urlopen", lambda *a, **k: _Response(b"<html>challenge</html>", "text/html"))
    assert official_source._fetch_verified_mirror("1/2020 Sb.", expected_country="X", timeout=1, errors=mirror_errors) is None
    assert "reference 1/2020 not found" in mirror_errors[-1]


def test_validate_knowledge_base_nested_missing_fields(tmp_path):
    path = tmp_path / "x.yaml"
    path.write_text(
        "id: x\npayer_country: CZ\nrecipient_country: DE\nincome_type: dividends\n"
        "domestic_law: {}\ntreaty: {}\ndocumentation: []\nsources: []\nstatus: verified\n",
        encoding="utf-8",
    )
    errors = validate_knowledge_base.validate_file(path)
    assert "domestic_law.standard_rate is required." in errors
    assert "domestic_law.legal_reference is required." in errors
    assert "treaty.applicable is required." in errors


class _FakeStdout:
    def __init__(self, lines=None, tail=""):
        self.lines = list(lines or [])
        self.tail = tail
        self.closed = False
    def readline(self):
        return self.lines.pop(0) if self.lines else ""
    def read(self):
        value, self.tail = self.tail, ""
        return value
    def close(self):
        self.closed = True


class _FakeProcess:
    def __init__(self, *, returncode=0, polls=(0,), lines=None, tail=""):
        self.stdout = _FakeStdout(lines, tail)
        self.returncode = returncode
        self.pid = 123
        self._polls = iter(polls)
        self.wait_calls = []
    def poll(self):
        return next(self._polls, self.returncode)
    def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        return self.returncode


class _FakeSelector:
    def __init__(self):
        self.fileobj = None
        self.used = False
    def register(self, fileobj, event):
        self.fileobj = fileobj
    def select(self, timeout=None):
        if self.used:
            return []
        self.used = True
        return [(SimpleNamespace(fileobj=self.fileobj), None)]
    def close(self):
        pass


def test_benchmark_scalar_progress_database_and_termination(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("BOOL", "YES")
    assert benchmark_treaties._env_flag("BOOL") is True
    monkeypatch.setenv("BOOL", "no")
    assert benchmark_treaties._env_flag("BOOL") is False
    monkeypatch.setenv("BOOL", "maybe")
    with pytest.raises(ValueError):
        benchmark_treaties._env_flag("BOOL")
    assert benchmark_treaties._as_bool(None) is False
    assert benchmark_treaties._format_duration(3661) == "1:01:01"

    times = iter([0.0, 0.0, 2.0, 2.0, 3.0])
    monkeypatch.setattr(benchmark_treaties.time, "monotonic", lambda: next(times, 3.0))
    monkeypatch.setattr(benchmark_treaties, "PROGRESS_INTERVAL_SECONDS", 1)
    progress = benchmark_treaties.LiveProgress(total=2)
    progress.begin("X")
    progress.update_ocr(1, 2)
    progress.render(force=True)
    progress.finish()
    progress.close()
    assert "OCR 1/2" in capsys.readouterr().err

    db = tmp_path / "db.sqlite"
    import sqlite3
    con = sqlite3.connect(db)
    con.executescript("CREATE TABLE documents(id INTEGER,title TEXT,local_path TEXT,status TEXT); CREATE TABLE country_documents(country_cs TEXT,document_id INTEGER,relation TEXT); INSERT INTO documents VALUES(1,'1/2020','x.pdf','downloaded'); INSERT INTO country_documents VALUES('X',1,'treaty');")
    con.commit(); con.close()
    monkeypatch.setattr(benchmark_treaties, "DB", db)
    assert benchmark_treaties.load_treaties()[0]["country_cs"] == "X"

    done = _FakeProcess(polls=(0,))
    benchmark_treaties._terminate_process(done)
    assert done.wait_calls == []

    live = _FakeProcess(polls=(None,))
    monkeypatch.setattr(benchmark_treaties.os, "killpg", lambda pid, sig: None)
    benchmark_treaties._terminate_process(live)
    assert live.wait_calls == [5]

    stubborn = _FakeProcess(polls=(None,))
    wait_calls = {"count": 0}
    def stubborn_wait(timeout=None):
        wait_calls["count"] += 1
        if wait_calls["count"] == 1:
            raise subprocess.TimeoutExpired("x", 5)
        return 0
    stubborn.wait = stubborn_wait
    kills = []
    monkeypatch.setattr(benchmark_treaties.os, "killpg", lambda pid, sig: kills.append(sig))
    benchmark_treaties._terminate_process(stubborn)
    assert len(kills) == 2


def test_benchmark_parse_subprocess_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(benchmark_treaties.selectors, "DefaultSelector", _FakeSelector)
    updates = []
    benchmark_treaties._LIVE_PROGRESS = SimpleNamespace(update_ocr=lambda a, b: updates.append((a, b)), render=lambda: None)
    process = _FakeProcess(returncode=0, polls=(0,), lines=["OCR file: 2/4 pages\n"], tail="tail")
    monkeypatch.setattr(benchmark_treaties.subprocess, "Popen", lambda *a, **k: process)
    benchmark_treaties.parse_treaty("X", "1/2020", tmp_path / "x.pdf", tmp_path / "x.json")
    assert updates == [(2, 4)] and process.stdout.closed

    failed = _FakeProcess(returncode=1, polls=(1,), lines=["boom\n"])
    monkeypatch.setattr(benchmark_treaties.subprocess, "Popen", lambda *a, **k: failed)
    with pytest.raises(RuntimeError, match="boom"):
        benchmark_treaties.parse_treaty("X", "", tmp_path / "x.pdf", tmp_path / "x.json")

    timeout_process = _FakeProcess(returncode=0, polls=(None,))
    monkeypatch.setattr(benchmark_treaties.subprocess, "Popen", lambda *a, **k: timeout_process)
    monkeypatch.setattr(benchmark_treaties, "PARSE_TIMEOUT_SECONDS", -1)
    monkeypatch.setattr(benchmark_treaties, "_terminate_process", lambda process: None)
    with pytest.raises(subprocess.TimeoutExpired):
        benchmark_treaties.parse_treaty("X", "", tmp_path / "x.pdf", tmp_path / "x.json")
    benchmark_treaties._LIVE_PROGRESS = None


def test_benchmark_cache_snapshot_and_refresh_errors(monkeypatch, tmp_path):
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr(benchmark_treaties, "CACHE", cache_path)
    settings = {"x": "y"}
    cache_path.write_text("bad", encoding="utf-8")
    assert benchmark_treaties._load_cache("p", settings)["entries"] == {}
    cache_path.write_text(json.dumps({"schema_version": 999, "entries": {}}))
    assert benchmark_treaties._load_cache("p", settings)["schema_version"] == benchmark_treaties.CACHE_SCHEMA_VERSION
    cache_path.write_text(json.dumps({"schema_version": benchmark_treaties.CACHE_SCHEMA_VERSION, "entries": []}))
    assert benchmark_treaties._load_cache("p", settings)["entries"] == {}

    latest = tmp_path / "snapshots" / "LATEST"
    latest.parent.mkdir()
    first = latest.parent / "a"; second = latest.parent / "b"
    for d in (first, second):
        d.mkdir(); (d / "treaty_extraction_benchmark.csv").write_text("country\n")
    monkeypatch.setattr(benchmark_treaties, "SNAPSHOT_LATEST", latest)
    assert benchmark_treaties._latest_snapshot_path() == second

    snapshot = tmp_path / "snapshot"; snapshot.mkdir()
    monkeypatch.setattr(benchmark_treaties, "_latest_snapshot_path", lambda: snapshot)
    empty = benchmark_treaties._empty_cache("p", settings)
    assert benchmark_treaties._bootstrap_from_snapshot(empty, treaties_by_country={}, parse_fingerprint="p", settings_fingerprint="s") == []

    parsed = tmp_path / "parsed.json"
    entry = {"row": {"parse_status": "ok", "parsed_file": str(parsed)}}
    with pytest.raises(FileNotFoundError):
        benchmark_treaties._refresh_cached_row(entry)
    parsed.write_text("{}")
    entry["parsed_sha256"] = "wrong"
    with pytest.raises(RuntimeError, match="hash mismatch"):
        benchmark_treaties._refresh_cached_row(entry)


def test_benchmark_main_timeout_and_interrupt(monkeypatch, tmp_path):
    source = tmp_path / "source.pdf"; source.write_bytes(b"x")
    treaty = {"country_cs": "X", "title": "1/2020", "local_path": str(source)}
    monkeypatch.setattr(benchmark_treaties, "PARSED_DIR", tmp_path / "parsed")
    monkeypatch.setattr(benchmark_treaties, "REPORT", tmp_path / "report.csv")
    monkeypatch.setattr(benchmark_treaties, "CACHE", tmp_path / "cache.json")
    monkeypatch.setattr(benchmark_treaties, "SNAPSHOT_LATEST", tmp_path / "snapshots" / "LATEST")
    monkeypatch.setattr(benchmark_treaties, "load_treaties", lambda: [treaty])
    monkeypatch.setattr(benchmark_treaties, "_parse_pipeline_fingerprint", lambda: "p")
    monkeypatch.setattr(benchmark_treaties, "PROGRESS_INTERVAL_SECONDS", 999)

    monkeypatch.setattr(benchmark_treaties, "parse_treaty", lambda *a: (_ for _ in ()).throw(subprocess.TimeoutExpired("x", 1)))
    benchmark_treaties.main()
    row = next(csv.DictReader((tmp_path / "report.csv").open(encoding="utf-8-sig")))
    assert row["identity_reason"] == "parse_timeout"

    (tmp_path / "cache.json").unlink()
    monkeypatch.setattr(benchmark_treaties, "parse_treaty", lambda *a: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        benchmark_treaties.main()
