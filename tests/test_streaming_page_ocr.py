from pathlib import Path


def test_ocr_processes_pdf_page_by_page_with_stable_order(monkeypatch, tmp_path):
    from taxtreat.parser.extractor import _extract_with_ocr

    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    monkeypatch.setenv("TAXTREAT_OCR_DPI", "150")
    monkeypatch.setenv("TAXTREAT_OCR_WORKERS", "2")
    monkeypatch.setenv("TAXTREAT_OCR_LANG", "ces+eng")
    monkeypatch.setattr("taxtreat.parser.extractor.shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("taxtreat.parser.extractor._pdf_page_count", lambda path: 3)

    processed = []

    def fake_ocr_page(path, page_number, *, dpi, language, workdir):
        processed.append((page_number, dpi, language))
        return f"Článek {page_number}"

    monkeypatch.setattr("taxtreat.parser.extractor._ocr_pdf_page", fake_ocr_page)

    pages = _extract_with_ocr(pdf_path)

    assert pages == ["Článek 1", "Článek 2", "Článek 3"]
    assert sorted(processed) == [
        (1, 150, "ces+eng"),
        (2, 150, "ces+eng"),
        (3, 150, "ces+eng"),
    ]


def test_ocr_keeps_running_when_one_page_fails(monkeypatch, tmp_path):
    from taxtreat.parser.extractor import _extract_with_ocr

    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    monkeypatch.setattr("taxtreat.parser.extractor.shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("taxtreat.parser.extractor._pdf_page_count", lambda path: 2)

    def fake_ocr_page(path, page_number, **kwargs):
        if page_number == 1:
            raise RuntimeError("broken page")
        return "Článek 2"

    monkeypatch.setattr("taxtreat.parser.extractor._ocr_pdf_page", fake_ocr_page)

    pages = _extract_with_ocr(pdf_path)

    assert pages == ["", "Článek 2"]
