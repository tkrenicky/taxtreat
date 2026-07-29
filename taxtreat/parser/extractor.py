from pathlib import Path
from pypdf import PdfReader

def extract_pdf_pages(path):
    path = Path(path)

    reader = PdfReader(str(path))

    return [
        page.extract_text() or ""
        for page in reader.pages
    ]
