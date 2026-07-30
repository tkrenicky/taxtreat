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
