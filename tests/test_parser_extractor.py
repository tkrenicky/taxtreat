from taxtreat.parser.extractor import extract_pdf_pages


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    def __init__(self, path):
        self.path = path
        self.pages = [
            FakePage("First page"),
            FakePage(None),
            FakePage("Third page"),
        ]


def test_extract_pdf_pages(monkeypatch, tmp_path):
    pdf_path = tmp_path / "treaty.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    created = {}

    def fake_pdf_reader(path):
        created["path"] = path
        return FakeReader(path)

    monkeypatch.setattr(
        "taxtreat.parser.extractor.PdfReader",
        fake_pdf_reader,
    )

    result = extract_pdf_pages(pdf_path)

    assert created["path"] == str(pdf_path)
    assert result == [
        "First page",
        "",
        "Third page",
    ]


def test_extract_pdf_pages_accepts_string_path(monkeypatch):
    monkeypatch.setattr(
        "taxtreat.parser.extractor.PdfReader",
        lambda path: FakeReader(path),
    )

    result = extract_pdf_pages("example.pdf")

    assert result == [
        "First page",
        "",
        "Third page",
    ]


def test_garbled_pypdf_output_uses_pdftotext(monkeypatch, tmp_path):
    pdf_path = tmp_path / "garbled.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    monkeypatch.setattr(
        "taxtreat.parser.extractor.PdfReader",
        lambda path: FakeReader(path),
    )

    monkeypatch.setattr(
        "taxtreat.parser.extractor._extract_with_pypdf",
        lambda path: ["/C83/C77/C76/C79/C85/C86/C65" * 5],
    )

    monkeypatch.setattr(
        "taxtreat.parser.extractor._extract_with_pdftotext",
        lambda path: ["SMLOUVA\nČlánek 1"],
    )

    assert extract_pdf_pages(pdf_path) == ["SMLOUVA\nČlánek 1"]


def test_auto_extractor_selects_hybrid_page_by_page(monkeypatch, tmp_path):
    from taxtreat.parser.extractor import extract_document

    pdf_path = tmp_path / "mixed.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    monkeypatch.setenv("TAXTREAT_OCR", "off")
    monkeypatch.setattr(
        "taxtreat.parser.extractor._extract_with_pypdf",
        lambda path: ["Cover", "", "Článek 10\nDividendy"],
    )
    monkeypatch.setattr(
        "taxtreat.parser.extractor._extract_with_pdftotext",
        lambda path: ["", "Článek 1\nOsoby\nČlánek 2\nDaně", ""],
    )

    result = extract_document(pdf_path)

    assert result.method == "hybrid"
    assert "Článek 1" in result.pages[1]
    assert "Článek 10" in result.pages[2]


def test_auto_extractor_uses_ocr_as_generic_fallback(monkeypatch, tmp_path):
    from taxtreat.parser.extractor import extract_document

    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    monkeypatch.setenv("TAXTREAT_OCR", "auto")
    monkeypatch.setattr(
        "taxtreat.parser.extractor._extract_with_pypdf",
        lambda path: ["Smlouva notice", ""],
    )
    monkeypatch.setattr(
        "taxtreat.parser.extractor._extract_with_pdftotext",
        lambda path: ["Smlouva notice", ""],
    )
    monkeypatch.setattr(
        "taxtreat.parser.extractor._extract_with_ocr",
        lambda path: [
            "Článek 1\nOsoby\nČlánek 2\nDaně",
            "Článek 10\nDividendy\nČlánek 11\nÚroky\nČlánek 12\nLicenční poplatky",
        ],
    )

    result = extract_document(pdf_path)

    assert "ocr" in result.method
    numbers = {
        number
        for attempt in result.attempts
        if "ocr" in attempt.method
        for number in attempt.article_numbers
    }
    assert {1, 10, 11, 12}.issubset(numbers)


def test_html_source_is_read_without_pdf_parser(tmp_path):
    from taxtreat.parser.extractor import extract_document

    path = tmp_path / "treaty.html"
    path.write_text(
        "<html><body><h1>Článek 1</h1><p>Osoby</p></body></html>",
        encoding="utf-8",
    )

    result = extract_document(path)

    assert result.method == "html"
    assert "Článek 1" in result.pages[0]
